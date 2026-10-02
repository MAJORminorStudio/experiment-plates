#!/usr/bin/env python3
"""Create a 30 s edit using unchanged real plates and captured inspector states."""
import pathlib,json,hashlib,textwrap,subprocess
from PIL import Image,ImageDraw,ImageFont,ImageOps
REPO=pathlib.Path(__file__).resolve().parents[2];S=REPO/'studies/qwen3-8b-base-20261001';O=S/'publication/demo';O.mkdir(exist_ok=True)
BONE='#E7DFCC';INK='#0A0A08';GREEN='#3DA887';ORANGE='#D9643A'
def font(size,display=False):return ImageFont.truetype(str(REPO/'assets/fonts'/('Anton-Regular.ttf' if display else 'IBMPlexMono-Regular.ttf')),size)
def new(label):
 im=Image.new('RGB',(1920,1080),BONE);d=ImageDraw.Draw(im);d.text((48,27),'MAJOR//MINOR',font=font(44,True),fill=INK);d.text((1300,38),'PLATE 001 / QWEN3-8B BASE',font=font(20),fill=INK);d.line((48,90,1872,90),fill=INK,width=2);d.text((48,1036),'1,680 REAL TRIALS / STRICT-OUTPUT MICROTASKS / VISUAL 0.1',font=font(19),fill=INK);d.text((1570,1036),label,font=font(19),fill=INK);return im,d
def save(im,n):p=O/(n+'.png');im.save(p);return p
r=json.loads((S/'results.json').read_text());cs=r['conditions'];shots=[]
for i,c in enumerate(cs):
 im,d=new(c['condition']);plate=Image.open(S/'artifacts'/(c['condition']+'.png')).convert('RGB');plate=ImageOps.contain(plate,(660,905),Image.Resampling.LANCZOS);im.paste(plate,(60,110));d.text((825,190),c['condition'],font=font(118,True),fill=ORANGE if i==6 else INK);d.text((830,365),f"{c['successes']} / 240 successes",font=font(48,True),fill=INK);d.text((830,445),f"{100*c['success_rate']:.2f}% strict success",font=font(30),fill=INK)
 if i==0:caption='80 agent tasks. 3 runs each.'
 else:caption='Same tasks. Same positions.'
 for j,line in enumerate(textwrap.wrap(caption,34)):d.text((830,575+j*50),line,font=font(32),fill=INK)
 d.text((830,780),'Proposed tools. No LLM judge.',font=font(23),fill=INK);d.text((830,825),'One Base model / one M1 Max desktop',font=font(22),fill=INK)
 shots.append({'file':save(im,f'{i:02d}-{c["condition"]}').name,'frames':120 if i==0 else 55,'source':f'../../artifacts/{c["condition"]}.png','caption':caption})
im,d=new('Q2 COLLAPSE');plate=ImageOps.contain(Image.open(S/'artifacts/Q2_K.png').convert('RGB'),(660,905),Image.Resampling.LANCZOS);im.paste(plate,(60,110));d.text((815,180),'Q2_K',font=font(140,True),fill=ORANGE);d.text((820,365),'3 / 240 successes',font=font(70,True),fill=INK);d.text((825,475),'230 / 240 exhausted the token budget',font=font(26),fill=INK);d.text((825,540),'36 rejected outputs began',font=font(30),fill=INK);d.text((825,588),'with correct JSON.',font=font(30),fill=INK);d.text((825,735),'Strict output can fail after a correct start.',font=font(23),fill=INK);d.text((825,810),'Stopping behavior may contribute to the cliff.',font=font(21),fill=INK)
shots.append({'file':save(im,'07-Q2-collapse').name,'frames':210,'source':'../../artifacts/Q2_K.png','caption':'3 / 240 successes'})
rows=[json.loads(l) for l in (S/'raw/trials.jsonl').read_text().splitlines()];row=next(x for x in rows if x['id']=='Q2_K-task-003-r1')
for phase,frames in [('open',30),('select',60),('raw',60)]:
 im,d=new('EVIDENCE INSPECTOR');capture=O/('inspector-unselected.png' if phase=='open' else 'inspector-selection.png');cap=ImageOps.contain(Image.open(capture).convert('RGB'),(1230,850),Image.Resampling.LANCZOS);im.paste(cap,(40,135));d.text((1310,150),'TRACE THE MARK',font=font(43,True),fill=INK);d.text((1310,228),'Q2_K / task-003',font=font(23),fill=INK)
 if phase=='open':
  d.text((1310,340),'Open the inspector.',font=font(24),fill=INK);d.text((1310,397),'Choose Q2_K.',font=font(24),fill=INK)
 else:
  d.text((1310,320),'0 / 3 strict successes',font=font(34,True),fill=ORANGE);d.text((1310,387),'Click the failed task.',font=font(23),fill=INK)
  # An editorial pointer guides attention to the actual selected cell; it carries no data.
  x,y=520,656;d.ellipse((x-28,y-28,x+28,y+28),outline=ORANGE,width=4);d.polygon([(x+16,y+14),(x+16,y+42),(x+24,y+35),(x+34,y+52),(x+42,y+48),(x+31,y+31),(x+42,y+30)],fill=INK)
 if phase=='raw':
  d.text((1310,465),'Actual run 1 output:',font=font(21),fill=INK)
  excerpt=row['raw_output'].split('\nTask:')[0];lines=textwrap.wrap(excerpt,30,break_long_words=True)
  for j,line in enumerate(lines):d.text((1310,510+j*33),line,font=font(21),fill=GREEN)
  yy=530+len(lines)*33;d.text((1310,yy),'Then more tasks → token limit.',font=font(20),fill=ORANGE);d.text((1310,yy+44),'96 tokens / official failure',font=font(20),fill=INK);d.text((1310,yy+105),'Correct opening object shown.',font=font(18),fill=INK);d.text((1310,yy+141),'Full response stays in the ledger.',font=font(18),fill=INK)
 shots.append({'file':save(im,{'open':'08-inspector-open','select':'09-inspector-select','raw':'10-inspector-raw'}[phase]).name,'frames':frames,'source':capture.name,'caption':'Actual inspector state; editorial cursor/callout guides attention','trial_id':row['id'] if phase=='raw' else None})
im,d=new('EXPERIMENT PLATES');sheet=ImageOps.contain(Image.open(S/'artifacts/contact-sheet.png').convert('RGB'),(1110,875),Image.Resampling.LANCZOS);im.paste(sheet,(42,123));d.text((1200,225),'MAJOR//MINOR',font=font(73,True),fill=INK);d.text((1205,383),'1,680 real trials',font=font(42,True),fill=INK);d.text((1205,523),'Every mark is',font=font(43,True),fill=GREEN);d.text((1205,580),'a measurement.',font=font(43,True),fill=GREEN);d.text((1205,756),'PLATE / EXPERIMENT PLATES',font=font(22),fill=INK);d.text((1205,809),'FIXED ADDRESSES. SHARED SCALES.',font=font(21),fill=INK)
shots.append({'file':save(im,'11-contact-sheet').name,'frames':90,'source':'../../artifacts/contact-sheet.png','caption':'1,680 real trials / Every mark is a measurement.'})
assert sum(s['frames'] for s in shots)==900
concat=['ffconcat version 1.0'];at=0
for s in shots:
 s['start_frame']=at;s['end_frame_exclusive']=at+s['frames'];s['start_seconds']=at/30;s['end_seconds']=(at+s['frames'])/30;at+=s['frames'];s['sha256']=hashlib.sha256((O/s['file']).read_bytes()).hexdigest();s['source_sha256']=hashlib.sha256((O/s['source']).read_bytes()).hexdigest();concat += [f"file '{s['file']}'",'option framerate 30',f"duration {s['frames']/30:.9f}"]
concat += [f"file '{shots[-1]['file']}'",'option framerate 30'];(O/'shots.ffconcat').write_text('\n'.join(concat)+'\n')
cmd=['ffmpeg','-y','-f','concat','-safe','0','-i','shots.ffconcat','-r','30','-frames:v','900','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart','-an','plate-001-demo.mp4']
with (O/'encode.log').open('w') as log:subprocess.run(cmd,cwd=O,stdout=log,stderr=subprocess.STDOUT,check=True)
manifest={'format':'major-minor/demo@1.0','duration_seconds':30,'fps':30,'frames':900,'resolution':[1920,1080],'audio':False,'synthetic_observations':False,'plate_visual_version':'0.1','ledger_sha256':hashlib.sha256((S/'raw/trials.jsonl').read_bytes()).hexdigest(),'shots':shots,'ffmpeg_command':cmd,'mp4_sha256':hashlib.sha256((O/'plate-001-demo.mp4').read_bytes()).hexdigest()};(O/'demo-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(O/'edit-spec.md').write_text('''# Plate 001 — exact 30-second edit

1920×1080, 30 fps, H.264/yuv420p, silent, 900 frames. Hard cuts preserve the unchanged task geometry; no transitions, altered strokes or invented telemetry. All source plates are visual 0.1. The inspector shots use actual browser captures; the pointer and response callout are editorial overlays. The green snippet is explicitly the correct opening object, not the full response or an official success.

| Time | Frames (end exclusive) | Shot |
| --- | --- | --- |
'''+''.join(f"| {s['start_seconds']:.3f}–{s['end_seconds']:.3f}s | {s['start_frame']}–{s['end_frame_exclusive']} | {s['file']} |\n" for s in shots)+'''
0–4s: F16, “80 agent tasks. 3 runs each.” 4–15s: step through Q8_0, Q6_K, Q5_K_M, Q4_K_M, Q3_K_M and Q2_K at identical positions (55 frames each). 15–22s: hold on Q2, “3 / 240 successes.” 22–27s: actual inspector opening, selected failed task 003, then the correct opening JSON and its rejected status. 27–30s: contact sheet + MAJOR//MINOR, “1,680 real trials” and “Every mark is a measurement.”

From this demo directory:

```sh
ffmpeg -y -f concat -safe 0 -i shots.ffconcat -r 30 -frames:v 900 \\
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \\
  -movflags +faststart -an plate-001-demo.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames,duration -of json plate-001-demo.mp4
```

`demo-manifest.json` maps shots to frames, source assets, trial ID and hashes. `scripts/publication/demo.py` rebuilds all compositions from the same real assets and inspector captures. No benchmark is run.
''')
print('Generated 30-second / 900-frame demo, 12 PNG edit frames, concat recipe and provenance manifest.')
