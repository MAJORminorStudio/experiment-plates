import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
const root=fileURLToPath(new URL('../',import.meta.url));
const hash=b=>createHash('sha256').update(b).digest('hex');
const tree=JSON.parse(readFileSync(join(root,'releases/github-tree-live.json')));
const blobs=tree.tree.filter(x=>x.type==='blob');
for(const item of blobs){const bytes=execFileSync('git',['-C',root,'cat-file','blob',item.sha],{maxBuffer:128*1024*1024});const gitHash=createHash('sha1').update(Buffer.from(`blob ${bytes.length}\0`)).update(bytes).digest('hex');if(gitHash!==item.sha)throw Error('Remote Git blob mismatch '+item.path)}
if(blobs.length!==262||tree.truncated)throw Error('Incomplete repository tree');
const releases=JSON.parse(readFileSync(join(root,'releases/github-releases-live.json')));
const wanted=releases.filter(r=>['plate-v0.1.0','plate-001-v1.0.0'].includes(r.tag_name));
if(wanted.length!==2||wanted.some(r=>r.draft||r.prerelease))throw Error('Releases not public');
const report={status:'passed',repository:'https://github.com/MAJORminorStudio/experiment-plates',remote_git_blobs_verified:blobs.length,pages:[],assets:[]};
for(const url of [report.repository,...wanted.map(r=>r.html_url)]){const response=await fetch(url,{signal:AbortSignal.timeout(60000)});if(response.status!==200)throw Error('Public page failed '+url+' '+response.status);await response.arrayBuffer();report.pages.push({url,status:response.status})}
const files=wanted.flatMap(r=>r.assets);
for(let i=0;i<files.length;i+=3){await Promise.all(files.slice(i,i+3).map(async asset=>{
 const name=asset.name;const source=name==='plate-001-demo.mp4'?join(root,'studies/qwen3-8b-base-20261001/publication/demo',name):name.startsWith('plate-001-launch-1600')?join(root,'studies/qwen3-8b-base-20261001/publication/social',name):join(root,'releases',name);
 const expected=hash(readFileSync(source));if(asset.digest!=='sha256:'+expected)throw Error('GitHub upload digest mismatch '+name);
 const response=await fetch(asset.browser_download_url,{signal:AbortSignal.timeout(60000)});if(response.status!==200)throw Error('Public asset failed '+name+' '+response.status);const bytes=Buffer.from(await response.arrayBuffer());if(hash(bytes)!==expected||bytes.length!==asset.size)throw Error('Public download byte mismatch '+name);
 report.assets.push({url:asset.browser_download_url,status:200,bytes:bytes.length,sha256:expected});console.log('Verified public release download: '+name);
 }))}
report.assets.sort((a,b)=>a.url.localeCompare(b.url));writeFileSync(join(root,'releases/github-live-validation.json'),JSON.stringify(report,null,2)+'\n');console.log('GitHub live verification passed: public repo/release pages, 262 remote Git blobs and all 8 release downloads.');
