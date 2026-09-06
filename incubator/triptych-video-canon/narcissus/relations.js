/* NARCISSUS study 0.1: finite, explicit relation state. No media or network IO. */
(function(root) {
  'use strict';
  const VERSION = 'narcissus-study-0.1';
  const IDS = ['self', 'reflection', 'echo'];
  const DEFAULTS = Object.freeze({delay:0.8, feedback:0.32, fracture:0.15, depth:2,
    focus:'self', blocked:false, frozen:false, motion:true});
  const LIMITS = {delay:[0.1,2], feedback:[0,0.6], fracture:[0,1], depth:[0,3]};
  function need(ok, message) { if (!ok) throw new Error(message); }
  const clone = value => JSON.parse(JSON.stringify(value));
  function canonical(value) {
    if (value === null || typeof value === 'boolean' || typeof value === 'string') return JSON.stringify(value);
    if (typeof value === 'number') { need(Number.isFinite(value), 'Non-finite number'); return JSON.stringify(value); }
    if (Array.isArray(value)) return '['+value.map(canonical).join(',')+']';
    need(value && Object.getPrototypeOf(value) === Object.prototype, 'Expected a plain object');
    return '{'+Object.keys(value).sort().map(k => JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
  }
  // Portable SHA-256 for the explicit, embedded offline adapter. Not a fetch fallback.
  function sha256(input) {
    const bytes = typeof input === 'string' ? new TextEncoder().encode(input) : new Uint8Array(input);
    const K = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
      0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
      0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
      0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
      0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
      0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
      0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
      0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
    const H = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    const data = new Uint8Array(Math.ceil((bytes.length+9)/64)*64); data.set(bytes); data[bytes.length]=128;
    const view = new DataView(data.buffer); const bits = bytes.length*8;
    view.setUint32(data.length-8,Math.floor(bits/4294967296)); view.setUint32(data.length-4,bits>>>0);
    const rr = (x,n) => (x>>>n)|(x<<(32-n)); const w = new Uint32Array(64);
    for (let offset=0;offset<data.length;offset+=64) {
      for (let i=0;i<16;i++) w[i]=view.getUint32(offset+4*i);
      for (let i=16;i<64;i++) { const a=w[i-15],b=w[i-2];
        w[i]=(w[i-16]+(rr(a,7)^rr(a,18)^(a>>>3))+w[i-7]+(rr(b,17)^rr(b,19)^(b>>>10)))>>>0; }
      let [a,b,c,d,e,f,g,h]=H;
      for (let i=0;i<64;i++) {
        const t1=(h+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^(~e&g))+K[i]+w[i])>>>0;
        const t2=((rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c)))>>>0;
        h=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;
      }
      [a,b,c,d,e,f,g,h].forEach((v,i)=>{H[i]=(H[i]+v)>>>0;});
    }
    return H.map(v=>v.toString(16).padStart(8,'0')).join('');
  }
  function params(value) {
    need(value && Object.keys(value).sort().join()===Object.keys(DEFAULTS).sort().join(),'Parameter fields');
    for (const [key,[lo,hi]] of Object.entries(LIMITS))
      need(typeof value[key]==='number' && Number.isFinite(value[key]) && value[key]>=lo && value[key]<=hi,'Parameter range: '+key);
    need(Number.isInteger(value.depth),'Depth must be integer');
    need(IDS.includes(value.focus),'Unknown focus');
    for (const key of ['blocked','frozen','motion']) need(typeof value[key]==='boolean','Boolean parameter: '+key);
    return clone(value);
  }
  function graph(settings) {
    const p=params(settings);
    return {nodes:IDS.slice(),edges:[
      {from:'self',to:'reflection',op:'reflect',delay:0,gain:0.5,enabled:true},
      {from:'self',to:'echo',op:'echo',delay:p.delay,gain:0.5,enabled:!p.blocked},
      {from:'echo',to:'self',op:'feedback',delay:p.delay,gain:p.feedback,enabled:!p.blocked}
    ]};
  }
  function validateGraph(g) {
    need(g && Array.isArray(g.nodes) && g.nodes.length>0 && g.nodes.length<=8 && new Set(g.nodes).size===g.nodes.length,'Graph nodes');
    need(g.nodes.every(n=>IDS.includes(n)), 'Unknown graph node');
    need(Array.isArray(g.edges) && g.edges.length<=12,'Graph edge guard');
    const sums = Object.fromEntries(g.nodes.map(n=>[n,0])), adj=Object.fromEntries(g.nodes.map(n=>[n,[]]));
    for (const e of g.edges) {
      need(g.nodes.includes(e.from)&&g.nodes.includes(e.to),'Unknown edge node');
      need(['reflect','echo','feedback'].includes(e.op),'Unknown operation');
      need(typeof e.enabled==='boolean','Edge enabled');
      need(Number.isFinite(e.delay)&&e.delay>=0&&e.delay<=2,'Edge delay');
      need(Number.isFinite(e.gain)&&e.gain>=0&&e.gain<=0.6,'Edge gain');
      if(e.enabled) { sums[e.to]+=e.gain; if(e.delay===0) adj[e.from].push(e.to); }
    }
    need(Object.values(sums).every(x=>x<1),'Incoming gain must be below one');
    const seen=new Set(),active=new Set();
    function visit(n) { need(!active.has(n),'Zero-delay cycle'); if(seen.has(n)) return;
      active.add(n);for(const b of adj[n])visit(b);active.delete(n);seen.add(n); }
    g.nodes.forEach(visit);return true;
  }
  function event(e, maxFrame) {
    need(e && Object.keys(e).sort().join()==='frame,key,value','Event fields');
    need(Number.isInteger(e.frame)&&e.frame>=0&&e.frame<maxFrame,'Event frame');
    if(e.key==='pulse') need(e.value===true,'Pulse value');
    else if(e.key==='mic') need(typeof e.value==='number'&&Number.isFinite(e.value)&&e.value>=0&&e.value<=1,'Mic envelope');
    else {need(Object.hasOwn(DEFAULTS,e.key),'Unknown event');params({...DEFAULTS,[e.key]:e.value});}
  }
  function at(initial, events, frame) {
    const p=params(initial);for(const e of events)if(e.frame<=frame && Object.hasOwn(DEFAULTS,e.key))p[e.key]=e.value;
    return p;
  }
  function pulse(events, frame, fps) {
    let value=0;for(const e of events)if(e.key==='pulse'&&e.frame<=frame&&frame-e.frame<4*fps)
      value+=Math.exp(-(frame-e.frame)/(0.45*fps));
    return Math.min(1,value);
  }
  function envelope(initial, events, frame, fps) {
    const p=at(initial,events,frame), d=Math.round(p.delay*fps);
    const delayed=frame>=d?pulse(events,frame-d,fps):0;
    let mic=0;for(const e of events)if(e.key==='mic'&&e.frame<=frame&&frame-e.frame<fps/2)mic=e.value;
    return {params:p,direct:Math.max(pulse(events,frame,fps),mic),returned:p.blocked?0:delayed};
  }
  function artifact(payload) { const p=clone(payload); return {id:sha256(canonical(p)),payload:p}; }
  function validateArtifact(doc, binding) {
    need(doc && Object.keys(doc).sort().join()==='id,payload','Artifact envelope');
    need(/^[a-f0-9]{64}$/.test(doc.id)&&sha256(canonical(doc.payload))===doc.id,'Artifact checksum');
    const p=doc.payload;
    need(Object.keys(p).sort().join()==='asset,base,caption,events,frame,initial,parent,schema,sourceNote','Artifact fields');
    need(p.schema===VERSION && p.base===binding.sha,'Incompatible engine or media binding');
    need(p.parent===null||/^[a-f0-9]{64}$/.test(p.parent),'Parent ID');
    params(p.initial);validateGraph(graph(p.initial));
    need(Number.isInteger(p.frame)&&p.frame>=0&&p.frame<binding.frames,'Saved frame');
    need(Array.isArray(p.events)&&p.events.length<=4096,'Event limit');
    let last=-1;for(const e of p.events){event(e,binding.frames);need(e.frame>=last,'Event order');last=e.frame;}
    need(typeof p.caption==='string'&&p.caption.length<=500,'Caption limit');
    need(typeof p.sourceNote==='string'&&p.sourceNote.length<=250,'Source note limit');
    if(p.asset!==null) {
      need(p.asset && Object.keys(p.asset).sort().join()==='kind,sha256','Asset fields');
      need(['image','video','audio','live'].includes(p.asset.kind),'Asset kind');
      need(p.asset.kind==='live'?p.asset.sha256===null:/^[a-f0-9]{64}$/.test(p.asset.sha256),'Asset digest');
    }
    return clone(p);
  }
  // Same bounded delay bus is used by the running instrument and offline tests.
  function audioBus(ctx, p=DEFAULTS) {
    params(p);const input=ctx.createGain(),dry=ctx.createGain(),delay=ctx.createDelay(2.1),feedback=ctx.createGain(),wet=ctx.createGain(),output=ctx.createGain();
    dry.gain.value=0.7;delay.delayTime.value=p.delay;feedback.gain.value=p.feedback;wet.gain.value=p.blocked?0:0.45;
    output.gain.value=0.2;input.connect(dry);dry.connect(output);input.connect(delay);delay.connect(feedback);feedback.connect(delay);delay.connect(wet);wet.connect(output);
    return {input,dry,delay,feedback,wet,output, update(settings){params(settings);const t=ctx.currentTime;
      delay.delayTime.setTargetAtTime(settings.delay,t,0.04);feedback.gain.setTargetAtTime(settings.blocked?0:settings.feedback,t,0.04);wet.gain.setTargetAtTime(settings.blocked?0:0.45,t,0.04);},
      disconnect(){[input,dry,delay,feedback,wet,output].forEach(n=>n.disconnect());}};
  }
  const api={VERSION,IDS,DEFAULTS,LIMITS,need,clone,canonical,sha256,params,graph,validateGraph,event,at,pulse,envelope,artifact,validateArtifact,audioBus};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.NarcissusRelations=api;
})(typeof window==='undefined'?globalThis:window);
