#!/usr/bin/env python3
"""80 fixed agent-relevant reasoning tasks; expected answers and evaluators are deterministic."""
import hashlib, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
CATEGORIES = ['structured_output','tool_selection','tool_arguments','planning','state_tracking','context_retention','recovery','constraints','completion','code_file_reasoning']
ERRORS = ['malformed_structured_output','wrong_tool','wrong_arguments','incomplete_plan','state_loss','failure_to_recover','premature_completion','constraint_violation','reasoning','timeout_loop','other']
TOOLS = {
 'read_file': {'path':'string'}, 'write_file': {'path':'string','content':'string'},
 'list_dir': {'path':'string'}, 'search_files': {'root':'string','query':'string'},
 'run_tests': {'target':'string'}, 'http_get': {'url':'string'},
 'notify': {'channel':'string','message':'string'}, 'copy_file': {'source':'string','destination':'string'},
}
SYSTEM = 'Solve the agent reasoning task using only the supplied facts. Return exactly one compact JSON object, with the requested keys and no commentary or markdown. Do not execute tools. Tool calls are proposals. Strings, booleans, numbers and lists must have their correct JSON types. Never invent missing evidence.'
EXAMPLES = '''### Example:
Task: A counter starts at 3, increases by 2, then decreases by 1. Return {"count": integer}.
Answer: {"count":4}
### Example:
Task: Propose reading /tmp/a.txt. Return {"tool": string, "arguments": object}.
Answer: {"tool":"read_file","arguments":{"path":"/tmp/a.txt"}}
### Example:
Task: Required outputs a.txt and b.txt. Only a.txt has a successful write receipt. Return {"complete": boolean, "missing": list of names}.
Answer: {"complete":false,"missing":["b.txt"]}'''

def canonical(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def sha(v): return hashlib.sha256(v.encode()).hexdigest()
def build_suite():
 tasks=[]
 def add(category,index,label,question,expected,dependencies=None):
  number=len(tasks)+1
  prompt=f'{SYSTEM}\nTools: {canonical(TOOLS)}\n{EXAMPLES}\n### Task:\n{question}\n### Answer:\n'
  tasks.append({'id':f'task-{number:03}', 'name':f'{number:03} {label}', 'category':category, 'variant':index+1,'question':question,'prompt':prompt,'prompt_sha256':sha(prompt),'expected':expected,'dependencies':dependencies or [],'scorer_version':'1.0.0'})
 for i in range(8):
  tag=['urgent','normal','urgent','low','normal','urgent','low','normal'][i]
  code=410+i; owner=['Mina','Tariq','Jo','Anya','Luis','Nia','Pia','Ren'][i]
  question=f'Ticket {code} belongs to {owner}. Its written priority is {tag}. There are {i+2} attempts. Labels, in the given order, are ops and agent. Convert priority urgent->3, normal->2, low->1. Return exactly {{"ticket": integer,"owner": string,"priority": integer,"attempts": integer,"labels": list of strings}}.'
  add('structured_output',i,'JSON ticket',question,{'ticket':code,'owner':owner,'priority':{'urgent':3,'normal':2,'low':1}[tag],'attempts':i+2,'labels':['ops','agent']})
 choices=[('read_file',{'path':'/workspace/report.md'},'Read the contents of /workspace/report.md.'),('list_dir',{'path':'/workspace/src'},'List immediate entries of /workspace/src without reading their contents.'),('search_files',{'root':'/workspace/logs','query':'ERROR'},'Search recursively under /workspace/logs for the literal text ERROR.'),('write_file',{'path':'/workspace/flag.txt','content':'ready'},'Overwrite /workspace/flag.txt with exactly ready.'),('run_tests',{'target':'unit'},'Run only the unit test target.'),('http_get',{'url':'https://example.test/status'},'Retrieve https://example.test/status.'),('notify',{'channel':'ops','message':'build passed'},'Send the proposed message build passed to the ops channel.'),('copy_file',{'source':'/workspace/a.txt','destination':'/workspace/b.txt'},'Copy /workspace/a.txt to /workspace/b.txt, preserving the source.')]
 for i,(tool,args,intent) in enumerate(choices): add('tool_selection',i,'Choose tool',intent+' Choose the single best tool. Return {"tool": string,"arguments": object}.',{'tool':tool,'arguments':args})
 for i in range(8):
  root=f'/workspace/job-{i+1}'; filename=f'result {i+1}.json'; content=canonical({'ready':True,'count':i+1})
  question=f'Use write_file. Join directory {root} and filename {filename} with exactly one slash. Overwrite that file with the following literal content, including its quotes: {content}. Return {{"tool":string,"arguments":{{"path":string,"content":string}}}}. Do not turn content into an object.'
  add('tool_arguments',i,'Build arguments',question,{'tool':'write_file','arguments':{'path':root+'/'+filename,'content':content}})
 for i in range(8):
  steps=['read_config','validate_config','write_change','run_tests','report_result'] if i%2==0 else ['read_source','read_target','compute_diff','apply_patch','verify_target','report_result']
  deps=list(zip(steps[:-1],steps[1:])) if i%2==0 else [('read_source','compute_diff'),('read_target','compute_diff'),('compute_diff','apply_patch'),('apply_patch','verify_target'),('verify_target','report_result')]
  shuffled=steps[i%len(steps):]+steps[:i%len(steps)]
  question=f'Construct a complete plan for job {i+1}. Required steps (unordered): {canonical(shuffled)}. Constraints: '+ '; '.join(f'{a} before {b}' for a,b in deps)+'. Every step must appear exactly once. Return {"steps": list of step names}. Any valid topological order is accepted.'
  add('planning',i,'Dependency plan',question,{'steps':steps},deps)
 for i in range(8):
  count=10+i; final=count+4-3+2-i%3
  question=f'State initially: count={count}, location="staging", active=false. Apply events in order: add 4; move to "processing"; set active true; subtract 3; add 2; subtract {i%3}; move to "archive"; set active false. Return final {{"count":integer,"location":string,"active":boolean}}.'
  add('state_tracking',i,'Track state',question,{'count':final,'location':'archive','active':False})
 for i in range(8):
  notes=[f'Unrelated note {j}: worker-{j} keeps bucket {(j*7+i)%13} and policy tag p{j%5}.' for j in range(1,19+i*2)]
  inserts=[(2,f'Target ALPHA endpoint is https://alpha{i}.example.test/v1.'),(10,f'Target ALPHA file suffix is .agent{i}.'),(len(notes)-2,f'Correction: replace only ALPHA endpoint with https://alpha{i}.example.test/v2. All other ALPHA fields remain unchanged.')]
  for ix,note in reversed(inserts):notes.insert(ix,note)
  question='Read this ordered notebook; unrelated workers cannot override ALPHA.\n'+'\n'.join(notes)+'\nReturn ALPHA final {"endpoint":string,"suffix":string}.'
  add('context_retention',i,'Retain context',question,{'endpoint':f'https://alpha{i}.example.test/v2','suffix':f'.agent{i}'})
 for i in range(8):
  path=f'/workspace/input-{i+1}.json'
  if i%2==0:
   question=f'Read of {path} failed with TEMPORARY_UNAVAILABLE. Policy allows one retry of the same read, then escalation. No retry has happened yet. A mirror exists but policy forbids using it. Propose the next action as {{"tool":string,"arguments":object}}.'
   expected={'tool':'read_file','arguments':{'path':path}}
  else:
   question=f'Read of {path} failed with NOT_FOUND. Policy forbids retrying a missing path. A verified backup exists at /workspace/backups/input-{i+1}.json. Read the backup; never claim the job is done. Propose the next action as {{"tool":string,"arguments":object}}.'
   expected={'tool':'read_file','arguments':{'path':f'/workspace/backups/input-{i+1}.json'}}
  add('recovery',i,'Recover read',question,expected)
 for i in range(8):
  candidates=[{'id':f'a{i}','cost':2,'safe':True},{'id':f'b{i}','cost':7,'safe':True},{'id':f'c{i}','cost':1,'safe':False},{'id':f'd{i}','cost':3,'safe':True},{'id':f'e{i}','cost':4,'safe':True}]
  limit=3+i%3; maxitems=2+i%2
  allowed=sorted([x['id'] for x in candidates if x['safe'] and x['cost']<=limit])[:maxitems]
  question=f'Candidate actions: {canonical(candidates)}. Keep only safe=true and cost <= {limit}. Sort retained IDs alphabetically, then take at most {maxitems}. Do not use unsafe actions even if cheap. Return exactly {{"ids":list of strings}}.'
  add('constraints',i,'Filter actions',question,{'ids':allowed})
 for i in range(8):
  required=[f'job{i}/report.txt',f'job{i}/summary.json',f'job{i}/receipt.log']
  completed=required if i in [0,3,6] else required[:1+(i%2)]
  receipts=[{'path':p,'status':'success' if p in completed else 'failed'} for p in required]
  question=f'Job requires successful write receipts for every file in {canonical(required)}. Observed receipts: {canonical(receipts)}. A proposed plan is not completion evidence. Return {{"complete":boolean,"missing":list of paths in required order}}.'
  missing=[p for p in required if p not in completed]
  add('completion',i,'Judge completion',question,{'complete':not missing,'missing':missing})
 for i in range(8):
  original=f'line-{i+1}'; suffix=f'|done-{i+1}'
  question=f'In a simulated filesystem, /work/a.txt initially contains exactly {original}, /work/b.txt is absent. Apply: copy a.txt to b.txt; append exactly {suffix} to b.txt; rename b.txt to result.txt; overwrite a.txt with exactly reset. No operation adds a newline. Return final {{"files":object mapping absolute paths to string contents}}. Absent paths must not appear.'
  add('code_file_reasoning',i,'Reason files',question,{'files':{'/work/a.txt':'reset','/work/result.txt':original+suffix}})
 assert len(tasks)==80
 return {'format':'major-minor/agent-microbench@1.0','task_count':80,'tasks_per_category':8,'categories':CATEGORIES,'system_prompt':SYSTEM,'tool_definitions':TOOLS,'few_shot_examples':EXAMPLES,'prompt_format':'raw completion; no chat template, grammar, or JSON constraint','tasks':tasks}

def parse_json(text):
 def pairs(items):
  out={}
  for key,value in items:
   if key in out: raise ValueError('duplicate JSON key: '+key)
   out[key]=value
  return out
 return json.loads(text.strip(),object_pairs_hook=pairs,parse_constant=lambda s: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
def same_shape(actual,expected):
 if type(actual) is not type(expected):return False
 if isinstance(expected,dict):return set(actual)==set(expected) and all(same_shape(actual[k],expected[k]) for k in expected)
 if isinstance(expected,list):return all(same_shape(v,expected[0]) for v in actual) if expected else isinstance(actual,list)
 return True
def score(task,text,stop_reason=None,transport_error=None):
 flags={key:False for key in ERRORS}; parsed=None; diagnostics=[]
 if transport_error:
  flags['timeout_loop' if transport_error=='timeout' else 'other']=True;diagnostics.append('transport:'+transport_error)
 else:
  try:
   parsed=parse_json(text)
   if not isinstance(parsed,dict):raise ValueError('top level must be object')
  except (ValueError,TypeError) as e:flags['malformed_structured_output']=True;diagnostics.append(str(e))
  if parsed is not None and not flags['malformed_structured_output']:
   cat=task['category'];expected=task['expected']
   if cat=='planning':
    steps=parsed.get('steps')
    valid=isinstance(steps,list) and all(isinstance(s,str) for s in steps) and len(steps)==len(expected['steps']) and set(steps)==set(expected['steps']) and len(set(steps))==len(steps) and set(parsed)=={'steps'}
    if valid:valid=all(steps.index(a)<steps.index(b) for a,b in task['dependencies'])
    if not valid:flags['incomplete_plan']=True;diagnostics.append('required step set/order differs')
   elif cat in ['tool_selection','tool_arguments','recovery']:
    if parsed.get('tool')!=expected['tool']:flags['wrong_tool']=True
    if canonical(parsed.get('arguments'))!=canonical(expected['arguments']) or set(parsed)!=set(expected):flags['wrong_arguments']=True
    if cat=='recovery' and any(flags.values()):flags['failure_to_recover']=True
   elif canonical(parsed)!=canonical(expected):
    error={'structured_output':'malformed_structured_output','state_tracking':'state_loss','context_retention':'state_loss','constraints':'constraint_violation','completion':'other','code_file_reasoning':'reasoning'}[cat]
    if cat=='structured_output' and same_shape(parsed,expected):error='other'
    flags[error]=True
    if cat=='completion' and parsed.get('complete') is True and expected['complete'] is False:flags['premature_completion']=True
    diagnostics.append('answer does not match deterministic oracle')
  if stop_reason=='limit' or stop_reason=='length':flags['timeout_loop']=True;diagnostics.append('generation budget exhausted')
 primary=next((k for k in ['timeout_loop','malformed_structured_output','premature_completion','failure_to_recover','wrong_tool','wrong_arguments','incomplete_plan','state_loss','constraint_violation','reasoning','other'] if flags[k]),None)
 return {'success':not any(flags.values()),'error_category':primary,'error_flags':flags,'parsed_output':parsed,'diagnostics':diagnostics,'scorer_version':'1.0.0'}

if __name__=='__main__':
 suite=build_suite()
 for task in suite['tasks']:assert score(task,canonical(task['expected']))['success'],task['id']
 assert not score(suite['tasks'][0],'```json\n{}\n```')['success']
 assert not score(suite['tasks'][0],'{"ticket":1,"ticket":2}')['success']
 text=json.dumps(suite,indent=2,ensure_ascii=False)+'\n';(ROOT/'task-suite.json').write_text(text)
 definitions={'version':'1.0.0','llm_evaluator':None,'strict_json':True,'rules':'Complete output must be exactly one JSON object; duplicate keys, nonfinite values, markdown, extra prose and wrong primitive types fail. Exact object equality except plans: complete unique step set plus dependency partial order. Tool name and arguments scored separately. Budget exhaustion always fails.','error_priority':['timeout_loop','malformed_structured_output','premature_completion','failure_to_recover','wrong_tool','wrong_arguments','incomplete_plan','state_loss','constraint_violation','reasoning','other'],'category_rules':{c:('partial-order plan oracle' if c=='planning' else 'tool+argument oracle' if c in ['tool_selection','tool_arguments','recovery'] else 'strict exact JSON oracle') for c in CATEGORIES},'suite_sha256':sha(text),'prompt_max_characters':max(len(t['prompt']) for t in suite['tasks'])}
 (ROOT/'scoring-definitions.json').write_text(json.dumps(definitions,indent=2)+'\n')
 print('Wrote 80 tasks; all oracle-positive scorer checks passed. Max prompt chars',definitions['prompt_max_characters'])
