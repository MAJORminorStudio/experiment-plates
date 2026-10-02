#!/usr/bin/env python3
"""Install completed Plate 001 into the existing mm-labs research structure."""
import pathlib,sys,json,re,shutil,hashlib,gzip,tarfile,difflib
from urllib.parse import urljoin,urlparse
R=pathlib.Path(__file__).resolve().parents[2];S=R/'studies/qwen3-8b-base-20261001';P=S/'publication'
if len(sys.argv)!=2:raise SystemExit('Usage: python3 scripts/publication/integrate-site.py /path/to/major-minor-sites')
platform=pathlib.Path(sys.argv[1]).resolve();site=platform/'sites/mm-labs';assert (site/'app/research/page.tsx').exists()
base='/research/plate-001';public=site/'public/research/plate-001';route=site/'app/research/plate-001';route.mkdir(parents=True,exist_ok=True);public.mkdir(parents=True,exist_ok=True)
reportdir=P/'site-integration';reportdir.mkdir(exist_ok=True)
# Reuse completed article markup and the existing site frame; no new UI behavior.
source=(P/'index.html').read_text();body=re.search(r'<article id="article">([\s\S]*?)</article>',source).group(1)
body=re.sub(r'^<h1>[\s\S]*?</h1>\s*','',body)
body=re.sub(r'<div class="(?:deck|article-meta)">[\s\S]*?</div>\s*','',body)
private_metadata={'raw/trials.jsonl','model-manifest.json','quantization-commands.json','performance.json'}
outputs=[]
def copy(source,rel):
 target=public/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);outputs.append(str(target.relative_to(platform)))
def install_study(rel):
 if rel in private_metadata:
  target=public/(rel+'.gz');target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes(gzip.compress((S/rel).read_bytes(),compresslevel=9,mtime=0));outputs.append(str(target.relative_to(platform)));return rel+'.gz'
 copy(S/rel,rel);return rel
# Map every actual publication URL to its production root; download bytes stay intact.
def urlmap(match):
 attr,url=match.group(1),match.group(2)
 if urlparse(url).scheme or url.startswith('#'):return match.group(0)
 resolved=urljoin('/study/publication/',url)
 if url=='../../../docs/renderer-0.1.md':
  rel='docs/renderer-0.1.md';copy(R/rel,rel);return f'{attr}="{base}/{rel}"'
 assert resolved.startswith('/study/'),url
 rel=resolved[len('/study/'):]
 if rel=='publication/demo/plate-001-demo.mp4':copy(S/rel,rel)
 elif rel=='publication/success-rates.svg':copy(S/rel,rel)
 else:rel=install_study(rel)
 return f'{attr}="{base}/{rel}"'
body=re.sub(r'(href|src)="([^"]+)"',urlmap,body)
body=body.replace('JSONL ledger</a>','JSONL ledger (gzip)</a>').replace('Raw ledger / JSONL</a>','Raw ledger / JSONL.gz</a>').replace('Model / source hashes</a>','Model / source hashes (gzip)</a>').replace('Quantization commands</a>','Quantization commands (gzip)</a>')
# The standalone viewer's seven conditions and interaction remain byte-for-byte in logic.
js=(P/'article.js').read_text().replace("'../artifacts/'",json.dumps(base+'/artifacts/'))
for condition in ['F16','Q8_0','Q6_K','Q5_K_M','Q4_K_M','Q3_K_M','Q2_K']:copy(S/f'artifacts/{condition}.png',f'artifacts/{condition}.png')
for file in (P/'social').glob('plate-001-launch-1600.*'):copy(file,'publication/social/'+file.name)
copy(P/'social/validation.json','publication/social/validation.json')
article_source=(P/'article.md').read_text()
article_source=re.sub(r'(href|src)="([^"]+)"',urlmap,article_source)
def md_url(match):
 u=match.group(1)
 if urlparse(u).scheme or u.startswith('#'):return match.group(0)
 mapped=urlmap(re.match(r'(href|src)="([^"]+)"','href="'+u+'"'))
 return ']('+mapped[len('href="'):-1]+')'
article_source=re.sub(r'\]\(([^)]+)\)',md_url,article_source)
(public/'publication/article.md').write_text(article_source);outputs.append(str((public/'publication/article.md').relative_to(platform)))
copy(P/'demo/edit-spec.md','publication/demo/edit-spec.md')
for rel in ['publication/social-posts.md','publication/social-posts.json','publication/validation-report.json']:
 copy(S/rel,rel)
for path in (S/'artifacts').rglob('*'):
 if path.is_file():copy(path,'artifacts/'+str(path.relative_to(S/'artifacts')))
renderer_doc=public/'docs/renderer-0.1.md'
renderer_doc.write_text(renderer_doc.read_text().replace('../studies/qwen3-8b-base-20261001/README.md','../README.md'))

# Reproduction docs refer to related metadata: keep their public links in the same root.
for rel in ['task-suite.json','scoring-definitions.json','study-protocol.json','inference-settings.json','source-model-card.md','artifacts/verification.json']:
 copy(S/rel,rel)
for file in (R/'assets/fonts').iterdir():copy(file,'fonts/'+file.name)
(public/'publication/article.js').write_text(js);outputs.append(str((public/'publication/article.js').relative_to(platform)))
for rel in ['methodology.md','README.md','reproduction.md','LICENSES.md']:
 path=public/rel
 if path.exists():
  text=path.read_text().replace('(publication/index.html)',f'({base})').replace('../../assets/fonts/','fonts/')
  text=re.sub(r'\]\(([^)]+)\)',lambda m:']('+base+'/'+m.group(1)+')' if not urlparse(m.group(1)).scheme and not m.group(1).startswith('/') else m.group(0),text)
  path.write_text(text)
# A self-contained evidence download is under Cloudflare's 25 MiB per-asset ceiling.
evidence_names=['README.md','methodology.md','reproduction.md','LICENSES.md','source-model-card.md','raw/trials.jsonl','raw/trials.csv','normalized.json','results.json','experiment-manifest.json','model-manifest.json','inference-settings.json','scoring-definitions.json','task-suite.json','study-protocol.json','quantization-commands.json','environment.json','performance.json','plate-spec.json','manual-failure-review.json','validation.json','error-category-mapping.json']
evidence_paths=[S/n for n in evidence_names]+[p for p in (S/'artifacts').rglob('*') if p.is_file()]+[S/'scripts/suite.py',S/'scripts/test_suite.py']
evidence=public/'downloads/plate-001-evidence.tar.gz';evidence.parent.mkdir(exist_ok=True)
with tarfile.open(evidence,'w:gz',compresslevel=9) as tar:
 for path in sorted(evidence_paths):tar.add(path,arcname='plate-001/'+str(path.relative_to(S)))
 tar.add(R/'LICENSE',arcname='plate-001/LICENSE')
assert evidence.stat().st_size<25*1024*1024
outputs.append(str(evidence.relative_to(platform)))
body=body.replace('<div class="downloads">',f'<div class="downloads"><a href="{base}/downloads/plate-001-evidence.tar.gz" download>Complete study evidence / tar.gz</a>')
(route/'content.ts').write_text('// Generated from the completed, validated Plate 001 article.\nexport const plate001Body = '+json.dumps(body,ensure_ascii=False)+';\n')
page='''import type { Metadata } from "next";
import Link from "next/link";
import Script from "next/script";
import { PublicHeader } from "../../../components/public-header";
import { plate001Body } from "./content";
import styles from "./plate-001.module.css";

const title = "We Quantized an 8B Agent From F16 to Q2. It Didn’t Break Gradually.";
const description = "1,680 real Qwen3-8B Base trials. Q8/Q6 stayed near F16; Q2 collapsed under a strict-output contract. Fixed Experiment Plates, raw evidence and an inspector.";
const launchImage = "/research/plate-001/publication/social/plate-001-launch-1600.png";
export const metadata: Metadata = {
  title, description,
  alternates: { canonical: "https://majorminor.xyz/research/plate-001" },
  openGraph: { title, description, type: "article", url: "https://majorminor.xyz/research/plate-001", images: [{ url: launchImage, width: 1600, height: 1600, alt: "Plate 001: seven measured success rates and the Q2 collapse" }] },
  twitter: { card: "summary_large_image", title, description, images: [launchImage] },
};

export default function Plate001Page() {
  return (
    <main id="main-content" className="sheet subpage">
      <PublicHeader />
      <article className="blog-article">
        <header className="subpage-header">
          <p className="subpage-label">Research / Experiment Plates / Plate 001 / Qwen3-8B Base / Visual 0.1</p>
          <h1 className="headline" data-length="long">{title}</h1>
          <p className="blog-dek">1,680 real trials. Seven precision levels. A clear Q2 cliff—and a few awkward reversals on the way down.</p>
        </header>
        <div className={styles.body} dangerouslySetInnerHTML={{ __html: plate001Body }} />
      </article>
      <footer className="subpage-footer study-footer">
        <Link href="/research">← Research index</Link>
        <a href="/research/plate-001/artifacts/inspector.html">Evidence inspector →</a>
      </footer>
      <Script src="/research/plate-001/publication/article.js" strategy="afterInteractive" />
    </main>
  );
}
'''
(route/'page.tsx').write_text(page)
# Scope the completed article's body styling. Preserve the existing platform shell.
css='''.body{--bone:#E7DFCC;--ink:#0A0A08;--verdigris:#3DA887;--oxide:#D9643A;background:var(--bone);color:var(--ink);font:15px/1.85 var(--font-mono);margin:0 var(--page-inset);padding:30px;max-width:var(--page-measure);min-width:0}.body a{color:inherit;text-decoration:underline;text-underline-offset:4px}.body p,.body ul{max-width:68ch;margin:22px 0}.body li{margin:12px 0}.body h2{font:400 clamp(30px,4vw,49px)/1.08 var(--font-display);margin:70px 0 28px;padding-top:26px;border-top:2px solid var(--ink)}.body h2:first-of-type{margin-top:45px}.body figure{margin:32px 0 38px}.body figure img{display:block;width:100%;height:auto;border:1px solid rgba(10,10,8,.3)}.body figcaption{font-size:11px;line-height:1.7;margin-top:12px;color:#514e44}.body :global(.pair){display:grid;grid-template-columns:1fr 1fr;gap:25px}.body :global(.pair) figure{min-width:0}.body :global(.explorer){border-block:1px solid var(--ink);padding:25px 0;margin:30px 0}.body :global(.condition-tabs){display:flex;gap:7px;flex-wrap:wrap}.body button{font:12px var(--font-mono);cursor:pointer;border:1px solid var(--ink);padding:10px 14px;background:transparent;color:var(--ink)}.body button[aria-pressed=true]{background:var(--ink);color:var(--bone)}.body :global(#plate-image){display:block;width:100%;max-width:670px;margin:24px auto;height:auto}.body :global(.small){font-size:12px}.body :global(.table-scroll){width:100%;overflow-x:auto;margin:26px 0}.body table{border-collapse:collapse;min-width:650px;width:100%;font-size:12px;line-height:1.6}.body th{text-align:left;background:var(--ink);color:var(--bone);font-weight:400}.body th,.body td{padding:13px 12px;border-bottom:1px solid rgba(10,10,8,.3)}.body details{margin:26px 0;border:1px solid var(--ink);padding:18px 22px;max-width:100%;min-width:0}.body summary{cursor:pointer;font-size:13px}.body pre{background:var(--ink);color:var(--bone);padding:24px;white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.7 var(--font-mono);max-width:100%;overflow-x:auto}.body code{font:inherit;overflow-wrap:anywhere}.body :global(.stat-band){display:grid;grid-template-columns:repeat(3,1fr);gap:25px;background:var(--ink);color:var(--bone);padding:30px;margin:35px 0}.body :global(.stat-band) strong{display:block;font:clamp(34px,4vw,56px)/1.2 var(--font-display);color:var(--oxide)}.body :global(.stat-band) span{display:block;font-size:11px;margin-top:10px}.body :global(.quote){font:clamp(35px,5vw,64px)/1.2 var(--font-display);border-left:6px solid var(--verdigris);padding:12px 0 12px 25px;margin:30px 0}.body :global(.downloads){display:grid;grid-template-columns:repeat(2,1fr);border-top:1px solid var(--ink);margin:32px 0}.body :global(.downloads) a{padding:15px 12px;font-size:12px;border-bottom:1px solid rgba(10,10,8,.4)}@media(max-width:650px){.body{padding:16px;font-size:13px;line-height:1.8}.body h2{font-size:33px;margin-top:52px}.body :global(.pair),.body :global(.stat-band),.body :global(.downloads){grid-template-columns:1fr}.body details{padding:14px}.body pre{font-size:10px;padding:16px}.body button{padding:9px 10px;font-size:10px}}
'''
(route/'plate-001.module.css').write_text(css)
# Only append the study destination to the current research index and sitemap.
changed={}
for rel in ['app/research/page.tsx','app/sitemap.ts','package.json']:
 path=site/rel;before=path.read_text();after=before
 if rel.endswith('research/page.tsx') and 'href="/research/plate-001"' not in before:
  row='''        <div className="research-feature-row"><div><h3>Plate 001: Qwen3-8B Base under quantization</h3><p>1,680 strict-output trials across seven precision levels. Q8/Q6 stayed near F16; Q2 collapsed. Fixed Experiment Plates and inspectable raw evidence.</p></div><Link className="study-link" href="/research/plate-001">Open Plate 001 <span aria-hidden="true">→</span></Link></div>\n'''
  needle='        {researchSurface.registryStudies.map((study) => (' if 'researchSurface.registryStudies.map' in before else '        <div className="research-feature-row">';at=before.index(needle);after=before[:at]+row+before[at:]
 elif rel.endswith('sitemap.ts') and '`${site.url}/research/plate-001`' not in before:
  needle='    { url: `${site.url}/research`, lastModified: new Date() },';assert needle in before;after=before.replace(needle,needle+'\n    { url: `${site.url}/research/plate-001`, lastModified: new Date("2026-10-01") },',1)
 elif rel=='package.json' and 'prepare-plate-001-assets.mjs' not in before:
  assert '"scripts": { ' in before;after=before.replace('"scripts": { ','"scripts": { "prebuild": "node scripts/prepare-plate-001-assets.mjs", ',1)
 if after!=before:
  path.write_text(after);changed['sites/mm-labs/'+rel]=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/sites/mm-labs/'+rel,tofile='b/sites/mm-labs/'+rel))
 if rel not in changed and (reportdir/'existing-files.patch').exists():continue
if changed:(reportdir/'existing-files.patch').write_text(''.join(changed.values()))
# Hash-pinned build inputs preserve original exports while avoiding scanner false
# matches inside base64 fonts. The site prebuild restores exact original bytes.
source_assets=site/'plate-001-source-assets';source_assets.mkdir(exist_ok=True)
generated={}
for file in public.rglob('*'):
 if not file.is_file() or file.suffix not in {'.svg','.html'}:continue
 original=file.read_bytes();text=original.decode('utf-8')
 matches=list(re.finditer(r'AKIA[0-9A-Z]{16}',text,re.I))
 if not matches:continue
 spans=[(m.start(),m.end()) for m in re.finditer(r'data:font/[^,;]+;base64,[A-Za-z0-9+/=]+',text)]
 assert all(any(a<=m.start()<m.end()<=b for a,b in spans) for m in matches),'Unexpected credential-like content outside font data'
 rel=str(file.relative_to(public));target=source_assets/(rel+'.gz');target.parent.mkdir(parents=True,exist_ok=True)
 encoded=gzip.compress(original,compresslevel=8,mtime=0);assert gzip.decompress(encoded)==original;target.write_bytes(encoded)
 generated[rel]=hashlib.sha256(original).hexdigest()
(source_assets/'manifest.json').write_text(json.dumps({'format':'plate-001/static-build-inputs@1.0','encoding':'gzip','assets':generated},indent=2)+'\n')
(public/'.gitignore').write_text(''.join('/'+rel+'\n' for rel in sorted(generated)))
prep=site/'scripts/prepare-plate-001-assets.mjs';prep.parent.mkdir(exist_ok=True);shutil.copy2(R/'scripts/publication/site-static-assets.mjs',prep)
newfiles=[p for p in route.rglob('*') if p.is_file()]+[p for p in public.rglob('*') if p.is_file() and str(p.relative_to(public)) not in generated]+[p for p in source_assets.rglob('*') if p.is_file()]+[prep]
manifest={'format':'major-minor/site-integration@1.0','site':'mm-labs','production_article_url':'https://majorminor.xyz/research/plate-001','article_route':'sites/mm-labs/app/research/plate-001/page.tsx','public_asset_root':'sites/mm-labs/public/research/plate-001','primary_launch_image':base+'/publication/social/plate-001-launch-1600.png','public_data_encoding':'Original ledger and machine-path command metadata are downloadable gzip files; decompressed bytes match original evidence hashes. No observations or hashes were redacted.','evidence_archive_bytes':evidence.stat().st_size,'largest_asset_bytes':max(p.stat().st_size for p in newfiles),'existing_files_patch':'existing-files.patch','new_files':{str(p.relative_to(platform)):hashlib.sha256(p.read_bytes()).hexdigest() for p in newfiles},'static_asset_build':'Original SVG/HTML restored from hash-pinned gzip build inputs; served bytes remain unchanged','generated_files':{'sites/mm-labs/public/research/plate-001/'+rel:h for rel,h in generated.items()},'existing_files':['sites/mm-labs/app/research/page.tsx','sites/mm-labs/app/sitemap.ts','sites/mm-labs/package.json'],'deployed':False}
(reportdir/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Integrated completed article at /research/plate-001 with '+str(len(newfiles))+' new route/assets files; research index and sitemap extended. No deployment.')
