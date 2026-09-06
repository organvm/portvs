#!/usr/bin/env python3
"""Build an offline NARCISSUS study over the existing normalized compiler/runtime.

Default sources are synthetic. --image explicitly makes moving-still derivatives
in an ignored local output, never overwrites or publishes the original.
"""
from __future__ import annotations
import argparse, base64, hashlib, json, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
sys.path.insert(0,str(PARENT))
import composition as c
from browser_runtime import compile_plan
UPSTREAM={"composition.py":"c943ae82f0807686ffef5dc15cbf5d5dcc66ca48",
          "browser_runtime.py":"9bf5561bfe336af98f0f0c887301de74a03baccb",
          "browser_runtime.js":"82a3fce7066b882cf7d0c393981bc41a6467668b"}

def blob(path:Path)->str:
    b=path.read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def layouts()->dict:
    def cell(role,rect):return dict(loop=role,rect=rect,fit='cover',focal=['1/2','1/2'])
    return {
      'landscape':dict(name='narcissus-study-001-landscape',cells=[cell('self',[0,0,'3/5',1]),cell('reflection',['3/5',0,'2/5','3/5']),cell('echo',['3/5','3/5','2/5','2/5'])]),
      'portrait':dict(name='narcissus-study-001-portrait',cells=[cell('self',[0,0,1,'3/5']),cell('reflection',[0,'3/5','1/2','2/5']),cell('echo',['1/2','3/5','1/2','2/5'])])}

def build(output:Path,image:Path|None=None)->dict:
    output=output.resolve()
    if not output.is_relative_to(PARENT/'runtime-proof'):
        raise ValueError('Output must remain in incubator/triptych-video-canon/runtime-proof/')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a fresh output directory; existing study is never overwritten')
    for name,expected in UPSTREAM.items():
        if blob(PARENT/name)!=expected:raise ValueError('Upstream changed; revalidate adapter: '+name)
    output.mkdir(parents=True,exist_ok=True);(output/'media').mkdir()
    original=None
    if image:
        image=image.resolve();raw=image.read_bytes()
        original=hashlib.sha256(raw).hexdigest()
        facts=json.loads(subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,codec_name','-of','json',str(image)],check=True,capture_output=True,text=True).stdout)['streams'][0]
        if facts['codec_name'] not in ('mjpeg','png'):raise ValueError('Still input must be JPEG or PNG')
    sources=[];recipes=[]
    crops=[(0,0,1,1),(.015,.29,.36,.65),(.31,.14,.68,.62)]
    for i,(role,seconds) in enumerate(zip(('self','reflection','echo'),(8,10,12))):
        temp=output/'media'/f'{role}.mp4';frames=24*seconds
        cmd=['ffmpeg','-v','error','-nostdin','-y']
        if image:
            x,y,w,h=crops[i];W,H=facts['width'],facts['height']
            X,Y,CW,CH=[int(n)//2*2 for n in (W*x,H*y,W*w,H*h)]
            filt=f"crop={CW}:{CH}:{X}:{Y},scale=720:960:force_original_aspect_ratio=increase,crop=720:960,zoompan=z='1.025+0.015*sin(on*2*PI/{frames})':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s=480x640:fps=24,format=yuv420p"
            cmd+=['-i',str(image),'-vf',filt,'-frames:v',str(frames)]
            recipes.append(dict(id=role,operation='moving-still-derivative',crop_pixels=[X,Y,CW,CH],duration=seconds,filter=filt,ancestor_sha256=original))
        else:
            cmd+=['-f','lavfi','-i',f'testsrc2=size=480x640:rate=24:duration={seconds}', '-vf',f'hue=h={i*65}']
            recipes.append(dict(id=role,operation='synthetic-testsrc2',duration=seconds,hue=i*65))
        cmd+=['-an','-c:v','libx264','-preset','veryfast','-crf','27','-pix_fmt','yuv420p','-movflags','+faststart',str(temp)]
        subprocess.run(cmd,check=True,timeout=60)
        digest=c.sha256_file(temp);target=temp.with_name(digest+'.mp4');temp.rename(target)
        sources.append(dict(id=role+'-source',path='media/'+target.name,sha256=digest,kind='video',duration=str(seconds)))
    state=dict(schema_version=1,engine_version=c.ENGINE_VERSION,rng=c.RNG,seed='narcissus-study-001',fps=24,frames=1440,
      sources=sources,loops=[dict(id=role,bank=[s['id']],offset=str(i),rate='1',period=s['duration'],epoch=0,held=False) for i,(role,s) in enumerate(zip(('self','reflection','echo'),sources))],
      layouts=layouts(),events=[],audio=dict(mode='none',routing=None,generative=None),allow_source_reuse=True)
    c.validate_state(state);c.media_paths(state,output);c.save_state(state,output/'state.json')
    plan=compile_plan(state)
    for s in plan['sources']:s['bytes']=(output/s['path']).stat().st_size
    (output/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    proof=dict(schema='narcissus-source-custody-0.1',upstream_commit='beecfee905cb2685b7c71ede13a1955faed6c153',upstream_blobs=UPSTREAM,
      source_class='moving-still derivatives' if image else 'synthetic engineering fixtures',ancestor_sha256=original,
      original_unchanged=(not image or c.sha256_file(image)==original),derivatives=recipes,media=sources,
      historical_video_recovered=False,artist_approved=False,publication_authorized=False)
    (output/'custody.json').write_text(json.dumps(proof,indent=2)+'\n')
    bundle=dict(plan=plan,state=state,sourceClass=proof['source_class'],ancestor=original,
      media={s['id']:base64.b64encode((output/s['path']).read_bytes()).decode('ascii') for s in sources})
    html=(HERE/'index.template.html').read_text()
    replacements={'/*__RELATIONS__*/':(HERE/'relations.js').read_text(),'/*__BUNDLE__*/':json.dumps(bundle,separators=(',',':')).replace('<','\\u003c'),
      '/*__UPSTREAM__*/':(PARENT/'browser_runtime.js').read_text(),'/*__APP__*/':(HERE/'instrument.js').read_text()}
    for a,b in replacements.items():html=html.replace(a,b)
    (output/'NARCISSUS-study.html').write_text(html)
    return dict(output=str(output),state_sha256=plan['state_sha256'],source_class=proof['source_class'],media_bytes=sum(s['bytes'] for s in plan['sources']))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--image',type=Path);args=p.parse_args()
    print(json.dumps(build(args.output,args.image),indent=2))
