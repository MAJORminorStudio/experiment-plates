#!/usr/bin/env python3
"""Create an allowlisted public directory and tarball; never publish."""
import pathlib,json,shutil,hashlib,tarfile,subprocess
R=pathlib.Path(__file__).resolve().parents[2];S=R/'studies/qwen3-8b-base-20261001';D=R/'releases/plate-001-v1.0.0';A=R/'releases/plate-001-v1.0.0.tar.gz'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run(['python3',str(R/'scripts/publication/validate.py')],check=True)
files=[R/n for n in ['README.md','LICENSE','.gitignore','package.json','package-lock.json','tsconfig.json','releases/visual-0.1.freeze.json','releases/PLATE-v0.1.0.md','releases/Plate-001-v1.0.0.md']]
for folder in ['assets','src','schemas','test','docs','scripts/publication','studies/qwen3-8b-base-20261001']:
 for p in (R/folder).rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(R)
  if any(part in {'node_modules','__pycache__','.venv','weights','models','runtime','.git'} for part in rel.parts):continue
  if p.name.startswith('.') or '.draft.' in p.name or p.name.endswith('.pyc'):continue
  if p.name in {'release-manifest.json','inspector-preview.log','downloaded-normalized.json','inspector-normalized.json'}:continue
  files.append(p)
files=sorted(set(files),key=lambda p:str(p.relative_to(R)))
assert not any(p.relative_to(R).parts[0] in {'examples','outputs'} for p in files)
assert not any('synthetic' in p.name and p.suffix in {'.json','.csv','.svg','.png','.html'} for p in files)
# Staging is rebuilt only inside this task's owned release directory.
if D.exists():shutil.rmtree(D)
D.mkdir(parents=True)
for p in files:
 to=D/p.relative_to(R);to.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,to)
index={str(p.relative_to(R)):sha(p) for p in files}
manifest={'format':'major-minor/public-release@1.0','release':'plate-001-v1.0.0','study':'Plate 001 / Qwen3-8B Base','status':'complete','publication_status':'prepared_unpublished','publication_destination_configured':True,'site_destination':'mm-labs / https://majorminor.xyz/research/plate-001','github_repository_configured':True,'github_repository':'MAJORminorStudio/experiment-plates','scored_trials':1680,'conditions':['F16','Q8_0','Q6_K','Q5_K_M','Q4_K_M','Q3_K_M','Q2_K'],'visualVersion':'0.1','rendererVersion':'0.1.0','benchmark_rerun':False,'plate_002_run':False,'synthetic_artifacts_included':False,'excluded':['models','weights','runtime','.venv','node_modules','examples','outputs','Python caches','earlier working drafts'],'article':'studies/qwen3-8b-base-20261001/publication/index.html','validation':'studies/qwen3-8b-base-20261001/publication/validation-report.json','files':index}
text=json.dumps(manifest,indent=2)+'\n';(S/'release-manifest.json').write_text(text);mp=D/'studies/qwen3-8b-base-20261001/release-manifest.json';mp.write_text(text)
index[str(mp.relative_to(D))]=sha(mp)
(D/'SHA256SUMS').write_text(''.join(f'{h}  {p}\n' for p,h in sorted(index.items())))
with tarfile.open(A,'w:gz',compresslevel=9) as tar:tar.add(D,arcname=D.name,filter=lambda t: None if pathlib.PurePosixPath(t.name).name=='.DS_Store' else t)
# Extract once and verify bytes and article links from the actual archive.
import tempfile,re
from urllib.parse import urlparse,unquote
from html.parser import HTMLParser
class URLs(HTMLParser):
 def __init__(self):super().__init__();self.urls=[]
 def handle_starttag(self,tag,attrs):self.urls += [v for k,v in attrs if k in ['href','src']]
with tempfile.TemporaryDirectory(prefix='plate-release-verify-') as temp:
 with tarfile.open(A,'r:gz') as tar:tar.extractall(temp,filter='data')
 root=pathlib.Path(temp)/D.name
 for p,h in index.items():assert sha(root/p)==h,p
 page=root/manifest['article'];parser=URLs();parser.feed(page.read_text())
 for u in parser.urls:
  link=urlparse(u)
  if not link.scheme and link.path:assert (page.parent/unquote(link.path)).resolve().is_file(),u
 archived_files=[p for p in root.rglob('*') if p.is_file()]
 assert len(archived_files)==len(index)+1
archive_sha=sha(A);(A.with_suffix(A.suffix+'.sha256')).write_text(f'{archive_sha}  {A.name}\n')
report={'status':'passed','archive':str(A.relative_to(R)),'archive_sha256':archive_sha,'bytes':A.stat().st_size,'files':len(index)+1,'extracted_files_verified':len(index),'archive_article_links':'passed','synthetic_artifacts':0,'publication_status':'prepared_unpublished'}
(R/'releases/plate-001-v1.0.0.package-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
