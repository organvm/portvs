'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const R=require('./relations.js');
const base={sha:'a'.repeat(64),frames:1440};
function payload(){return {schema:R.VERSION,base:base.sha,initial:{...R.DEFAULTS},events:[],frame:0,parent:null,caption:'',sourceNote:'',asset:null};}
test('portable SHA-256 matches native digest, binary boundaries and UTF-8',()=>{
 for(const n of [0,1,3,55,56,64,127,1024,65537]){const b=Buffer.from(Array.from({length:n},(_,i)=>i%251));assert.equal(R.sha256(b),crypto.createHash('sha256').update(b).digest('hex'));}
 for(const s of ['abc','NARCISSUS — ECHO','\u0000\n'])assert.equal(R.sha256(s),crypto.createHash('sha256').update(s).digest('hex'));
});
test('canonical order is independent of object insertion order',()=>assert.equal(R.canonical({z:2,a:[1,3]}),R.canonical({a:[1,3],z:2})));
test('non-finite values fail closed',()=>{for(const v of [NaN,Infinity,-Infinity])assert.throws(()=>R.canonical({v}));});
test('default relation graph includes a bounded delayed feedback cycle',()=>assert.equal(R.validateGraph(R.graph(R.DEFAULTS)),true));
test('zero-delay feedback cycle is rejected',()=>{const g=R.graph(R.DEFAULTS);g.edges.forEach(e=>e.delay=0);assert.throws(()=>R.validateGraph(g),/Zero-delay cycle/);});
test('unknown graph nodes and unbounded incoming gain are rejected',()=>{
 let g=R.graph(R.DEFAULTS);g.edges[0].from='missing';assert.throws(()=>R.validateGraph(g));
 g=R.graph(R.DEFAULTS);g.edges.push({...g.edges[0]});assert.throws(()=>R.validateGraph(g),/Incoming gain/);
});
test('parameter contract rejects missing, additional and invalid fields',()=>{
 const wrong=[{...R.DEFAULTS,delay:0},{...R.DEFAULTS,feedback:.61},{...R.DEFAULTS,depth:1.5},{...R.DEFAULTS,focus:'other'},{...R.DEFAULTS,blocked:1},{...R.DEFAULTS,new:1}];
 const missing={...R.DEFAULTS};delete missing.delay;wrong.push(missing);for(const p of wrong)assert.throws(()=>R.params(p));
});
test('same-frame events retain array ordering',()=>assert.equal(R.at(R.DEFAULTS,[{frame:2,key:'delay',value:.2},{frame:2,key:'delay',value:1.7}],2).delay,1.7));
test('echo cannot respond before the authored delay',()=>{
 const p={...R.DEFAULTS,delay:.5},e=[{frame:12,key:'pulse',value:true}];
 assert.equal(R.envelope(p,e,23,24).returned,0);assert.equal(R.envelope(p,e,24,24).returned,1);
});
test('block removes the return without erasing the direct event',()=>{
 const p={...R.DEFAULTS,blocked:true,delay:.5},e=[{frame:0,key:'pulse',value:true}];
 assert.ok(R.envelope(p,e,12,24).direct>0);assert.equal(R.envelope(p,e,12,24).returned,0);
});
test('event values, frames and fields are validated',()=>{
 for(const e of [{frame:-1,key:'pulse',value:true},{frame:1440,key:'pulse',value:true},{frame:1,key:'mic',value:NaN},{frame:1,key:'missing',value:0},{frame:1,key:'pulse',value:true,extra:1}])assert.throws(()=>R.event(e,1440));
});
test('artifact save/load round trip preserves exact Unicode and whitespace',()=>{
 const p=payload();p.caption=' : TEST\n  me\t<test>\n';p.sourceNote='test fixture, not artist text';const d=R.artifact(p);
 assert.deepEqual(R.validateArtifact(JSON.parse(JSON.stringify(d)),base),p);
});
test('checksum detects a changed saved value',()=>{const d=R.artifact(payload());d.payload.initial.depth=3;assert.throws(()=>R.validateArtifact(d,base),/checksum/);});
test('a recomputed checksum does not bypass the engine/media binding',()=>{const p=payload();p.base='b'.repeat(64);assert.throws(()=>R.validateArtifact(R.artifact(p),base),/binding/);});
test('fork ancestry changes the child ID without changing the parent',()=>{
 const d=R.artifact(payload()),p=R.clone(d.payload);p.parent=d.id;const child=R.artifact(p);assert.notEqual(child.id,d.id);assert.equal(R.validateArtifact(child,base).parent,d.id);assert.equal(d.payload.parent,null);
});
test('recipes reject unordered history, excess history and unsupported assets',()=>{
 let p=payload();p.events=[{frame:2,key:'pulse',value:true},{frame:1,key:'pulse',value:true}];assert.throws(()=>R.validateArtifact(R.artifact(p),base));
 p=payload();p.events=Array.from({length:4097},()=>({frame:0,key:'pulse',value:true}));assert.throws(()=>R.validateArtifact(R.artifact(p),base));
 p=payload();p.asset={kind:'image',sha256:'b'.repeat(64),bytes:'data'};assert.throws(()=>R.validateArtifact(R.artifact(p),base));
});
test('live recipe contains only an ephemeral dependency, never raw capture',()=>{
 const p=payload();p.asset={kind:'live',sha256:null};const d=R.artifact(p);assert.deepEqual(R.validateArtifact(d,base).asset,p.asset);assert.ok(!R.canonical(d).includes('data:'));
});
test('pure signal evaluation is replayable in any query order',()=>{
 const p=R.DEFAULTS,e=[{frame:3,key:'pulse',value:true},{frame:24,key:'delay',value:1.5}];const frames=[0,9,25,48,72];
 const a=Object.fromEntries(frames.map(f=>[f,R.envelope(p,e,f,24)])),b=Object.fromEntries([...frames].reverse().map(f=>[f,R.envelope(p,e,f,24)]));assert.deepEqual(a,b);
});
