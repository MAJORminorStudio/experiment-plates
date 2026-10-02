#!/usr/bin/env python3
"""Sequential on-device inference; append-only raw ledger; matched prompts and seeds."""
import argparse,datetime,glob,hashlib,json,os,pathlib,random,re,socket,subprocess,threading,time,urllib.request,urllib.error
import psutil
from suite import score,sha
from prepare import filehash,CONDITIONS,REVISION,LLAMA_REVISION
ROOT=pathlib.Path(__file__).resolve().parents[1]
PORT=18173
INFERENCE={'n_predict':96,'temperature':0.2,'top_k':40,'top_p':0.95,'min_p':0.0,'repeat_penalty':1.0,'frequency_penalty':0.0,'presence_penalty':0.0,'stop':['\n### Task:','\n### Example:'],'cache_prompt':False,'stream':False,'samplers':['penalties','top_k','top_p','min_p','temperature']}
SERVER_ARGS=['--host','127.0.0.1','--port',str(PORT),'-c','2048','-np','1','-ngl','99','-t','8','-tb','8','-b','512','-ub','512','-fa','on','-ctk','f16','-ctv','f16','--fit','off','--no-cache-prompt','--cache-ram','0','--no-cache-idle-slots','--no-webui','--metrics','--cors-origins','http://127.0.0.1:18173']
MEMORY_METHOD={'metric':'sampled llama-server process RSS','unit':'bytes','sample_interval_ms':50,'limitations':'RSS sampling is not a complete unified-memory/Metal physical-footprint account; short-lived peaks may be missed. Per-trial maximum includes the resident model and runtime.'}
def utcnow():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def request(path,payload=None,timeout=60):
 data=json.dumps(payload).encode() if payload is not None else None
 req=urllib.request.Request(f'http://127.0.0.1:{PORT}{path}',data=data,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=timeout) as response:return json.load(response)
def command(command):return subprocess.run(command,capture_output=True,text=True).stdout.strip()
class Sampler:
 def __init__(self,pid):self.pid=pid;self.peak=0;self.stop=threading.Event();self.thread=threading.Thread(target=self.sample,daemon=True)
 def sample(self):
  while not self.stop.is_set():
   try:self.peak=max(self.peak,psutil.Process(self.pid).memory_info().rss)
   except psutil.Error:pass
   self.stop.wait(.05)
 def __enter__(self):self.thread.start();return self
 def __exit__(self,*_):self.stop.set();self.thread.join()
def start_server(condition,model):
 log=open(ROOT/f'raw/server-{condition}.log','a')
 argv=['/opt/homebrew/bin/llama-server','-m',model,*SERVER_ARGS];start=time.monotonic()
 process=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
 try:
  while time.monotonic()-start<600:
   if process.poll() is not None:raise RuntimeError(f'{condition} server exited {process.returncode}; see log')
   try:
    health=request('/health',timeout=2)
    if health.get('status')=='ok':return process,log,argv,time.monotonic()-start
   except (OSError,ValueError):pass
   time.sleep(.25)
  raise RuntimeError('server health timed out')
 except:
  process.terminate()
  try:process.wait(timeout=15)
  except subprocess.TimeoutExpired:process.kill();process.wait()
  log.close();raise
def stop_server(process,log):
 process.terminate()
 try:process.wait(timeout=15)
 except subprocess.TimeoutExpired:process.kill();process.wait()
 log.close()
def bench(condition,model):
 path=ROOT/f'raw/bench-{condition}.json'
 argv=['/usr/bin/time','-l','/opt/homebrew/bin/llama-bench','-m',model,'-p','256','-n','64','-r','3','-t','8','-b','512','-ub','512','-ngl','99','-fa','on','-ctk','f16','-ctv','f16','-o','json']
 start=time.monotonic()
 with open(path,'w') as out,open(ROOT/f'raw/bench-{condition}.log','w') as err:subprocess.run(argv,stdout=out,stderr=err,check=True,timeout=900)
 rows=json.loads(path.read_text());stderr=(ROOT/f'raw/bench-{condition}.log').read_text()
 peak=re.search(r'(\d+)\s+maximum resident set size',stderr)
 footprint=re.search(r'(\d+)\s+peak memory footprint',stderr)
 return {'condition':condition,'command':argv,'wall_seconds':time.monotonic()-start,'repeats':3,'model_bytes':pathlib.Path(model).stat().st_size,'prompt_processing_tokens_per_second':next(r['avg_ts'] for r in rows if r['n_prompt']==256),'generation_tokens_per_second':next(r['avg_ts'] for r in rows if r['n_gen']==64),'maximum_rss_bytes':int(peak[1]) if peak else None,'peak_memory_footprint_bytes':int(footprint[1]) if footprint else None,'raw_measurements':rows}
def validate_generation(response,payload):
 settings=response.get('generation_settings',{})
 for key in ['n_predict','temperature','top_k','top_p','min_p','repeat_penalty','presence_penalty','frequency_penalty','seed']:
  actual=settings.get(key)
  assert actual is not None and abs(actual-payload[key])<1e-5,('runtime ignored inference control',key,actual,payload[key])
 assert settings.get('samplers')==payload['samplers'],('sampler order differs',settings.get('samplers'))
 assert settings.get('stop')==payload['stop'],'runtime stop sequences differ'
 assert not settings.get('grammar'),'unexpected output grammar'
 return True
def collect_environment():
 version=subprocess.run(['/opt/homebrew/bin/llama-server','--version'],capture_output=True,text=True)
 metal=subprocess.run(['/opt/homebrew/bin/llama-bench','--list-devices'],capture_output=True,text=True)
 for label,proc in [('llama-version',version),('metal-devices',metal)]: (ROOT/f'raw/{label}.txt').write_text(proc.stdout+'\n'+proc.stderr)
 display=json.loads(command(['system_profiler','SPDisplaysDataType','-json']))
 gpu=[{k:v for k,v in d.items() if k in ['sppci_model','spdisplays_cores','spdisplays_metal','spdisplays_vendor','sppci_bus']} for d in display.get('SPDisplaysDataType',[])]
 return {'captured_at':utcnow(),'os':command(['sw_vers']),'machine_identifier':command(['sysctl','-n','hw.model']),'memory_bytes':int(command(['sysctl','-n','hw.memsize'])),'cpu_count':psutil.cpu_count(),'graphics':gpu,'llama_revision':LLAMA_REVISION,'llama_version':(version.stdout+'\n'+version.stderr).split('load_backend:')[0].strip(),'binaries':{n:{'path':f'/opt/homebrew/bin/{n}','sha256':filehash(f'/opt/homebrew/bin/{n}')} for n in ['llama-server','llama-bench','llama-quantize']},'metal_details_file':'raw/metal-devices.txt','runtime_libraries':{'ggml':'Homebrew ggml 0.24.0','libllama':'Homebrew llama.cpp 0.4.1'},'runtime_library_sha256':{p:filehash(p) for p in sorted(set(glob.glob('/opt/homebrew/Cellar/llama.cpp/0.4.1/lib/*.dylib')+glob.glob('/opt/homebrew/Cellar/ggml/0.24.0/lib/*.dylib')+glob.glob('/opt/homebrew/Cellar/ggml/0.24.0/libexec/*.so')))},'physical_ids':'Serial numbers, hardware UUIDs, user names and device identifiers excluded.'}
def run(calibrate=False):
 suite=json.loads((ROOT/'task-suite.json').read_text());models=json.loads((ROOT/'model-manifest.json').read_text())
 assert models['source_revision']==REVISION and models['llama_revision']==LLAMA_REVISION
 with socket.socket() as sock:
  if sock.connect_ex(('127.0.0.1',PORT))==0:raise RuntimeError('Study port already in use; will not interfere with another server')
 if not calibrate:assert set(models['conditions'])==set(CONDITIONS),'Prepare all common-source quantizations before measurements'
 environment=collect_environment();assert LLAMA_REVISION[:9] in environment['llama_version'],'Installed llama.cpp revision differs';assert environment['memory_bytes']==34359738368 and environment['machine_identifier']=='Mac13,1','Wrong study hardware';(ROOT/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
 manifest={'format':'major-minor/real-study@1.0','id':'mm-qwen3-8b-base-20261001','status':'calibration' if calibrate else 'running','started_at':utcnow(),'synthetic':False,'model':models['model'],'source_revision':REVISION,'llama_revision':LLAMA_REVISION,'visualVersion':'0.1','rendererVersion':'0.1.0','conditions':CONDITIONS,'tasks':80,'repeats':3,'target_trial_count':1680,'suite_sha256':filehash(ROOT/'task-suite.json'),'scorer_sha256':filehash(ROOT/'scripts/suite.py'),'system_prompt':suite['system_prompt'],'tool_definitions':suite['tool_definitions'],'few_shot_examples':suite['few_shot_examples'],'inference':INFERENCE,'server_args':SERVER_ARGS,'seed_rule':'100000 + task array index * 10 + run index (1..3); same per task/run in all conditions','context_size':2048,'request_timeout_seconds':60,'memory_method':MEMORY_METHOD,'prompt_caching':False,'grammar_constrained_output':False,'llm_judge':None,'trial_order':'Repeat blocks 1,2,3; deterministic task shuffle seed 20261001+run, reused in each condition','condition_order':CONDITIONS,'performance':'Separate llama-bench pp256 and tg64, 3 measurements, warmed; trial speed recorded separately','load_time_definition':'wall time from process spawn to health ready, including runtime/model load and warmup','environment_file':'environment.json','model_manifest_file':'model-manifest.json','renderer_freeze':'../../releases/visual-0.1.freeze.json','primary_degradation_rule':'At least 5 percentage-point paired drop vs F16 and positive lower bound of 95% task-cluster bootstrap interval (10000 resamples). Exploratory categories, no multiplicity-corrected claim.','limitations':['Agent-relevant microtasks with proposed tools, not an end-to-end agent execution benchmark','Base completion model; fixed few-shot instructions, no instruction-tuned model substituted','Long-context tasks target retention within 2048-token context, not 32768-token capability','Fixed sequential condition order can confound performance with thermal or background load drift','Three seeds per task; task cluster is the analysis unit for uncertainty']}
 if not calibrate:(ROOT/'experiment-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 ledger_path=ROOT/'raw/trials.jsonl';existing=[]
 if ledger_path.exists():existing=[json.loads(line) for line in ledger_path.read_text().splitlines() if line]
 done={(r['condition'],r['task_id'],r['run']) for r in existing};assert len(done)==len(existing),'Duplicate existing ledger slots'
 for row in existing:assert row['suite_sha256']==manifest['suite_sha256'] and row['scorer_sha256']==manifest['scorer_sha256'],'Resume would change benchmark/scorer'
 performance=json.loads((ROOT/'performance.json').read_text()) if (ROOT/'performance.json').exists() else {}
 for condition in ['F16'] if calibrate else CONDITIONS:
  condition_done=[s for s in done if s[0]==condition]
  if len(condition_done)==240 and not calibrate:print(condition,'already has 240 trials',flush=True);continue
  model=models['conditions'][condition];model_path=str(ROOT/'models'/pathlib.Path(model['path']).name);assert filehash(model_path)==model['sha256'],'Model hash mismatch'
  print(condition,'model hash verified',flush=True)
  before={'at':utcnow(),'thermal':command(['pmset','-g','therm']),'vm_stat':command(['vm_stat']),'memory_available':psutil.virtual_memory().available}
  if condition not in performance and not calibrate:
   print(condition,'controlled llama-bench starting',flush=True);performance[condition]=bench(condition,model_path);(ROOT/'performance.json').write_text(json.dumps(performance,indent=2)+'\n')
  process,log,argv,load=start_server(condition,model_path)
  print(condition,'server ready in',round(load,2),'seconds',flush=True)
  try:
   if calibrate:
    rows=[]
    for index in [0,8,16,24,32,40,48,56,64,72]:
     task=suite['tasks'][index];payload={**INFERENCE,'seed':100000+index*10+1,'prompt':task['prompt']}
     response=request('/completion',payload);validate_generation(response,payload);evaluation=score(task,response['content'],response.get('stop_type'))
     rows.append({'task_id':task['id'],'prompt':task['prompt'],'request':payload,'response':response,'evaluation':evaluation});print(task['id'],evaluation['success'],repr(response['content'][:180]),flush=True)
    (ROOT/'raw/calibration-F16.json').write_text(json.dumps(rows,indent=2)+'\n');return
   maxprompt=0
   for task in suite['tasks']:
    tokens=request('/tokenize',{'content':task['prompt'],'add_special':False})['tokens'];maxprompt=max(maxprompt,len(tokens))
    assert len(tokens)+INFERENCE['n_predict']<2048,('Task exceeds shared context',task['id'],len(tokens))
   performance[condition].update({'server_command':argv,'load_to_ready_seconds':load,'max_task_prompt_tokens':maxprompt,'system_before':before})
   # One neutral warmup, excluded from the task ledger and all success estimates.
   request('/completion',{**INFERENCE,'prompt':'Return the JSON object {"ready":true}.\nAnswer:','seed':7,'n_predict':16})
   successes=sum(r['success'] for r in existing if r['condition']==condition)
   for run_index in [1,2,3]:
    indices=list(range(80));random.Random(20261001+run_index).shuffle(indices)
    for index in indices:
     task=suite['tasks'][index];slot=(condition,task['id'],run_index)
     if slot in done:continue
     payload={**INFERENCE,'prompt':task['prompt'],'seed':100000+index*10+run_index}
     started_at=utcnow();start=time.monotonic();response=None;transport=None
     with Sampler(process.pid) as memory:
      try:response=request('/completion',payload)
      except (TimeoutError,socket.timeout):transport='timeout'
      except (OSError,ValueError) as e:raise RuntimeError(f'Infrastructure failure at {slot}; no model-outcome row written: {e}') from e
     wall_ms=(time.monotonic()-start)*1000
     if transport:raise RuntimeError(f'Request timed out at {slot}; preserve logs and diagnose before continuing')
     assert response is not None
     validate_generation(response,payload)
     evaluation=score(task,response['content'],response.get('stop_type'))
     timings=response.get('timings',{})
     row={'id':f'{condition}-{task["id"]}-r{run_index}','condition':condition,'task_id':task['id'],'task_name':task['name'],'category':task['category'],'run':run_index,'started_at':started_at,'finished_at':utcnow(),'model_sha256':model['sha256'],'source_revision':REVISION,'llama_revision':LLAMA_REVISION,'suite_sha256':manifest['suite_sha256'],'scorer_sha256':manifest['scorer_sha256'],'prompt_sha256':task['prompt_sha256'],'seed':payload['seed'],'latency_ms':wall_ms,'prompt_tokens':timings.get('prompt_n',response.get('tokens_evaluated')),'generated_tokens':timings.get('predicted_n',response.get('tokens_predicted')),'prompt_processing_tokens_per_second':timings.get('prompt_per_second'),'tokens_per_second':timings.get('predicted_per_second'),'sampled_peak_rss_bytes':memory.peak,'memory_gb':memory.peak/1e9 if memory.peak else None,'request':payload,'response':response,'raw_output':response['content'],**evaluation}
     with open(ledger_path,'a') as ledger:ledger.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n');ledger.flush();os.fsync(ledger.fileno())
     done.add(slot);successes+=int(row['success']);count=len([s for s in done if s[0]==condition])
     if count%10==0:print(condition,f'{count}/240',f'{successes} successes',task['id'],row['error_category'] or 'intact',flush=True)
   performance[condition]['system_after']={'at':utcnow(),'thermal':command(['pmset','-g','therm']),'vm_stat':command(['vm_stat']),'memory_available':psutil.virtual_memory().available}
   (ROOT/'performance.json').write_text(json.dumps(performance,indent=2)+'\n')
  finally:stop_server(process,log)
  print(condition,'COMPLETE',len([s for s in done if s[0]==condition]),flush=True)
 manifest.update({'status':'inference_complete','finished_at':utcnow(),'trial_count':len(done),'ledger_sha256':filehash(ledger_path),'performance_sha256':filehash(ROOT/'performance.json')})
 assert len(done)==1680
 (ROOT/'experiment-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('ALL 1680 TRIALS COMPLETE',flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--calibrate',action='store_true');args=parser.parse_args();run(args.calibrate)
