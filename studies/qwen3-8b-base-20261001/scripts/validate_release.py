#!/usr/bin/env python3
"""Final release audit against observed evidence and independently saved reviews."""
import hashlib,json,pathlib,re,struct
from prepare import CONDITIONS,filehash
ROOT=pathlib.Path(__file__).resolve().parents[1]
def read(name):return json.loads((ROOT/name).read_text())
def main():
 v=read('validation.json');manifest=read('experiment-manifest.json');models=read('model-manifest.json');verification=read('artifacts/verification.json')
 assert verification['status']=='passed' and verification['trial_count']==1680 and not verification['synthetic']
 assert len(verification['artifacts'])==37
 manual=read('manual-failure-review.json');assert manual and all(r['review_status']=='passed' and r.get('review_notes') for r in manual),'Manual failure inspection remains pending'
 visual=read('visual-review.json');assert all(visual.get(k,{}).get('status')=='passed' for k in ['hero','contact_sheet','inspector']),'Visual inspection remains pending'
 native=[json.loads(line) for line in (ROOT/'raw/trials.jsonl').read_text().splitlines()]
 assert len(native)==1680 and {r['condition'] for r in native}==set(CONDITIONS)
 assert all(r['response']['timings'].get('cache_n')==0 for r in native),'Unexpected prompt reuse'
 assert all(not r['response'].get('truncated') for r in native),'Context truncated'
 assert filehash(ROOT/'raw/trials.jsonl')==manifest['ledger_sha256']==v['ledger_sha256']
 checks={}
 for c in CONDITIONS:
  info=models['conditions'][c];actual=filehash(info['path']);assert actual==info['sha256'],c
  checks[c]={'sha256':actual,'bytes':pathlib.Path(info['path']).stat().st_size,'status':'passed'}
  print(c,'final model hash passed',flush=True)
 for file,expected in read('../../releases/visual-0.1.freeze.json')['files'].items():assert filehash(ROOT/'../..'/file)==expected,('Freeze mismatch',file)
 pngs=[]
 for item in verification['artifacts']:
  p=ROOT/'artifacts'/item['file'].replace('.svg','.png');b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';width,height=struct.unpack('>II',b[16:24])
  assert {'width':width,'height':height}==item['dimensions'],p
  pngs.append({'file':str(p.relative_to(ROOT)), 'width':width,'height':height,'sha256':hashlib.sha256(b).hexdigest()})
 html=(ROOT/'artifacts/inspector.html').read_text();match=re.search(r'<script id="evidence" type="application/json">([\s\S]*?)</script>',html);assert match
 payload=json.loads(match[1]);assert payload['provenance']['raw_ledger_sha256']==manifest['ledger_sha256']
 byid={r['id']:r for r in native};assert len(payload['data']['observations'])==1680
 for o in payload['data']['observations']:
  r=byid[o['id']];assert o['raw_output']==r['raw_output'] and o['error_flags']==r['error_flags'] and o['prompt_tokens']==r['prompt_tokens'] and o['generated_tokens']==r['generated_tokens']
 assert not re.search(r'''<(?:script|link)\b[^>]*(?:src|href)\s*=\s*["']https?://''',html,re.I),'Inspector external asset dependency'
 for attrs,body in re.findall(r'<script([^>]*)>([\s\S]*?)</script>',html):
  if 'application/json' not in attrs:assert not re.search(r'\b(?:fetch|XMLHttpRequest|WebSocket)\s*\(',body),'Inspector network call'
 perf=read('performance.json')
 for c in CONDITIONS:
  assert perf[c]['load_to_ready_seconds']>0
  for measurement in perf[c]['raw_measurements']:
   assert measurement['build_commit']==manifest['llama_revision'][:9]
   assert measurement['model_filename']==models['conditions'][c]['path']
   assert measurement['n_gpu_layers']==99 and measurement['n_threads']==8 and measurement['n_batch']==512
   assert measurement['flash_attn']==1 and measurement['type_k']=='f16' and measurement['type_v']=='f16'
   assert len(measurement['samples_ts'])==3 and all(x>0 for x in measurement['samples_ts'])
 v.update({'status':'passed','manual_failure_review':'passed','manual_sample_count':len(manual),'artifact_verification':'passed','svg_manifest_count':37,'png_file_count':37,'png_files':pngs,'final_model_hashes':checks,'frozen_renderer':'unchanged','canonical_panel_datasets':4,'stable_task_addresses':80,'shared_scales':verification['scales'],'prompt_cache_reused_tokens':0,'context_truncations':0,'visual_review':'visual-review.json','inspector_raw_observation_count':1680,'controlled_benchmarks':'three native samples per test per condition validated'})
 (ROOT/'validation.json').write_text(json.dumps(v,indent=2)+'\n')
 print('FINAL RELEASE AUDIT PASSED',flush=True)
if __name__=='__main__':main()
