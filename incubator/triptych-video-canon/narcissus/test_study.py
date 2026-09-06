#!/usr/bin/env python3
"""Scoped proof for the NARCISSUS extension; not the upstream PR #9 suite.

Browser tests deliberately inject the exact standalone HTML into an isolated
Chromium document. This is neither HTTP nor file-navigation proof. Camera/mic
lifecycle tests inject synthetic providers and never claim hardware permission.
"""
from __future__ import annotations
import argparse, base64, hashlib, io, json, math, os, struct, subprocess, sys, time, unittest, wave
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
from build_study import UPSTREAM,blob
import composition as c
from browser_runtime import compile_plan
STUDY=HERE.parent/'runtime-proof/narcissus-synthetic-v1'
OUTPUT=HERE.parent/'runtime-proof/narcissus-evidence'
BROWSER='/usr/bin/chromium'
MEASUREMENTS={}

def wait(page,fn,timeout=12):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if page.evaluate(fn):return
        page.wait_for_timeout(50)
    raise AssertionError('Predicate did not become true: '+fn)

class CompilerProof(unittest.TestCase):
    def test_01_upstream_blobs_are_exact(self):
        for name,expected in UPSTREAM.items():self.assertEqual(blob(HERE.parent/name),expected)
    def test_02_sources_pass_existing_media_integrity_probe(self):
        s=c.load_state(STUDY/'state.json');self.assertEqual(len(c.media_paths(s,STUDY)),3)
    def test_03_existing_compiler_reproduces_each_span(self):
        state=c.load_state(STUDY/'state.json');plan=compile_plan(state);saved=json.loads((STUDY/'plan.json').read_text())
        self.assertEqual(plan['tracks'],saved['tracks']);self.assertEqual(plan['layout_keyframes'],saved['layout_keyframes'])
        self.assertEqual(plan['state_sha256'],saved['state_sha256']);self.assertEqual(plan['audio'],'none')
    def test_04_three_distinct_clocks_and_explicit_ancestry(self):
        s=c.load_state(STUDY/'state.json');self.assertTrue(s['allow_source_reuse'])
        r=c.resolve_at(s,24);self.assertEqual([x['id'] for x in r['loops']],['self','reflection','echo'])
        self.assertEqual([x['source_offset'] for x in r['loops']],['1','2','3'])
    def test_05_orientation_changes_only_presentation(self):
        s=c.load_state(STUDY/'state.json');a=c.presentation_at(s,45,320,600);b=c.presentation_at(s,45,960,540)
        self.assertEqual(a['loops'],b['loops']);self.assertNotEqual(a['layout'],b['layout'])
    def test_06_layout_overlap_is_rejected_by_existing_engine(self):
        s=c.load_state(STUDY/'state.json');s['layouts']['portrait']['cells'][1]['rect']=[0,0,1,1]
        with self.assertRaises(c.StateError):c.validate_state(s)

class BrowserProof(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw=sync_playwright().start();cls.browser=cls.pw.chromium.launch(executable_path=BROWSER)
        MEASUREMENTS['browser']=cls.browser.version;MEASUREMENTS['transport']='explicit isolated-document HTML injection'
        MEASUREMENTS['media_integrity']='portable SHA-256 over embedded bytes, no injected expected digest'
    @classmethod
    def tearDownClass(cls):cls.browser.close();cls.pw.stop()
    def setUp(self):
        self.context=self.browser.new_context(viewport={'width':1000,'height':1100},accept_downloads=True)
        self.page=self.context.new_page();self.errors=[];self.requests=[]
        self.page.on('pageerror',lambda e:self.errors.append(str(e)))
        self.page.on('request',lambda r:self.requests.append(r.url))
        self.page.set_content((STUDY/'NARCISSUS-study.html').read_text())
        wait(self.page,'() => !!window.narcissusStudy?.ready')
    def tearDown(self):
        self.context.close();self.assertEqual(self.errors,[])
    def snap(self):return self.page.evaluate('() => window.narcissusStudy.snapshot()')
    def test_01_ready_and_no_remote_requests(self):
        s=self.snap();self.assertTrue(s['ready']);self.assertEqual(len(s['engine']['loops']),3)
        self.assertFalse(s['engine']['running']);self.assertEqual(s['liveTracks'],0)
        self.assertEqual([u for u in self.requests if u.startswith(('http:','https:'))],[])
    def test_02_resize_preserves_native_nodes_sources_and_time(self):
        p=self.page;p.click('#play');p.wait_for_timeout(200)
        p.evaluate('''() => {window.refs=[...document.querySelectorAll('#stage video')];window.nativeEvents=[];
          window.mark={wall:performance.now(),times:refs.map(v=>v.currentTime),srcs:refs.map(v=>v.currentSrc)};
          for(const v of refs)for(const name of ['seeking','loadstart','pause','ratechange'])v.addEventListener(name,()=>nativeEvents.push(name));
          window.domEvents=[];window.observer=new MutationObserver(ms=>domEvents.push(...ms.map(m=>m.type)));observer.observe(document.querySelector('#stage'),{subtree:true,childList:true});}''')
        p.set_viewport_size({'width':320,'height':950});p.wait_for_timeout(500)
        p.screenshot(path=str(OUTPUT/'synthetic-portrait.png'),full_page=True)
        self.assertEqual(self.snap()['engine']['orientation'],'portrait')
        p.set_viewport_size({'width':1000,'height':1000});p.wait_for_timeout(400)
        result=p.evaluate('''() => ({same:refs.every((v,i)=>v===document.querySelectorAll('#stage video')[i]),count:document.querySelectorAll('#stage video').length,
          source:refs.every((v,i)=>v.currentSrc===mark.srcs[i]),events:nativeEvents,dom:domEvents,
          deltas:refs.map((v,i)=>v.currentTime-mark.times[i]),wall:(performance.now()-mark.wall)/1000})''')
        self.assertTrue(result['same']);self.assertTrue(result['source']);self.assertEqual(result['count'],3)
        self.assertEqual(result['events'],[]);self.assertEqual(result['dom'],[])
        self.assertTrue(all(abs(x-result['wall'])<.20 for x in result['deltas']))
        MEASUREMENTS['native_resize']=result;p.screenshot(path=str(OUTPUT/'synthetic-landscape.png'),full_page=True)
    def test_03_pause_and_resume(self):
        p=self.page;p.click('#play');p.wait_for_timeout(350);p.click('#play');wait(p,'() => !window.compositionRuntime.running')
        before=self.snap();p.wait_for_timeout(250);after=self.snap();self.assertEqual(before['frame'],after['frame'])
        for a,b in zip(before['engine']['loops'],after['engine']['loops']):self.assertAlmostEqual(a['currentTime'],b['currentTime'],places=2)
        p.click('#play');p.wait_for_timeout(300);self.assertGreater(self.snap()['frame'],after['frame'])
    def test_04_relation_controls_do_not_seek_or_remount(self):
        p=self.page;p.click('#play');p.wait_for_timeout(200)
        p.evaluate("() => {window.refs=[...document.querySelectorAll('#stage video')];window.changes=[];for(const v of refs)v.addEventListener('seeking',()=>changes.push('seek'));}")
        p.evaluate("() => {narcissusStudy.parameter('delay',1.7);narcissusStudy.parameter('feedback',.55);narcissusStudy.parameter('focus','echo');narcissusStudy.parameter('blocked',true);}")
        p.wait_for_timeout(200);self.assertEqual(p.evaluate('() => changes'),[])
        self.assertTrue(p.evaluate("() => refs.every((v,i)=>v===document.querySelectorAll('#stage video')[i])"))
        self.assertEqual(self.snap()['params']['delay'],1.7)
    def test_05_recipe_exact_text_download_and_restore(self):
        p=self.page;p.locator('summary').click();exact='TEST ONLY\n  : me\t<no markup>\n'
        p.fill('#caption',exact);p.fill('#source-note','engineering test fixture')
        p.evaluate("() => narcissusStudy.parameter('delay',1.2)")
        with p.expect_download() as download:p.click('#save')
        target=OUTPUT/'test-variation.json';download.value.save_as(str(target));doc=json.loads(target.read_text())
        self.assertEqual(doc['payload']['caption'],exact);self.assertNotIn('media',doc['payload'])
        p.evaluate("() => narcissusStudy.parameter('delay',.2)")
        p.set_input_files('#load',str(target));wait(p,"() => narcissusStudy.snapshot().params.delay===1.2")
        self.assertEqual(p.locator('#caption').input_value(),exact)
        self.assertEqual(p.evaluate('() => narcissusStudy.artifact().id'),doc['id'])
    def test_06_parent_hash_is_retained(self):
        p=self.page;original=p.evaluate('() => narcissusStudy.artifact()');child=p.evaluate('() => narcissusStudy.fork()')
        self.assertEqual(child['payload']['parent'],original['id']);self.assertNotEqual(child['id'],original['id'])
    def test_07_invalid_recipe_is_transactionally_rejected(self):
        p=self.page;before=p.evaluate('() => narcissusStudy.artifact()')
        result=p.evaluate('''async () => {const d=narcissusStudy.artifact();d.payload.initial.delay=1.9;try{await narcissusStudy.loadArtifact(d);return false;}catch{return true;}}''')
        self.assertTrue(result);self.assertEqual(before,p.evaluate('() => narcissusStudy.artifact()'))
    def test_08_rewind_replays_parameter_events(self):
        p=self.page;p.click('#play');p.wait_for_timeout(350);p.evaluate("() => narcissusStudy.parameter('delay',1.9)");p.wait_for_timeout(150)
        p.click('#reset');wait(p,'() => narcissusStudy.snapshot().frame===0');self.assertEqual(self.snap()['params']['delay'],.8)
        p.click('#play');p.wait_for_timeout(650);self.assertEqual(self.snap()['params']['delay'],1.9)
        self.assertEqual(p.locator('#delay').input_value(),'1.9')
    def test_09_return_buffer_is_bounded_and_trace_freezes(self):
        p=self.page;p.click('#play');p.wait_for_timeout(2700);s=self.snap()
        self.assertLessEqual(s['ringFrames'],26);self.assertGreater(s['ringFrames'],15);self.assertLessEqual(s['ringBytes'],5990400)
        p.click('#freeze');before=self.snap()['ringFrames'];p.wait_for_timeout(300);self.assertEqual(self.snap()['ringFrames'],before)
        MEASUREMENTS['return_buffer']={'frames':s['ringFrames'],'bytes':s['ringBytes'],'budget':5990400}
    def test_10_web_audio_bus_has_measured_delayed_returns(self):
        result=self.page.evaluate('''async () => {
          async function render(blocked){const c=new OfflineAudioContext(1,48000,48000),p={...NarcissusRelations.DEFAULTS,delay:.25,feedback:.4,blocked};
            const bus=NarcissusRelations.audioBus(c,p);bus.output.connect(c.destination);const s=c.createBufferSource(),b=c.createBuffer(1,48000,48000);b.getChannelData(0)[0]=1;s.buffer=b;s.connect(bus.input);s.start();
            const out=(await c.startRendering()).getChannelData(0);const peaks=[];let invalid=0,max=0,sum=0;for(let i=0;i<out.length;i++){const x=out[i];if(Math.abs(x)>1e-5)peaks.push([i,x]);if(!Number.isFinite(x))invalid++;max=Math.max(max,Math.abs(x));sum+=x*x;}return {peaks,invalid,max,rms:Math.sqrt(sum/out.length)};}
          return {open:await render(false),blocked:await render(true)};}''')
        peaks=result['open']['peaks'];self.assertEqual(len(peaks),4)
        self.assertEqual([peaks[0][0],peaks[1][0]],[0,12000])
        # Chromium inserts a render quantum on later traversals of a cycle.
        # Measure the actual onsets; do not imply sample-exact feedback delay.
        for a,b in zip(peaks[1:],peaks[2:]):self.assertTrue(12000 <= b[0]-a[0] <= 12128)
        for (_,got),expected in zip(peaks,[.14,.09,.036,.0144]):self.assertAlmostEqual(got,expected,places=5)
        self.assertEqual(len(result['blocked']['peaks']),1);self.assertEqual(result['open']['invalid'],0)
        MEASUREMENTS['offline_audio_impulse']=result
    def test_11_sound_is_opt_in_and_has_nonzero_signal(self):
        p=self.page;self.assertTrue(p.evaluate('() => narcissusStudy.audio===null'));p.click('#play');p.click('#sound');p.wait_for_timeout(400)
        result=p.evaluate('''() => {const a=narcissusStudy.audio;window.checkAnalyser=a.context.createAnalyser();checkAnalyser.fftSize=1024;a.bus.output.connect(checkAnalyser);return a.context.state;}''')
        self.assertEqual(result,'running');p.wait_for_timeout(200)
        rms=p.evaluate('''() => {const b=new Float32Array(1024);checkAnalyser.getFloatTimeDomainData(b);return Math.sqrt(b.reduce((a,v)=>a+v*v,0)/b.length);}''')
        self.assertGreater(rms,1e-6);MEASUREMENTS['live_graph_rms']=rms
        p.click('#sound');p.wait_for_timeout(180);self.assertEqual(p.evaluate('() => narcissusStudy.audio.context.state'),'suspended')
    def test_12_recorded_excerpt_contains_decodable_video_and_audio(self):
        p=self.page;p.click('#play');p.click('#sound');p.click('#capture');p.click('#pulse');p.wait_for_timeout(1800);p.click('#capture')
        wait(p,'() => !!narcissusStudy.recording')
        result=p.evaluate('''async () => {const r=narcissusStudy.recording;const data=await new Promise(resolve=>{const f=new FileReader();f.onload=()=>resolve(f.result.split(',').pop());f.readAsDataURL(r.blob);});return {data,bytes:r.bytes,mime:r.mime};}''')
        file=OUTPUT/'synthetic-excerpt.webm';file.write_bytes(base64.b64decode(result.pop('data')))
        facts=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(file)],capture_output=True,text=True,check=True).stdout)
        self.assertEqual({s['codec_type'] for s in facts['streams']},{'video','audio'})
        raw=subprocess.run(['ffmpeg','-v','error','-i',str(file),'-vn','-f','f32le','-ac','1','pipe:1'],capture_output=True,check=True).stdout
        samples=struct.unpack('<'+'f'*(len(raw)//4),raw);rms=math.sqrt(sum(x*x for x in samples)/len(samples));self.assertGreater(rms,1e-6)
        MEASUREMENTS['recorded_excerpt']={**result,'audio_rms':rms,'streams':[{k:s.get(k) for k in ['codec_type','codec_name','width','height','sample_rate']} for s in facts['streams']]}
    def test_13_local_image_relink_verifies_bytes(self):
        p=self.page;p.locator('summary').click();file=OUTPUT/'participant-test.png';Image.new('RGB',(32,32),(31,171,100)).save(file)
        p.set_input_files('#asset',str(file));wait(p,"() => narcissusStudy.snapshot().asset?.kind==='image'")
        doc=p.evaluate('() => narcissusStudy.artifact()');self.assertEqual(doc['payload']['asset']['sha256'],hashlib.sha256(file.read_bytes()).hexdigest())
        p.evaluate('async d => narcissusStudy.loadArtifact(d)',doc)
        bad=OUTPUT/'participant-wrong.png';Image.new('RGB',(32,32),(200,10,30)).save(bad)
        p.set_input_files('#asset',str(bad));p.wait_for_timeout(100);self.assertIn('does not match',p.locator('#status').inner_text())
        p.set_input_files('#asset',str(file));wait(p,"() => !document.querySelector('#asset-status').textContent.startsWith('Relink')")
        self.assertEqual(p.evaluate('() => narcissusStudy.artifact().payload.asset'),doc['payload']['asset'])
    def test_14_audio_file_can_replace_test_tones(self):
        p=self.page;p.locator('summary').click();file=OUTPUT/'participant-test.wav'
        with wave.open(str(file),'wb') as w:
            w.setparams((1,2,22050,0,'NONE','not compressed'));w.writeframes(b''.join(struct.pack('<h',int(5000*math.sin(i*2*math.pi*220/22050))) for i in range(11025)))
        p.set_input_files('#asset',str(file));wait(p,"() => narcissusStudy.snapshot().asset?.kind==='audio'")
        self.assertEqual(self.snap()['asset']['sha256'],hashlib.sha256(file.read_bytes()).hexdigest())
        p.click('#clear-asset');wait(p,'() => narcissusStudy.snapshot().asset===null')
    def test_15_denied_media_provider_keeps_capture_off(self):
        result=self.page.evaluate('''async () => {try{await narcissusStudy.live('video',{secure:true,devices:{getUserMedia:async()=>{throw new DOMException('denied','NotAllowedError');}}});return false;}catch{return narcissusStudy.snapshot().liveTracks===0;}}''')
        self.assertTrue(result)
    def test_16_late_media_permission_is_cancelled_and_tracks_stop(self):
        result=self.page.evaluate('''async () => {const c=document.createElement('canvas');c.width=32;c.height=32;const s=c.captureStream(1);let resolve;
          const pending=narcissusStudy.live('video',{secure:true,devices:{getUserMedia:()=>new Promise(r=>resolve=r)}});
          narcissusStudy.stopLive();resolve(s);await pending;return {ended:s.getTracks().every(t=>t.readyState==='ended'),active:narcissusStudy.snapshot().liveTracks};}''')
        self.assertEqual(result,{'ended':True,'active':0})
    def test_17_camera_preview_stops_and_cannot_be_recorded(self):
        self.page.click('#play')
        result=self.page.evaluate('''async () => {const c=document.createElement('canvas');c.width=32;c.height=32;const x=c.getContext('2d');const s=c.captureStream(10);const timer=setInterval(()=>{x.fillStyle='#123456';x.fillRect(0,0,32,32);},30);
          try{await narcissusStudy.live('video',{secure:true,devices:{getUserMedia:async()=>s}});const before=narcissusStudy.snapshot();const disabled=document.querySelector('#capture').disabled;const recipe=narcissusStudy.artifact();narcissusStudy.stopLive();return {before:before.liveTracks,disabled,asset:recipe.payload.asset,ended:s.getTracks().every(t=>t.readyState==='ended'),after:narcissusStudy.snapshot().liveTracks};}finally{clearInterval(timer);s.getTracks().forEach(t=>t.stop());}}''')
        self.assertEqual(result,{'before':1,'disabled':True,'asset':{'kind':'live','sha256':None},'ended':True,'after':0})
    def test_18_external_control_adapter_uses_same_validation(self):
        p=self.page;p.evaluate("() => narcissusStudy.control({address:'narcissus/echo/delay',value:1.4})");self.assertEqual(self.snap()['params']['delay'],1.4)
        self.assertTrue(p.evaluate("() => {try{narcissusStudy.control({address:'unknown',value:1});return false;}catch{return true;}}"))
    def test_19_mobile_controls_fit_320_pixels(self):
        p=self.page;p.set_viewport_size({'width':320,'height':900});p.wait_for_timeout(120)
        facts=p.evaluate('''() => ({width:innerWidth,scroll:document.documentElement.scrollWidth,targets:[...document.querySelectorAll('button')].filter(b=>b.getBoundingClientRect().height>0).map(b=>b.getBoundingClientRect().height)})''')
        self.assertLessEqual(facts['scroll'],facts['width']);self.assertTrue(all(h>=44 for h in facts['targets']))
    def test_20_reduced_motion_has_static_visual_baseline(self):
        self.page.close();self.page=self.context.new_page();p=self.page
        p.on('pageerror',lambda e:self.errors.append(str(e)))
        p.emulate_media(reduced_motion='reduce');p.set_content((STUDY/'NARCISSUS-study.html').read_text());wait(p,'() => !!narcissusStudy?.ready')
        self.assertFalse(self.snap()['params']['motion']);p.click('#play');p.wait_for_timeout(200)
        a=p.evaluate("() => NarcissusRelations.sha256(document.querySelector('#view').getContext('2d').getImageData(0,0,document.querySelector('#view').width,document.querySelector('#view').height).data)")
        p.wait_for_timeout(300);b=p.evaluate("() => NarcissusRelations.sha256(document.querySelector('#view').getContext('2d').getImageData(0,0,document.querySelector('#view').width,document.querySelector('#view').height).data)")
        self.assertEqual(a,b)


    def test_21_rewind_does_not_suppress_a_new_impulse(self):
        p=self.page;p.click('#play');p.wait_for_timeout(600);p.click('#pulse');p.wait_for_timeout(100)
        p.click('#reset');wait(p,'() => narcissusStudy.snapshot().frame===0');p.click('#play');p.wait_for_timeout(100);p.click('#pulse')
        doc=p.evaluate('() => narcissusStudy.artifact()');pulses=[e for e in doc['payload']['events'] if e['key']=='pulse']
        self.assertEqual(len(pulses),1);self.assertLess(pulses[0]['frame'],8)
    def test_22_microphone_envelope_is_numeric_and_tracks_are_stopped(self):
        p=self.page;p.click('#play')
        result=p.evaluate('''async () => {const c=new AudioContext(),o=c.createOscillator(),gain=c.createGain(),dest=c.createMediaStreamDestination();
          gain.gain.value=.1;o.connect(gain);gain.connect(dest);o.start();await c.resume();window.micFixture={c,o,dest};
          await narcissusStudy.live('audio',{secure:true,devices:{getUserMedia:async()=>dest.stream}});return narcissusStudy.snapshot().liveTracks;}''')
        self.assertEqual(result,1);p.wait_for_timeout(500)
        result=p.evaluate('''async () => {const doc=narcissusStudy.artifact(),mic=doc.payload.events.filter(e=>e.key==='mic');narcissusStudy.stopLive();
          const stopped=micFixture.dest.stream.getTracks().every(t=>t.readyState==='ended');micFixture.o.stop();await micFixture.c.close();
          return {stopped,count:mic.length,maximum:Math.max(...mic.map(e=>e.value)),asset:doc.payload.asset,active:narcissusStudy.snapshot().liveTracks};}''')
        self.assertTrue(result['stopped']);self.assertEqual(result['active'],0);self.assertGreater(result['count'],1)
        self.assertGreater(result['maximum'],0);self.assertLessEqual(result['maximum'],1);self.assertIsNone(result['asset'])
        MEASUREMENTS['synthetic_microphone_envelope']=result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--study',type=Path,default=STUDY);parser.add_argument('--output',type=Path,default=OUTPUT);parser.add_argument('--browser',default=BROWSER)
    args=parser.parse_args();STUDY=args.study.resolve();OUTPUT=args.output.resolve();BROWSER=args.browser;OUTPUT.mkdir(parents=True,exist_ok=True)
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(CompilerProof),unittest.defaultTestLoader.loadTestsFromTestCase(BrowserProof)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),measurements=MEASUREMENTS,
      failed=[dict(test=str(t),detail=d) for t,d in result.failures+result.errors])
    (OUTPUT/'test-results.json').write_text(json.dumps(report,indent=2)+'\n');sys.exit(not result.wasSuccessful())
