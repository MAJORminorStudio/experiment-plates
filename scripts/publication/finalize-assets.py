#!/usr/bin/env python3
"""Prepare site-only and renderer release bundles; no deployment or publishing."""
import pathlib,json,hashlib,tarfile,shutil,tempfile,sys
R=pathlib.Path(__file__).resolve().parents[2];P=R/'studies/qwen3-8b-base-20261001/publication';O=R/'releases'
platform=pathlib.Path(sys.argv[1]).resolve() if len(sys.argv)>1 else R.parents[1]/'major-minor-sites'
# Platform location is used only for local assembly, never embedded in public route source.
manifest=json.loads((P/'site-integration/manifest.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
notes=(P/'release-notes.md').read_text();cut=notes.index('# PLATE / Experiment Plates')
(O/'Plate-001-v1.0.0.md').write_text(notes[:cut].strip()+'\n\nFinal launch: 1600×1600 PNG/SVG with a 20% optical-weight increase, model/trial/hardware label and stronger oxide COLLAPSE treatment. Integrated into the existing mm-labs research index and sitemap at `/research/plate-001`. Production-relative links, images, inspector, gzip downloads and 360/390/768 layouts passed. No benchmark rerun or Plate 002 execution.\n')
(O/'PLATE-v0.1.0.md').write_text(notes[cut:].strip()+'\n\nThe canonical renderer, fonts, schema, lockfiles and stroke grammar remain byte-identical to the visual-0.1 freeze manifest. Publication-only optical adjustments are confined to the separate social adaptation.\n')
archive=O/'plate-001-site-integration.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=9) as tar:
 for rel,expected in sorted(manifest['new_files'].items()):
  path=platform/rel;assert sha(path)==expected,rel;tar.add(path,arcname=rel)
 tar.add(P/'site-integration/existing-files.patch',arcname='plate-001-existing-files.patch')
 tar.add(P/'site-integration/manifest.json',arcname='plate-001-site-manifest.json')
(archive.with_suffix(archive.suffix+'.sha256')).write_text(sha(archive)+'  '+archive.name+'\n')
# Verify actual extracted overlay hashes, rather than only the staging tree.
with tempfile.TemporaryDirectory(prefix='plate-site-overlay-') as temp:
 with tarfile.open(archive) as tar:tar.extractall(temp,filter='data')
 for rel,expected in manifest['new_files'].items():assert sha(pathlib.Path(temp)/rel)==expected,rel
 # Validate the Plate 001-only additions against copies with just those additions removed.
 for rel in manifest.get('existing_files',['sites/mm-labs/app/research/page.tsx','sites/mm-labs/app/sitemap.ts']):
  text=(platform/rel).read_text();before=text.replace('"prebuild": "node scripts/prepare-plate-001-assets.mjs", ','') if rel.endswith('/package.json') else '\n'.join(line for line in text.split('\n') if '/research/plate-001' not in line)
  path=pathlib.Path(temp)/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(before)
 import subprocess
 subprocess.run(['git','apply','--check',str(P/'site-integration/existing-files.patch')],cwd=temp,check=True)
 subprocess.run(['git','apply',str(P/'site-integration/existing-files.patch')],cwd=temp,check=True)
 for rel in manifest.get('existing_files',['sites/mm-labs/app/research/page.tsx','sites/mm-labs/app/sitemap.ts']):assert (pathlib.Path(temp)/rel).read_bytes()==(platform/rel).read_bytes()
# Code-only PLATE archive. No synthetic observations or image artifacts are distributed.
D=O/'plate-v0.1.0'
if D.exists():shutil.rmtree(D)
D.mkdir()
files=[R/n for n in ['LICENSE','package.json','package-lock.json','tsconfig.json','releases/visual-0.1.freeze.json']]
for folder in ['src','schemas','assets/fonts','test']:
 files.extend(p for p in (R/folder).rglob('*') if p.is_file() and p.name!='.DS_Store')
for source in files:
 dest=D/source.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
(D/'README.md').write_text('''# PLATE / Experiment Plates — visual 0.1

Every mark is a measurement. Fixed task addresses, shared scales, trial-derived geometry, embedded provenance and deterministic rendering connect experiment plates to observations.

This archive contains the frozen TypeScript renderer, schemas, font assets/notices, source tests, lockfiles and source-hash freeze. It contains no pre-generated synthetic data or study artifacts. Plate 001 is a separate companion release with 1,680 real Qwen3-8B Base trials and an evidence inspector. Code: MIT. Fonts: SIL OFL 1.1. See LICENSE and font notices.

Build the renderer:

```sh
npm ci
npm run build
```

To run the original renderer tests, generate their explicitly synthetic development fixtures locally first:

```sh
npm run example
npm test
```

Those fixtures are test inputs only and are never included in Plate 001 or its release assets. For real-data reproduction, use the full Plate 001 repository snapshot and its study/export verifier. The visual-0.1 freeze file records the exact renderer, schema, font and root dependency hashes. Tables and conventional plots accompany PLATE when exact values or uncertainty matter.
''')
index={str(p.relative_to(D)):sha(p) for p in D.rglob('*') if p.is_file()};(D/'SHA256SUMS').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(index.items())))
A=O/'plate-v0.1.0.tar.gz'
with tarfile.open(A,'w:gz',compresslevel=9) as tar:tar.add(D,arcname=D.name)
(A.with_suffix(A.suffix+'.sha256')).write_text(sha(A)+'  '+A.name+'\n')
report={'status':'passed','site_overlay':{'archive':archive.name,'sha256':sha(archive),'files':len(manifest['new_files']),'extracted_hashes':'passed','existing_files_patch':'passed; reconstructs only the Plate 001 additions'},'plate_visual_0_1':{'archive':A.name,'sha256':sha(A),'files':len(index)+1,'synthetic_observations':0},'production_article_url':manifest['production_article_url'],'largest_site_asset_bytes':manifest['largest_asset_bytes'],'cloudflare_25_mib_asset_limit':'passed','published':False}
(O/'finalization-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
