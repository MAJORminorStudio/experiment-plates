#!/usr/bin/env python3
"""Independent scorer boundary checks; never generate or alter observed trials."""
import json,pathlib,unittest
from suite import score,canonical
ROOT=pathlib.Path(__file__).resolve().parents[1]
TASKS=json.loads((ROOT/'task-suite.json').read_text())['tasks']
class ScorerChecks(unittest.TestCase):
 def test_all_oracles(self):
  for task in TASKS:
   with self.subTest(task=task['id']):self.assertTrue(score(task,canonical(task['expected']))['success'])
 def test_strict_json(self):
  t=TASKS[0]
  for bad in ['```json\n{}\n```','{} trailing','{"ticket":1,"ticket":2}','{"ticket":NaN}','[]']:
   with self.subTest(output=bad):self.assertTrue(score(t,bad)['error_flags']['malformed_structured_output'])
 def test_primitive_types_and_wrong_values(self):
  t=TASKS[0];answer=dict(t['expected']);answer['attempts']=str(answer['attempts'])
  self.assertTrue(score(t,canonical(answer))['error_flags']['malformed_structured_output'])
  answer=dict(t['expected']);answer['attempts']+=1
  self.assertTrue(score(t,canonical(answer))['error_flags']['other'])
 def test_topological_order(self):
  t=TASKS[25];a=list(t['expected']['steps']);a[0],a[1]=a[1],a[0]
  self.assertTrue(score(t,canonical({'steps':a}))['success'])
  a[2],a[3]=a[3],a[2]
  self.assertTrue(score(t,canonical({'steps':a}))['error_flags']['incomplete_plan'])
  self.assertFalse(score(t,canonical({'steps':t['expected']['steps'][:-1]}))['success'])
 def test_tools_and_recovery(self):
  t=TASKS[48];a={'tool':'notify','arguments':t['expected']['arguments']}
  r=score(t,canonical(a));self.assertTrue(r['error_flags']['wrong_tool']);self.assertTrue(r['error_flags']['failure_to_recover'])
  t=TASKS[16];a={'tool':t['expected']['tool'],'arguments':{'path':t['expected']['arguments']['path'],'content':{'count':1,'ready':True}}}
  self.assertTrue(score(t,canonical(a))['error_flags']['wrong_arguments'])
 def test_premature_completion(self):
  t=TASKS[65];r=score(t,'{"complete":true,"missing":[]}')
  self.assertEqual(r['error_category'],'premature_completion')
 def test_state_constraints_files(self):
  for i,flag in [(32,'state_loss'),(40,'state_loss'),(56,'constraint_violation'),(72,'reasoning')]:
   with self.subTest(task=TASKS[i]['id']):self.assertTrue(score(TASKS[i],'{}')['error_flags'][flag])
 def test_budget_exhaustion(self):
  r=score(TASKS[0],canonical(TASKS[0]['expected']),'limit')
  self.assertFalse(r['success']);self.assertEqual(r['error_category'],'timeout_loop')
if __name__=='__main__':unittest.main()
