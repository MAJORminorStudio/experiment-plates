#!/usr/bin/env python3
"""Replay existing evidence and audit publication; no inference or benchmark calls."""
import pathlib,json,hashlib,sys,math,re,collections,subprocess
from html.parser import HTMLParser
from urllib.parse import urlparse,unquote
REPO=pathlib.Path(__file__).resolve().parents[2];S=REPO/'studies/qwen3-8b-base-20261001';P=S/'publication'
sys.path.insert(0,str(S/'scripts'))
from suite import score
checks=[]
def check(ok,name):
 if not ok:raise AssertionError(name)
 checks.append(name)
def load(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
r=load(S/'results.json');m=load(S/'experiment-manifest.json');models=load(S/'model-manifest.json');v=load(S/'validation.json');a=load(P/'article-data.json');tasks={x['id']:x for x in load(S/'task-suite.json')['tasks']}
rows=[json.loads(l) for l in (S/'raw/trials.jsonl').read_text().splitlines()];conditions=['F16','Q8_0','Q6_K','Q5_K_M','Q4_K_M','Q3_K_M','Q2_K']
check(not r['synthetic'] and not m['synthetic'] and r['trial_count']==len(rows)==1680,'1,680 real trials; no synthetic study data')
check({(x['condition'],x['task_id'],x['run']) for x in rows}=={(c,t,n) for c in conditions for t in tasks for n in [1,2,3]},'Every condition/task/repeat slot present once')
check(sha(S/'raw/trials.jsonl')==m['ledger_sha256']==v['ledger_sha256'],'Original ledger hash unchanged')
check(sha(S/'results.json')==v['results_sha256']==a['results_sha256'],'Original results hash unchanged; article matches source')
check(sha(S/'scripts/suite.py')==m['scorer_sha256'] and sha(S/'task-suite.json')==m['suite_sha256'],'Scorer and task suite hashes unchanged')
for x in rows:
 fresh=score(tasks[x['task_id']],x['raw_output'],x['response'].get('stop_type'))
 for k,value in fresh.items():assert x[k]==value,(x['id'],k)
 assert x['model_sha256']==models['conditions'][x['condition']]['sha256']
 assert x['request']['prompt']==tasks[x['task_id']]['prompt'] and x['prompt_sha256']==tasks[x['task_id']]['prompt_sha256']
 assert {k:v for k,v in x['request'].items() if k not in ['prompt','seed']}==m['inference']
check(True,'All 1,680 scorer decisions, native parameters, prompt hashes and model labels replayed')
article=(P/'article.md').read_text();html=(P/'index.html').read_text()
counts=collections.defaultdict(lambda:collections.Counter())
for x in rows:counts[x['condition']][x['task_id']]+=x['success']
for c in r['conditions']:
 rr=[x for x in rows if x['condition']==c['condition']];n=sum(x['success'] for x in rr)
 assert n==c['successes'] and len(rr)==c['trials']==240 and math.isclose(n/len(rr),c['success_rate'])
 assert f"{c['success_rate']*100:.2f}%" in article and f"{n}/{len(rr)}" in article
 expected={k:c[k] for k in a['conditions'][0]};assert expected==next(x for x in a['conditions'] if x['condition']==c['condition'])
 assert math.isclose(c['model_size_saving_vs_f16'],1-c['model_bytes']/r['conditions'][0]['model_bytes'])
 assert math.isclose(c['controlled_generation_gain_vs_f16'],c['controlled_generation_tokens_per_second']/r['conditions'][0]['controlled_generation_tokens_per_second'])
 for cat,entries in r['capability_categories'].items():
  e=next(e for e in entries if e['condition']==c['condition']);catrows=[x for x in rr if x['category']==cat];assert sum(x['success'] for x in catrows)==e['successes'] and len(catrows)==e['trials']==24 and math.isclose(e['success_rate'],e['successes']/24)
check(True,'All article rates, success counts, category counts, size savings and speed ratios recomputed')
reversals=sum(any(counts[conditions[i]][t]<counts[conditions[i+1]][t] for i in range(6)) for t in tasks)
check(reversals==r['non_monotonic_task_count']==a['task_reversals']==14,'14 task reversals recomputed')
q2=[x for x in rows if x['condition']=='Q2_K'];budget=sum(x['error_flags']['timeout_loop'] for x in q2)
check(budget==230==a['q2_budget_exhaustions'],'230 Q2 budget exhaustions recomputed')
prefix=[]
for x in q2:
 try:obj,end=json.JSONDecoder().raw_decode(x['raw_output'].lstrip())
 except (ValueError,TypeError):continue
 if not x['success'] and score(tasks[x['task_id']],json.dumps(obj,separators=(',',':')))['success']:prefix.append(x['id'])
check(len(prefix)==36==a['correct_prefix_q2'],'36 rejected Q2 responses with oracle-correct JSON prefixes independently checked')
check(not any(counts['F16'][t]>=2 and counts['Q2_K'][t]>=2 for t in tasks) and not r['unusually_late_robust_tasks'],'No task meets Q2 late-robustness criterion')
norm=load(S/'normalized.json');rawby={x['id']:x for x in rows}
check(norm['experiment']['synthetic'] is False and len(norm['observations'])==1680,'Normalized dataset contains every real observation')
for o in norm['observations']:
 x=rawby[o['id']];assert o['success']==x['success'] and o['condition']==x['condition'] and o['unit']==x['task_id'] and o['run']==x['run']
check(True,'Normalized outcomes trace back to raw ledger')
for file,expected in load(REPO/'releases/visual-0.1.freeze.json')['files'].items():assert sha(REPO/file)==expected,file
check(True,'PLATE visual 0.1 frozen renderer, schema, fonts and lockfiles unchanged')
verification=load(S/'artifacts/verification.json');check(verification['status']=='passed' and len(verification['artifacts'])==37,'All 37 SVG manifests verified by study verifier')
for item in verification['artifacts']:assert sha(S/'artifacts'/item['file'])==item['svgHash']
from PIL import Image
for item in v['png_files']:
 path=S/item['file'];assert sha(path)==item['sha256']
 with Image.open(path) as im:assert im.size==(item['width'],item['height']);im.verify()
check(True,'37 original PNGs decode and match audited image hashes')
class Links(HTMLParser):
 def __init__(self):super().__init__();self.urls=[];self.ids=set()
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if 'id' in d:self.ids.add(d['id'])
  for key in ['src','href']:
   if key in d:self.urls.append(d[key])
parser=Links();parser.feed(html);checked=[]
for url in parser.urls:
 u=urlparse(url)
 if u.scheme in ['data','mailto']:continue
 assert not u.scheme,'Article requires offline local assets'
 if u.path:assert (P/unquote(u.path)).resolve().is_file(),url;checked.append(url)
 if not u.path and u.fragment:assert u.fragment in parser.ids,url
check(True,'All article links and assets resolve; no external service dependency')
md_files=[REPO/'README.md',REPO/'docs/renderer-0.1.md']+[S/name for name in ['README.md','methodology.md','reproduction.md','LICENSES.md']]+list(P.glob('*.md'))
md_count=0
for path in md_files:
 for url in re.findall(r'\]\(([^)]+)\)',path.read_text()):
  u=urlparse(url)
  if u.scheme:continue
  assert (path.parent/unquote(u.path)).resolve().exists(),(str(path),url)
  md_count+=1
check(True,f'All {md_count} authored Markdown local links resolve')
check(sha(S/'source-model-card.md')==models['source_files']['README.md']['sha256'],'Pinned upstream model card and license declaration preserved byte-for-byte')
attribution=load(P/'qa/attribution-links.json');check(len(attribution)==3 and all(x.get('status')==200 for x in attribution),'Three external font/renderer attribution URLs returned HTTP 200')

check('results.json' in html and 'trials.jsonl' in html and 'Limitations' in html,'Raw data and limitations accessible from article')
check('do **not** establish that Q6 beats F16' in article and 'do not present this as confirmed overall degradation' in article and 'Desktop swapping affected the measurements' in article,'Required Q6, Q3 and 2.47× caveats visible')
check('36' in article and '14' in article and 'Plate 002 has not been run' in article,'Diagnostic counts and unrun Plate 002 plan present')
social=load(P/'social/validation.json')
check(social['visual_review']['status']=='passed' and social['checks']['optical_thickness_increased_20_percent'],'Final 1600×1600 launch image reviewed with 20% optical-weight increase')
for output in social['outputs']:assert sha(P/'social'/output['file'])==output['sha256']
check(True,'Final social PNG/SVG hashes match reviewed exports')
production=load(P/'site-integration/production-validation.json')
check(production['status']=='passed' and not production['browser_errors'],'Integrated research route production-relative browser QA passed')
posts=load(P/'social-posts.json');check(len(posts)==3 and all(x['characters']==len(x['text'])<=280 for x in posts) and posts[0]['attach']=='social/plate-001-launch-1600.png','Three differentiated X posts fit 280 characters; square graphic is primary launch image')
qa=load(P/'qa/browser-report.json');check(qa['status']=='passed' and not qa['browser_errors'],'Browser QA: images, links, interactive selectors, inspector and mobile passed')
demo=load(P/'demo/demo-manifest.json');check(demo['ledger_sha256']==m['ledger_sha256'] and not demo['synthetic_observations'] and demo['plate_visual_version']=='0.1','Demo uses real data and frozen visual 0.1')
for shot in demo['shots']:
 assert sha(P/'demo'/shot['file'])==shot['sha256'] and sha(P/'demo'/shot['source'])==shot['source_sha256']
check(True,'All 12 demo edit frames and original input sources match provenance hashes')
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(P/'demo/plate-001-demo.mp4')]))
stream=probe['streams'][0];check(stream['width']==1920 and stream['height']==1080 and stream['r_frame_rate']=='30/1' and int(stream['nb_frames'])==900 and float(probe['format']['duration'])==30,'Demo: 1920×1080, 30 fps, 900 frames, exactly 30 seconds')
check(sha(P/'demo/plate-001-demo.mp4')==demo['mp4_sha256'],'MP4 hash matches demo manifest')
report={'status':'passed','publication_status':'prepared_unpublished','benchmark_rerun':False,'next_experiment_run':False,'checks':checks,'local_link_count':len(checked),'browser_report':'qa/browser-report.json','raw_ledger_sha256':m['ledger_sha256'],'results_sha256':a['results_sha256'],'validation_failures':[],'manual_approval_remaining':['Post the prepared social copy when the article has a public URL'],'limitations':['Observed decode throughput affected by desktop swapping','One Base model and hardware system; three repeats; strict-output microtasks','Related task templates and exploratory category comparisons','Weak state/constraint reference categories; Q2 stopping effects']}
(P/'validation-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'Publication audit passed: {len(checks)} checks, 1,680 rescored observations, {len(checked)} local article assets/links, exact 30-second video.')
