#!/usr/bin/env python3
"""Verify original blobs, convert a common F16 reference, derive and hash each quant."""
import hashlib,json,pathlib,subprocess,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
REVISION='49e3418fbbbca6ecbdf9608b4d22e5a407081db4'
LLAMA_REVISION='b29c606e28a01b1bc8c1351026a0fa6e616bf6c4'
CONDITIONS=['F16','Q8_0','Q6_K','Q5_K_M','Q4_K_M','Q3_K_M','Q2_K']
def filehash(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 manifest={'model':'Qwen/Qwen3-8B-Base','source_revision':REVISION,'llama_revision':LLAMA_REVISION,'source_files':{},'conditions':{},'commands':[]}
 metadata=json.loads((ROOT/'raw/source-model-api.json').read_text())
 assert metadata['sha']==REVISION
 for info in metadata['siblings']:
  path=ROOT/'weights'/info['rfilename']
  if not path.exists():raise FileNotFoundError(path)
  actual=filehash(path)
  if info.get('lfs'):assert actual==info['lfs']['sha256'],('source hash mismatch',path)
  manifest['source_files'][info['rfilename']]={'sha256':actual,'bytes':path.stat().st_size}
 print('All original model files hashed; five safetensors blobs match upstream.',flush=True)
 reference=ROOT/'models/Qwen3-8B-Base-F16.gguf'
 convert=[str(ROOT/'.venv/bin/python'),str(ROOT/'runtime/llama.cpp/convert_hf_to_gguf.py'),str(ROOT/'weights'),'--outfile',str(reference),'--outtype','f16']
 manifest['commands'].append(convert)
 if not reference.exists():
  with open(ROOT/'raw/conversion.log','w') as log:subprocess.run(convert,stdout=log,stderr=subprocess.STDOUT,check=True)
 manifest['conditions']['F16']={'path':str(reference),'bytes':reference.stat().st_size,'sha256':filehash(reference),'command':convert,'source_type':'BF16 safetensors converted to common F16 GGUF'}
 (ROOT/'model-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('F16 reference ready',manifest['conditions']['F16']['bytes'],flush=True)
 for condition in CONDITIONS[1:]:
  path=ROOT/f'models/Qwen3-8B-Base-{condition}.gguf'
  command=['/opt/homebrew/bin/llama-quantize',str(reference),str(path),condition,'8']
  manifest['commands'].append(command);started=time.monotonic()
  if not path.exists():
   with open(ROOT/f'raw/quantize-{condition}.log','w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
  manifest['conditions'][condition]={'path':str(path),'bytes':path.stat().st_size,'sha256':filehash(path),'command':command,'reference_sha256':manifest['conditions']['F16']['sha256'],'imatrix':None,'preparation_wall_seconds':time.monotonic()-started}
  (ROOT/'model-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(condition,'ready',path.stat().st_size,flush=True)
 (ROOT/'quantization-commands.json').write_text(json.dumps({'source_model':manifest['model'],'source_revision':REVISION,'llama_revision':LLAMA_REVISION,'commands':manifest['commands']},indent=2)+'\n')
 subprocess.run([str(ROOT/'.venv/bin/pip'),'freeze'],stdout=open(ROOT/'python-requirements.lock.txt','w'),check=True)
if __name__=='__main__':main()
