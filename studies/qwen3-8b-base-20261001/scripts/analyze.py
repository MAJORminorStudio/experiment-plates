#!/usr/bin/env python3
"""Rescore the ledger, validate the design, emit measured canonical data and paired analyses."""
import collections,csv,hashlib,json,pathlib,re,statistics
import numpy as np
from suite import score,CATEGORIES
from run import validate_generation
from prepare import CONDITIONS,filehash
ROOT=pathlib.Path(__file__).resolve().parents[1]
METRICS={'success':{'type':'boolean','unit':'boolean'},'latency_ms':{'type':'number','unit':'ms'},'tokens_per_second':{'type':'number','unit':'tokens/s'},'memory_gb':{'type':'number','unit':'GB'},'error_category':{'type':'category','unit':'category'}}
ERROR_MAP={'malformed_structured_output':'schema','wrong_tool':'tool_selection','wrong_arguments':'tool_arguments','incomplete_plan':'planning','state_loss':'state_loss','failure_to_recover':'planning','premature_completion':'planning','constraint_violation':'instruction','reasoning':'reasoning','timeout_loop':'timeout','other':'other'}
def bootstrap(values,seed):
 a=np.array(values,dtype=float);rng=np.random.default_rng(seed);samples=a[rng.integers(0,len(a),size=(10000,len(a)))].mean(axis=1)
 return [float(x) for x in np.quantile(samples,[.025,.975])]
def main():
 suite=json.loads((ROOT/'task-suite.json').read_text());tasks=suite['tasks'];by_task={t['id']:t for t in tasks}
 manifest=json.loads((ROOT/'experiment-manifest.json').read_text());models=json.loads((ROOT/'model-manifest.json').read_text());perf=json.loads((ROOT/'performance.json').read_text())
 rows=[json.loads(line) for line in (ROOT/'raw/trials.jsonl').read_text().splitlines() if line]
 assert len(rows)==1680 and manifest['trial_count']==1680 and manifest['synthetic'] is False
 assert len({(r['condition'],r['task_id'],r['run']) for r in rows})==1680
 assert filehash(ROOT/'task-suite.json')==manifest['suite_sha256'] and filehash(ROOT/'scripts/suite.py')==manifest['scorer_sha256']
 expected_slots={(c,t['id'],r) for c in CONDITIONS for t in tasks for r in [1,2,3]};assert {(r['condition'],r['task_id'],r['run']) for r in rows}==expected_slots
 for r in rows:
  task=by_task[r['task_id']];validate_generation(r['response'],r['request']);fresh=score(task,r['raw_output'],r['response'].get('stop_type'))
  for k in fresh:assert fresh[k]==r[k],(r['id'],k,'rescore mismatch')
  assert r['prompt_sha256']==task['prompt_sha256'] and r['request']['prompt']==task['prompt']
  assert r['model_sha256']==models['conditions'][r['condition']]['sha256']
  assert r['latency_ms']>0 and r['tokens_per_second'] is not None and r['generated_tokens'] is not None
  assert r['prompt_tokens']+96<2048,(r['id'],'context overflow')
  assert {k:v for k,v in r['request'].items() if k not in ['prompt','seed']}==manifest['inference']
 index={(r['condition'],r['task_id'],r['run']):r for r in rows}
 ordered=[index[c,t['id'],run] for c in CONDITIONS for t in tasks for run in [1,2,3]]
 dataset={'experiment':{'id':manifest['id'],'title':'Agent capability under compression','model':'Qwen3-8B Base','repeats':3,'synthetic':False,'description':'Measured local Mac Studio M1 Max / 32 GB study. 80 programmatically scored agent-relevant microtasks, three matched seeds, seven common-source GGUF conditions. Proposed tools, not an end-to-end agent. Raw ledger, native responses, benchmark measurements and scoring rules preserved.'},'conditions':[{'id':c,'label':c} for c in CONDITIONS],'units':[{'id':t['id'],'name':t['name']} for t in tasks],'metrics':METRICS,'observations':[{'id':r['id'],'condition':r['condition'],'unit':r['task_id'],'run':r['run'],'success':r['success'],'latency_ms':r['latency_ms'],'tokens_per_second':r['tokens_per_second'],'memory_gb':r['memory_gb'],'error_category':ERROR_MAP.get(r['error_category'])} for r in ordered]}
 (ROOT/'normalized.json').write_text(json.dumps(dataset,indent=2,ensure_ascii=False)+'\n')
 with open(ROOT/'raw/trials.csv','w',newline='') as f:
  columns=['id','condition','task_id','task_name','category','run','success','latency_ms','prompt_tokens','generated_tokens','tokens_per_second','prompt_processing_tokens_per_second','memory_gb','sampled_peak_rss_bytes','error_category',*list(rows[0]['error_flags']),'raw_output','prompt_sha256','model_sha256','seed']
  writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
  for r in ordered:writer.writerow({**{k:r[k] for k in columns if k in r},**r['error_flags']})
 counts={c:{t['id']:sum(index[c,t['id'],run]['success'] for run in [1,2,3]) for t in tasks} for c in CONDITIONS}
 results={'format':'major-minor/results@1.0','experiment_id':manifest['id'],'synthetic':False,'trial_count':1680,'conditions':[],'capability_categories':{},'uncertainty_method':'Matched paired task-cluster bootstrap, 10000 seeded resamples; three repeats per task are kept together. Category results exploratory, no multiplicity correction.','meaningful_drop_rule':manifest['primary_degradation_rule'],'first_meaningful_degradation':None}
 ref_mem=perf['F16']['maximum_rss_bytes'];ref_tps=perf['F16']['generation_tokens_per_second']
 for ci,c in enumerate(CONDITIONS):
  condition_rows=[r for r in rows if r['condition']==c];succ=sum(r['success'] for r in condition_rows)
  differences=[(counts['F16'][t['id']]-counts[c][t['id']])/3 for t in tasks];drop=statistics.mean(differences);interval=bootstrap(differences,20261001+ci)
  memory=perf[c]['maximum_rss_bytes']
  entry={'condition':c,'successes':succ,'trials':240,'success_rate':succ/240,'success_rate_task_cluster_ci95':bootstrap([counts[c][t['id']]/3 for t in tasks],33300+ci),'paired_drop_vs_f16':drop,'paired_drop_ci95':interval,'meaningful_degradation':ci>0 and drop>=.05 and interval[0]>0,'median_trial_latency_ms':statistics.median(r['latency_ms'] for r in condition_rows),'median_trial_generation_tokens_per_second':statistics.median(r['tokens_per_second'] for r in condition_rows),'model_bytes':models['conditions'][c]['bytes'],'model_sha256':models['conditions'][c]['sha256'],'controlled_prompt_processing_tokens_per_second':perf[c]['prompt_processing_tokens_per_second'],'controlled_generation_tokens_per_second':perf[c]['generation_tokens_per_second'],'controlled_generation_gain_vs_f16':perf[c]['generation_tokens_per_second']/ref_tps,'bench_peak_memory_bytes':memory,'bench_memory_metric':'peak memory footprint' if perf[c].get('peak_memory_footprint_bytes') else 'maximum RSS','bench_memory_saving_vs_f16':1-memory/ref_mem if memory and ref_mem else None,'model_size_saving_vs_f16':1-models['conditions'][c]['bytes']/models['conditions']['F16']['bytes'],'load_to_ready_seconds':perf[c]['load_to_ready_seconds'],'primary_error_counts':dict(collections.Counter(r['error_category'] for r in condition_rows if not r['success'])),'error_flag_counts':{k:sum(r['error_flags'][k] for r in condition_rows) for k in rows[0]['error_flags']}}
  results['conditions'].append(entry)
  if entry['meaningful_degradation'] and results['first_meaningful_degradation'] is None:results['first_meaningful_degradation']=c
  for ki,category in enumerate(CATEGORIES):
   category_tasks=[t for t in tasks if t['category']==category];values=[counts[c][t['id']]/3 for t in category_tasks];d=[(counts['F16'][t['id']]-counts[c][t['id']])/3 for t in category_tasks];di=bootstrap(d,60000+ki*100+ci)
   results['capability_categories'].setdefault(category,[]).append({'condition':c,'successes':sum(counts[c][t['id']] for t in category_tasks),'trials':24,'success_rate':statistics.mean(values),'paired_drop_vs_f16':statistics.mean(d),'paired_drop_ci95':di,'exploratory_degradation':ci>0 and statistics.mean(d)>=.05 and di[0]>0})
 early=[];late=[];reversals=[]
 for task in tasks:
  taskcounts=[counts[c][task['id']] for c in CONDITIONS]
  detail={'task_id':task['id'],'task_name':task['name'],'category':task['category'],'successes_by_condition':dict(zip(CONDITIONS,taskcounts)),'repeats':3}
  if taskcounts[0]>=2 and any(x<=1 for x in taskcounts[1:3]):early.append(detail)
  if taskcounts[0]>=2 and taskcounts[-1]>=2:late.append(detail)
  if any(b>a for a,b in zip(taskcounts,taskcounts[1:])):reversals.append({**detail,'reversals':[{'from':CONDITIONS[i],'to':CONDITIONS[i+1],'increase_in_successes':b-a} for i,(a,b) in enumerate(zip(taskcounts,taskcounts[1:])) if b>a]})
 results.update({'unusually_early_failures':early,'unusually_late_robust_tasks':late,'non_monotonic_tasks':reversals,'non_monotonic_task_count':len(reversals),'reference_floor_categories':[c for c,entries in results['capability_categories'].items() if entries[0]['success_rate']<.5],'reference_success_rate':results['conditions'][0]['success_rate']})
 results['category_first_exploratory_degradation']=[{'category':cat,'first_condition':next((e['condition'] for e in entries if e['exploratory_degradation']),None),'reference_floor':cat in results['reference_floor_categories']} for cat,entries in results['capability_categories'].items()]
 # Post hoc anomaly diagnostic: retain strict outcomes; examine only a JSON object at output start.
 prefix_examples={c:[] for c in CONDITIONS}
 for row in ordered:
  text=row['raw_output'].lstrip()
  if row['success'] or not text.startswith('{'):continue
  try:_,end=json.JSONDecoder().raw_decode(text)
  except ValueError:continue
  prefix=text[:end]
  if score(by_task[row['task_id']],prefix)['success']:
   prefix_examples[row['condition']].append({'id':row['id'],'task_id':row['task_id'],'correct_initial_object':prefix,'strict_primary_error':row['error_category'],'stop_type':row['response'].get('stop_type'),'trailing_text_characters':len(text[end:])})
 results['output_discipline_diagnostic']={'status':'post hoc exploratory; does not change any strict score or primary inference rule','method':'Decode a JSON object only when it begins the response; rerun the frozen scorer on that exact prefix without a stop-budget flag. Do not search inside prose, repair JSON, or count these as official successes.','correct_initial_object_but_strict_failure_counts':{c:len(examples) for c,examples in prefix_examples.items()},'examples':prefix_examples}
 # Evidence callout is the largest observed F16->Q2 loss, among baseline-reliable tasks.
 eligible=[t for t in tasks if counts['F16'][t['id']]>=2]
 callout=max(eligible or tasks,key=lambda t:(counts['F16'][t['id']]-counts['Q2_K'][t['id']],-tasks.index(t)))
 results['hero_task_id']=callout['id'];results['hero_conditions']=['F16',results['first_meaningful_degradation'] if results['first_meaningful_degradation'] not in [None,'Q2_K'] else 'Q4_K_M','Q2_K']
 for e in results['conditions']:
  e['bench_memory_metric']='maximum RSS'
  e['reported_process_footprint_bytes']=perf[e['condition']].get('peak_memory_footprint_bytes')
 vm_activity={}
 for c in CONDITIONS:
  before=perf[c]['system_before']['vm_stat'];after=perf[c]['system_after']['vm_stat']
  page_size=int(re.search(r'page size of (\d+) bytes',before)[1])
  deltas={}
  for key in ['Swapins','Swapouts','Pageins','Pageouts','Compressions','Decompressions']:
   a=re.search(r'^'+key+r':\s+(\d+)',before,re.M);b=re.search(r'^'+key+r':\s+(\d+)',after,re.M)
   if a and b:deltas[key.lower()+'_pages']=int(b[1])-int(a[1])
  vm_activity[c]={'scope':'system-wide counters spanning benchmark, model startup and scored trials; cannot attribute all activity to study process','page_size_bytes':page_size,**deltas,'swapout_bytes':deltas.get('swapouts_pages',0)*page_size,'swapin_bytes':deltas.get('swapins_pages',0)*page_size}
 results['system_vm_activity']=vm_activity
 results['anomalies']={'non_monotonic_tasks':len(reversals),'reference_floor_categories':results['reference_floor_categories'],'budget_exhaustion_by_condition':{e['condition']:e['error_flag_counts']['timeout_loop'] for e in results['conditions']},'thermal_or_swap_warnings':[c for c in CONDITIONS if 'CPU_Speed_Limit' in perf[c].get('system_after',{}).get('thermal','') and 'CPU_Speed_Limit = 100' not in perf[c]['system_after']['thermal']],'memory_accounting':'F16 native peak process footprint was much smaller than RSS despite a 16.39 GB model. Both counters are preserved; infer that footprint does not capture total model occupancy. Comparison uses maximum RSS consistently. Neither counter measures complete system/Metal unified-memory use.'}
 results['anomalies']['conditions_with_system_swapping']=[c for c in CONDITIONS if vm_activity[c]['swapout_bytes']>0 or vm_activity[c]['swapin_bytes']>0]
 results['anomalies']['performance_interpretation']='Observed serial measurements on a running desktop. System swapping and long F16 startup confound isolated quantization speed/memory claims; repeat performance tests in a quiet session before generalizing hardware throughput gains.'
 (ROOT/'results.json').write_text(json.dumps(results,indent=2)+'\n')
 samples=[]
 for c in CONDITIONS:
  failed=[r for r in ordered if r['condition']==c and not r['success']]
  for error in sorted({r['error_category'] for r in failed}):
   r=next(r for r in failed if r['error_category']==error);t=by_task[r['task_id']]
   samples.append({'id':r['id'],'condition':c,'task_id':t['id'],'category':t['category'],'question':t['question'],'expected':t['expected'],'dependencies':t['dependencies'],'actual':r['raw_output'],'parsed':r['parsed_output'],'primary_error':r['error_category'],'flags':r['error_flags'],'stop_type':r['response'].get('stop_type'),'review_status':'pending manual inspection'})
 (ROOT/'manual-failure-review.json').write_text(json.dumps(samples,indent=2)+'\n')
 validation={'status':'data_and_scorers_passed','trial_count':1680,'unique_slots':1680,'deterministic_scorers_rerun':1680,'scorer_mismatches':0,'prompt_or_parameter_mismatches':0,'synthetic_observations':0,'source_revision':manifest['source_revision'],'model_hashes_in_ledger_match':True,'model_hashes_verified_by_runner_before_inference':True,'ledger_sha256':filehash(ROOT/'raw/trials.jsonl'),'normalized_sha256':filehash(ROOT/'normalized.json'),'results_sha256':filehash(ROOT/'results.json'),'manual_failure_review':'pending','artifact_verification':'pending'}
 (ROOT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
 print('RESCORED AND VALIDATED 1680 real observations. First meaningful degradation:',results['first_meaningful_degradation'])
 for e in results['conditions']:print(e['condition'],f'{e["successes"]}/240',f'{e["controlled_generation_tokens_per_second"]:.2f} tok/s')
if __name__=='__main__':main()
