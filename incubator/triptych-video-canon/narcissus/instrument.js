/* Additive, pinned adapter over browser_runtime.js. All source/timeline decisions
 * arrive from composition.py's compiled spans. Native nodes are never rebuilt by
 * a resize or a relation change. This study does not modify the silent exporter.
 */
(function(){
  'use strict';
  const R=window.NarcissusRelations,B=window.NARCISSUS_BUNDLE,rt=window.compositionRuntime;
  const root=document.getElementById('narcissus'),$=id=>root.querySelector('#'+id);
  const canvas=$('view'),ctx=canvas.getContext('2d'),well=$('well'),fps=B.plan.fps;
  const binding={sha:B.plan.state_sha256,frames:B.plan.frames};
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
  let initial={...R.DEFAULTS,motion:!reduced.matches},events=[],parent=null,caption='',sourceNote='';
  let started=false,pausedMs=0,transportBusy=false,ready=false,alive=true,raf=0,lastPaint=-1;
  let audio=null,sound=false,participant=null,expectedAsset=null,cameraStream=null,micStream=null;
  let cameraVideo=null,micNode=null,micAnalyser=null,micSamples=null,lastMicFrame=-99;
  let liveRequest=0,cameraPending=false,micPending=false,recording=null,recordingUrl=null,recordTimer=null;
  let fileEpoch=0,mediaUrl=null,mediaAudio=null,mediaGain=null,assetDescriptor=null;
  let lastCaptureFrame=-1,ring=[],frozenTrace=null,motionFrames=null,pulseFrame=-99,lastRecording=null;
  const thumb=document.createElement('canvas');thumb.width=320;thumb.height=180;const tx=thumb.getContext('2d');
  const low=document.createElement('canvas');low.width=240;low.height=180;const lx=low.getContext('2d');
  const status=message=>{$('status').textContent=message;};
  const guard=fn=>(...args)=>Promise.resolve().then(()=>fn(...args)).catch(error=>status(error.message||String(error)));
  function frame(){return Math.max(0,Math.min(B.plan.frames-1,rt.frame||0));}
  function settings(){return R.at(initial,events,frame());}
  function clearFrames(){ring=[];frozenTrace=null;motionFrames=null;lastCaptureFrame=-1;}
  function log(key,value){
    R.event({frame:frame(),key,value},B.plan.frames);
    events=events.filter(e=>e.frame<=frame());
    if(events.length>=4096)throw new Error('Take reached its event limit; save and start a new take.');
    const last=events[events.length-1];
    if(key!=='pulse'&&last&&last.frame===frame()&&last.key===key)last.value=value;
    else events.push({frame:frame(),key,value});
  }
  function parameter(key,value){
    log(key,value);const p=settings();R.validateGraph(R.graph(p));syncControls(p);audio?.bus.update(p);
    if(key==='frozen')frozenTrace=null;if(key==='motion')motionFrames=null;paint();
  }
  function syncControls(p){
    for(const key of Object.keys(R.LIMITS)){$(key).value=p[key];$(key+'-value').textContent=String(p[key])+(key==='delay'?' s':'');}
    for(const [id,key] of [['block','blocked'],['freeze','frozen'],['motion','motion']])$(id).setAttribute('aria-pressed',String(p[key]));
    root.querySelectorAll('[data-focus]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.focus===p.focus)));
  }
  async function quietBoundary(){
    const end=performance.now()+10000;
    while([...rt.nodes.values()].some(n=>n.busy)){
      if(performance.now()>end)throw new Error('Timeline boundary did not settle.');
      await new Promise(r=>setTimeout(r,10));
    }
  }
  async function pause(){
    if(!rt.running)return;
    pausedMs=Math.min(performance.now()-rt.origin,(B.plan.frames-1)*1000/fps);
    rt.running=false;for(const n of rt.nodes.values())n.media?.pause?.();
    rt.frame=Math.floor(pausedMs*fps/1000);participant?.pause?.();
    if(audio)await audio.context.suspend();
    stopRecording();
    // Drain the upstream RAF before scheduling a resumed one. No hidden restart.
    await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    await quietBoundary();$('play').textContent='Resume';paint();
  }
  async function play(){
    if(rt.error)throw new Error(rt.error);
    if(rt.finished){await seek(0);}
    if(!started && pausedMs===0){await rt.start();started=true;}
    else {
      await quietBoundary();rt.origin=performance.now()-pausedMs;rt.running=true;rt.finished=false;
      try{await Promise.all([...rt.nodes.values()].filter(n=>n.kind==='video'&&!n.span.held).map(n=>n.media.play()));}
      catch(error){rt.running=false;for(const n of rt.nodes.values())n.media?.pause?.();throw error;}
      if(rt.error){rt.running=false;throw new Error(rt.error);}requestAnimationFrame(tick);
    }
    if(participant?.tagName==='VIDEO')await participant.play();
    if(audio&&sound)await audio.context.resume();
    $('play').textContent='Pause';status('Playing. Relation changes do not reset the three loop clocks.');
  }
  async function seek(value){
    R.need(Number.isInteger(value)&&value>=0&&value<B.plan.frames,'Seek frame');
    await pause();await quietBoundary();rt.finished=false;rt.running=false;rt.frame=value;
    rt.layoutIndex=0;while(rt.layoutIndex+1<rt.plan.layout_keyframes.length&&rt.plan.layout_keyframes[rt.layoutIndex+1].frame<=value)rt.layoutIndex++;
    await Promise.all([...rt.nodes.values()].map(async n=>{
      let i=0;while(i+1<n.spans.length&&n.spans[i+1].frame<=value)i++;
      n.index=i;await activate(n,n.spans[i],value,true);
    }));
    pausedMs=value*1000/fps;started=true;pulseFrame=-99;lastMicFrame=-99;clearFrames();
    if(participant?.tagName==='VIDEO'&&Number.isFinite(participant.duration)&&participant.duration>0)participant.currentTime=(value/fps)%participant.duration;
    syncControls(settings());$('play').textContent=value?'Resume':'Start';paint();
  }
  async function transport(action){
    if(transportBusy)throw new Error('Transport is settling.');transportBusy=true;$('play').disabled=true;$('reset').disabled=true;
    try{await action();}finally{transportBusy=false;$('play').disabled=!ready;$('reset').disabled=!ready;}
  }
  function fitDraw(context,source,x,y,w,h,mirror=false){
    const sw=source.videoWidth||source.naturalWidth||source.width,sh=source.videoHeight||source.naturalHeight||source.height;
    if(!sw||!sh||source.readyState!==undefined&&source.readyState<2)return;
    const ratio=Math.max(w/sw,h/sh),cw=w/ratio,ch=h/ratio;
    context.save();context.beginPath();context.rect(x,y,w,h);context.clip();
    if(mirror){context.translate(2*x+w,0);context.scale(-1,1);}
    context.drawImage(source,(sw-cw)/2,(sh-ch)/2,cw,ch,x,y,w,h);context.restore();
  }
  function currentCells(){return rt.plan.layout_keyframes[rt.layoutIndex].layouts[rt.orientation||'landscape'].cells;}
  function delayedTrace(p){
    if(p.frozen&&frozenTrace)return frozenTrace;
    const target=frame()-Math.round(p.delay*fps);
    let found=null;for(const item of ring)if(item.frame<=target)found=item.canvas;
    if(p.frozen&&found)frozenTrace=found;
    return found;
  }
  function paint(){
    if(!ready||!alive)return;
    const p=settings(),env=R.envelope(initial,events,frame(),fps),W=canvas.width,H=canvas.height;
    syncControls(p);if(p.motion)motionFrames=null;
    ctx.fillStyle='#121211';ctx.fillRect(0,0,W,H);
    const cells=currentCells();
    if(!p.motion&&!motionFrames){motionFrames=new Map();for(const n of rt.nodes.values()){
      const c=document.createElement('canvas');c.width=320;c.height=400;fitDraw(c.getContext('2d'),n.media,0,0,320,400);motionFrames.set(n.id,c);}}
    for(const cell of cells){
      const n=rt.nodes.get(cell.loop),r=cell.rect.map(number),x=r[0]*W+3,y=r[1]*H+3,w=r[2]*W-6,h=r[3]*H-6;
      const source=motionFrames?.get(n.id)||n.media;
      ctx.save();ctx.globalAlpha=p.focus===n.id?1:0.7;
      ctx.filter=`grayscale(${p.fracture*0.8}) contrast(${1+p.fracture*0.45})`;
      if(n.id==='echo'&&p.fracture>0.05){
        low.width=Math.max(24,Math.round(240*(1-p.fracture*0.86)));low.height=Math.max(24,Math.round(low.width*h/w));
        fitDraw(lx,source,0,0,low.width,low.height);ctx.imageSmoothingEnabled=false;fitDraw(ctx,low,x,y,w,h);
      }else fitDraw(ctx,source,x,y,w,h,n.id==='reflection');
      ctx.restore();
      if(p.focus===n.id){ctx.strokeStyle='#dad5c7';ctx.lineWidth=2;ctx.strokeRect(x+1,y+1,w-2,h-2);}
      const energy=n.id==='echo'?env.returned:env.direct;
      if(energy>0.01){ctx.fillStyle=`rgba(255,255,250,${0.09*energy})`;ctx.fillRect(x,y,w,h);}
      const history=delayedTrace(p);
      if(n.id==='echo'&&!p.blocked&&history&&p.motion){
        ctx.save();ctx.globalAlpha=0.22+p.feedback*0.6;
        fitDraw(ctx,history,x+w*0.50,y+h*0.46,w*0.45,h*0.48);ctx.restore();
      }
      ctx.fillStyle='rgba(12,12,11,.78)';ctx.fillRect(x+7,y+7,Math.min(w-14,133),25);
      ctx.fillStyle='#eeeae1';ctx.font=`${Math.max(11,Math.min(14,W/65))}px monospace`;ctx.fillText(n.id.toUpperCase(),x+13,y+24);
    }
    const history=delayedTrace(p);
    if(history&&!p.blocked&&p.motion){
      const cell=cells.find(c=>c.loop==='self'),r=cell.rect.map(number);
      let x=r[0]*W+r[2]*W*0.60,y=r[1]*H+r[3]*H*0.59,w=r[2]*W*0.31,h=r[3]*H*0.26;
      for(let i=0;i<p.depth;i++){
        ctx.save();ctx.globalAlpha=p.feedback*Math.pow(.78,i);fitDraw(ctx,history,x,y,w,h,i%2===1);ctx.restore();
        ctx.strokeStyle='rgba(235,232,220,.4)';ctx.strokeRect(x,y,w,h);x+=w*.40;y+=h*.32;w*=.54;h*=.54;
      }
    }
    // The return buffer excludes participant/camera pixels. It contains only
    // artist/synthetic loops, keeping live pixels out of delayed persistence.
    if(rt.running&&p.motion&&!p.frozen&&frame()-lastCaptureFrame>=2){
      const c=document.createElement('canvas');c.width=320;c.height=180;c.getContext('2d').drawImage(canvas,0,0,320,180);
      ring.push({frame:frame(),canvas:c});while(ring.length>26)ring.shift();lastCaptureFrame=frame();
    }
    const other=cameraVideo||participant;
    if(other&&assetDescriptor?.kind!=='audio'){
      const r=cells.find(c=>c.loop==='self').rect.map(number),w=r[2]*W*.30,h=r[3]*H*.27,x=r[0]*W+12,y=(r[1]+r[3])*H-h-12;
      ctx.fillStyle='#111';ctx.fillRect(x-2,y-2,w+4,h+4);fitDraw(ctx,other,x,y,w,h);
      ctx.fillStyle='#eee';ctx.font='12px monospace';ctx.fillText('OTHER · LOCAL',x+6,y+17);
    }
    $('times').textContent=[...rt.nodes.values()].map(n=>n.id.toUpperCase()+' '+Number(n.media.currentTime||0).toFixed(2)).join('  ·  ');
    $('clock').textContent=(frame()/fps).toFixed(2)+' / '+(B.plan.frames/fps).toFixed(2);
    if(audio&&sound){
      const t=audio.context.currentTime;
      audio.bus.update(p);
      audio.voices.forEach((v,i)=>{
        const n=rt.nodes.get(R.IDS[i]),phase=Number(n.media.currentTime||0)/(8+i*2);
        const beat=Math.pow((Math.sin(phase*2*Math.PI)+1)/2,5);
        const attention=p.focus===R.IDS[i]?1:0.38;
        const impulse=i===2?env.returned:env.direct;
        const gain=rt.running&&!mediaAudio?(0.015+0.045*beat+0.06*impulse)*attention:0;
        v.gain.gain.setTargetAtTime(gain,t,0.04);
      });
    }
    if(micAnalyser&&rt.running&&frame()-lastMicFrame>=3){
      micAnalyser.getFloatTimeDomainData(micSamples);let sum=0;for(const v of micSamples)sum+=v*v;
      const level=Math.min(1,Math.sqrt(sum/micSamples.length)*5);
      if(events.length<4096)log('mic',Math.round(level*1000)/1000);lastMicFrame=frame();
    }
  }
  function resize(){
    const box=well.getBoundingClientRect();
    const scale=Math.min(1,960/box.width,960/box.height);
    canvas.width=Math.max(2,Math.round(box.width*scale));canvas.height=Math.max(2,Math.round(box.height*scale));
    applyLayout();paint();
  }
  const observer=new ResizeObserver(resize);observer.observe(well);
  const hostObserver=new ResizeObserver(()=>{well.classList.toggle('portrait',root.getBoundingClientRect().width<640);});hostObserver.observe(root);
  async function ensureAudio(){
    if(audio)return audio;
    const AC=window.AudioContext||window.webkitAudioContext;R.need(AC,'Web Audio is unavailable.');
    const context=new AC(),bus=R.audioBus(context,settings()),monitor=context.createGain(),capture=context.createMediaStreamDestination();
    const compressor=context.createDynamicsCompressor();compressor.threshold.value=-12;compressor.ratio.value=8;
    bus.output.connect(compressor);compressor.connect(monitor);monitor.connect(context.destination);compressor.connect(capture);
    monitor.gain.value=1;bus.output.gain.value=0;const voices=[110,165,220].map((frequency,i)=>{
      const osc=context.createOscillator(),gain=context.createGain(),pan=context.createStereoPanner();
      osc.type='sine';osc.frequency.value=frequency;gain.gain.value=0;pan.pan.value=[-.65,0,.65][i];
      osc.connect(gain);gain.connect(pan);pan.connect(bus.input);osc.start();return {osc,gain,pan};});
    audio={context,bus,monitor,capture,compressor,voices};await context.suspend();return audio;
  }
  async function toggleSound(){
    await ensureAudio();sound=!sound;audio.bus.output.gain.setTargetAtTime(sound?0.2:0,audio.context.currentTime,.03);
    $('sound').setAttribute('aria-pressed',String(sound));
    if(sound&&rt.running)await audio.context.resume();else if(!sound&&!micStream)await audio.context.suspend();
    status(sound?'Procedural study sound enabled.':'Sound muted.');
  }
  function artifact(){
    return R.artifact({schema:R.VERSION,base:binding.sha,initial:R.clone(initial),events:R.clone(events),frame:frame(),parent,
      caption,sourceNote,asset:expectedAsset||assetDescriptor});
  }
  function download(doc){
    const url=URL.createObjectURL(new Blob([JSON.stringify(doc,null,2)+'\n'],{type:'application/json'}));
    const a=document.createElement('a');a.href=url;a.download='narcissus-'+doc.id.slice(0,12)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),3000);
  }
  async function loadArtifact(doc){
    const p=R.validateArtifact(doc,binding); // Validate completely before mutation.
    stopLive();stopRecording();await removeAsset(false);await seek(p.frame);
    initial=p.initial;events=p.events;parent=p.parent;caption=p.caption;sourceNote=p.sourceNote;expectedAsset=p.asset;
    $('caption').value=caption;$('source-note').value=sourceNote;$('caption-preview').textContent=caption;
    $('lineage').textContent='Parent: '+(parent||'none');syncControls(settings());audio?.bus.update(settings());clearFrames();paint();
    $('asset-status').textContent=expectedAsset?'Relink required: '+expectedAsset.kind+' '+(expectedAsset.sha256||'permission required'):'No participant source.';
    status('Recipe restored at '+(p.frame/fps).toFixed(2)+' s. Delayed image memory refills on playback; external media requires relinking.');
  }
  function fork(){const previous=artifact();parent=previous.id;$('lineage').textContent='Parent: '+parent;status('Fork created locally; parent recipe ID retained.');return artifact();}
  async function removeAsset(clearExpected=true){
    fileEpoch++;if(participant?.tagName==='VIDEO'){participant.pause();participant.removeAttribute('src');participant.load();}
    participant=null;if(mediaAudio){try{mediaAudio.stop();}catch{}mediaAudio.disconnect();mediaAudio=null;}mediaGain?.disconnect();mediaGain=null;
    if(mediaUrl)URL.revokeObjectURL(mediaUrl);mediaUrl=null;assetDescriptor=null;if(clearExpected)expectedAsset=null;
    $('asset-status').textContent='No participant source.';paint();
  }
  async function loadAsset(file){
    R.need(file&&file.size>0&&file.size<=20*1024*1024,'Participant media limit: 20 MiB.');
    const kind=file.type.startsWith('image/')?'image':file.type.startsWith('video/')?'video':file.type.startsWith('audio/')?'audio':null;
    R.need(kind,'Use an image, video, or audio file.');
    const bytes=await file.arrayBuffer(),digest=R.sha256(bytes);
    if(expectedAsset)R.need(expectedAsset.kind===kind&&expectedAsset.sha256===digest,'Media does not match this recipe. Remove the required source to choose a new one.');
    stopLive();await removeAsset(false);const epoch=++fileEpoch;let candidate=null,url=null;
    try{
      if(kind==='audio'){
        await ensureAudio();const buffer=await audio.context.decodeAudioData(bytes.slice(0));
        R.need(buffer.duration<=90,'Decoded audio limit: 90 seconds.');if(epoch!==fileEpoch)return;
        mediaAudio=audio.context.createBufferSource();mediaAudio.buffer=buffer;mediaAudio.loop=true;
        mediaGain=audio.context.createGain();mediaGain.gain.value=.20;mediaAudio.connect(mediaGain);mediaGain.connect(audio.bus.input);mediaAudio.start();
        // Explicit source replacement: silence the engineering oscillators.
        for(const v of audio.voices)v.gain.gain.setTargetAtTime(0,audio.context.currentTime,.03);
      }else{
        url=URL.createObjectURL(new Blob([bytes],{type:file.type}));candidate=document.createElement(kind==='image'?'img':'video');
        if(kind==='video'){candidate.muted=true;candidate.loop=true;candidate.playsInline=true;}
        await new Promise((resolve,reject)=>{
          const good=kind==='image'?'load':'loadeddata';const timer=setTimeout(()=>finish(new Error('Participant media decode timed out.')),10000);
          function finish(error){clearTimeout(timer);candidate.removeEventListener(good,onGood);candidate.removeEventListener('error',onBad);error?reject(error):resolve();}
          const onGood=()=>finish(),onBad=()=>finish(new Error('Cannot decode participant media.'));
          candidate.addEventListener(good,onGood,{once:true});candidate.addEventListener('error',onBad,{once:true});candidate.src=url;
        });
        const w=candidate.videoWidth||candidate.naturalWidth,h=candidate.videoHeight||candidate.naturalHeight;
        R.need(w*h<=20000000,'Decoded image/video limit: 20 megapixels.');
        if(kind==='video')R.need(Number.isFinite(candidate.duration)&&candidate.duration<=90,'Video limit: 90 seconds.');
        if(epoch!==fileEpoch){candidate.pause?.();URL.revokeObjectURL(url);return;}
        participant=candidate;mediaUrl=url;if(kind==='video'&&rt.running)await participant.play();
      }
      assetDescriptor={kind,sha256:digest};expectedAsset=null;$('asset-status').textContent=kind+' · '+digest;paint();
    }catch(error){candidate?.pause?.();if(url)URL.revokeObjectURL(url);throw error;}
  }
  function stopLive(){
    liveRequest++;cameraPending=false;micPending=false;
    for(const stream of [cameraStream,micStream])stream?.getTracks().forEach(t=>t.stop());
    cameraStream=null;micStream=null;if(cameraVideo){cameraVideo.pause();cameraVideo.srcObject=null;}cameraVideo=null;
    micNode?.disconnect();micNode=null;micAnalyser?.disconnect();micAnalyser=null;micSamples=null;
    if(assetDescriptor?.kind==='live')assetDescriptor=null;
    $('camera').setAttribute('aria-pressed','false');$('microphone').setAttribute('aria-pressed','false');
    $('camera').disabled=false;$('microphone').disabled=false;$('capture').disabled=!canRecord();
    if(audio&&!sound&&audio.context.state!=='closed')audio.context.suspend().catch(()=>{});clearFrames();paint();
  }
  async function live(kind,provider={secure:window.isSecureContext,devices:navigator.mediaDevices}){
    R.need(provider.secure&&provider.devices?.getUserMedia,'Live input requires a secure browser context and media permissions.');
    R.need(!recording,'Stop excerpt recording before enabling live input.');
    if(kind==='video'&&(cameraStream||cameraPending)||kind==='audio'&&(micStream||micPending))return;
    const request=liveRequest;const button=kind==='video'?$('camera'):$('microphone');button.disabled=true;
    if(kind==='video')cameraPending=true;else micPending=true;
    let stream=null;
    try{
      stream=await provider.devices.getUserMedia(kind==='video'?{video:{width:{ideal:640},height:{ideal:480}},audio:false}:{video:false,audio:true});
      if(request!==liveRequest||!alive){stream.getTracks().forEach(t=>t.stop());return;}
      if(kind==='video'){
        await removeAsset();cameraStream=stream;cameraVideo=document.createElement('video');cameraVideo.muted=true;cameraVideo.playsInline=true;cameraVideo.srcObject=stream;await cameraVideo.play();
        if(request!==liveRequest){stream.getTracks().forEach(t=>t.stop());return;}
        assetDescriptor={kind:'live',sha256:null};$('asset-status').textContent='live camera · ephemeral';$('capture').disabled=true;
      }else{
        await ensureAudio();if(request!==liveRequest){stream.getTracks().forEach(t=>t.stop());return;}
        micStream=stream;micNode=audio.context.createMediaStreamSource(stream);micAnalyser=audio.context.createAnalyser();micAnalyser.fftSize=256;
        micSamples=new Float32Array(256);micNode.connect(micAnalyser);await audio.context.resume();
      }
      button.setAttribute('aria-pressed','true');status(kind==='video'?'Camera preview enabled locally. Excerpt recording disabled.':'Microphone envelope enabled; no microphone audio monitoring.');
    }catch(error){stream?.getTracks().forEach(t=>t.stop());throw error;}
    finally{button.disabled=false;if(kind==='video')cameraPending=false;else micPending=false;}
  }
  function canRecord(){return !!(window.MediaRecorder&&canvas.captureStream)&&!cameraStream;}
  function stopRecording(){if(recording&&recording.recorder.state!=='inactive')recording.recorder.stop();clearTimeout(recordTimer);recordTimer=null;}
  async function capture(){
    if(recording){stopRecording();return;}
    R.need(canRecord(),'Recording unavailable, or a camera preview is active.');R.need(rt.running,'Start playback before recording.');
    const a=await ensureAudio();if(sound)await a.context.resume();
    const stream=canvas.captureStream(24);if(sound)for(const t of a.capture.stream.getAudioTracks())stream.addTrack(t.clone());
    const options=['video/webm;codecs=vp8,opus','video/webm','video/mp4'];const mime=options.find(x=>MediaRecorder.isTypeSupported(x));
    R.need(mime,'No supported excerpt recording format.');
    const recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:1600000});const chunks=[];
    recording={recorder,stream,started:performance.now()};$('capture').textContent='Stop recording';
    recorder.addEventListener('dataavailable',e=>{if(e.data.size)chunks.push(e.data);});
    recorder.addEventListener('error',e=>status('Excerpt recording failed: '+(e.error?.message||'encoder error')));
    recorder.addEventListener('stop',()=>{
      stream.getTracks().forEach(t=>t.stop());const blob=new Blob(chunks,{type:recorder.mimeType});
      if(recordingUrl)URL.revokeObjectURL(recordingUrl);recordingUrl=URL.createObjectURL(blob);
      lastRecording={blob,bytes:blob.size,mime:recorder.mimeType};const link=$('recording-link');link.href=recordingUrl;link.download='narcissus-excerpt.'+(recorder.mimeType.includes('mp4')?'mp4':'webm');link.hidden=false;
      recording=null;$('capture').textContent='Record excerpt';status('Excerpt ready locally: '+Math.round(blob.size/1024)+' KiB. No upload occurred.');
    });
    try{recorder.start(250);}catch(error){stream.getTracks().forEach(t=>t.stop());recording=null;$('capture').textContent='Record excerpt';throw error;}recordTimer=setTimeout(stopRecording,16000);status('Recording the composited view'+(sound?' and procedural sound':' without sound')+'; maximum 16 seconds.');
  }
  const addresses={'narcissus/echo/delay':'delay','narcissus/echo/feedback':'feedback','narcissus/view/fracture':'fracture','narcissus/view/depth':'depth','narcissus/focus':'focus'};
  function control(message){R.need(message&&Object.keys(message).sort().join()==='address,value','Control fields');R.need(Object.hasOwn(addresses,message.address),'Unknown control address');parameter(addresses[message.address],message.value);}
  $('play').addEventListener('click',guard(()=>transport(()=>rt.running?pause():play())));
  $('reset').addEventListener('click',guard(()=>transport(async()=>{stopLive();await seek(0);status('Rewound. Existing parameter events will replay.');})));
  $('sound').addEventListener('click',guard(toggleSound));
  $('pulse').addEventListener('click',guard(()=>{R.need(rt.running,'Start playback before sending an impulse.');if(frame()-pulseFrame>=Math.ceil(fps*.3)){log('pulse',true);pulseFrame=frame();}}));
  for(const [id,key] of [['block','blocked'],['freeze','frozen'],['motion','motion']])$(id).addEventListener('click',guard(()=>parameter(key,!settings()[key])));
  for(const key of Object.keys(R.LIMITS))$(key).addEventListener('input',guard(e=>parameter(key,Number(e.target.value))));
  root.querySelectorAll('[data-focus]').forEach(b=>b.addEventListener('click',guard(()=>parameter('focus',b.dataset.focus))));
  canvas.addEventListener('click',guard(e=>{const b=canvas.getBoundingClientRect(),x=(e.clientX-b.left)/b.width,y=(e.clientY-b.top)/b.height;
    const cell=currentCells().find(c=>{const [a,b,w,h]=c.rect.map(number);return x>=a&&x<a+w&&y>=b&&y<b+h;});if(cell)parameter('focus',cell.loop);}));
  $('save').addEventListener('click',guard(()=>{download(artifact());status('Variation recipe saved; source media bytes are not included.');}));
  $('fork').addEventListener('click',guard(()=>{download(fork());}));
  $('load').addEventListener('change',guard(async e=>{const f=e.target.files[0];if(!f)return;R.need(f.size<=2*1024*1024,'Recipe limit: 2 MiB.');const doc=JSON.parse(await f.text());await transport(()=>loadArtifact(doc));e.target.value='';}));
  $('caption').addEventListener('input',e=>{caption=e.target.value;$('caption-preview').textContent=caption;});$('source-note').addEventListener('input',e=>{sourceNote=e.target.value;});
  $('asset').addEventListener('change',guard(async e=>{const f=e.target.files[0];if(f)await loadAsset(f);e.target.value='';}));
  $('clear-asset').addEventListener('click',guard(()=>{stopLive();return removeAsset();}));
  $('camera').addEventListener('click',guard(()=>live('video')));$('microphone').addEventListener('click',guard(()=>live('audio')));
  $('stop-inputs').addEventListener('click',()=>{stopLive();status('Live inputs stopped.');});$('capture').addEventListener('click',guard(capture));
  document.addEventListener('visibilitychange',()=>{if(document.hidden){stopLive();stopRecording();if(rt.running)guard(()=>transport(pause))();}});
  const externalControl=e=>guard(()=>control(e.detail))();window.addEventListener('narcissus-control',externalControl);
  function dispose(){alive=false;cancelAnimationFrame(raf);stopLive();stopRecording();observer.disconnect();hostObserver.disconnect();window.removeEventListener('narcissus-control',externalControl);
    for(const n of rt.nodes.values())n.media?.pause?.();rt.running=false;for(const s of rt.sources.values())URL.revokeObjectURL(s.url);
    if(mediaUrl)URL.revokeObjectURL(mediaUrl);if(recordingUrl)URL.revokeObjectURL(recordingUrl);audio?.context.close();}
  window.addEventListener('pagehide',dispose,{once:true});
  function animation(now){
    if(!alive)return;
    if(!ready&&rt.error){status(rt.error);return;}
    if(!ready&&rt.ready){ready=true;document.getElementById('stage').tabIndex=-1;root.querySelectorAll('button:disabled,input:disabled').forEach(b=>{b.disabled=false;});
      $('capture').disabled=!canRecord();$('provenance').textContent='Source class: '+B.sourceClass+'. Original motion has not been recovered. The supplied still is not overwritten.';
      syncControls(initial);resize();status('Ready. Tap Start; Sound is opt-in.');}
    if(ready&&now-lastPaint>40){lastPaint=now;paint();if(rt.finished){$('play').textContent='Replay';audio?.context.suspend();stopRecording();}}
    raf=requestAnimationFrame(animation);
  }
  const api=window.narcissusStudy={get ready(){return ready;},artifact,loadArtifact,parameter,control,fork,seek,play,pause,live,stopLive,loadAsset,removeAsset,capture,stopRecording,
    get audio(){return audio;},get recording(){return lastRecording;},snapshot(){return {ready,frame:frame(),params:settings(),parent,asset:expectedAsset||assetDescriptor,
      eventCount:events.length,ringFrames:ring.length,ringBytes:ring.length*320*180*4,liveTracks:[cameraStream,micStream].filter(Boolean).flatMap(s=>s.getTracks()).filter(t=>t.readyState==='live').length,
      engine:rt.snapshot()};}};
  raf=requestAnimationFrame(animation);
})();
