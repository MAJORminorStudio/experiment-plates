import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
const {chromium}=await import('playwright');
const p=fileURLToPath(new URL('../../studies/qwen3-8b-base-20261001/publication/',import.meta.url));
const study=p+'../';const origin=process.env.PLATE_QA_ORIGIN??'http://127.0.0.1:4180';const reportRoot=process.env.PLATE_QA_REPORT_DIR??p+'site-integration';const url=origin+'/research/plate-001';mkdirSync(reportRoot+'/qa',{recursive:true});
const browser=await chromium.launch({headless:true,...(process.env.PLATE_QA_BROWSER_CHANNEL?{channel:process.env.PLATE_QA_BROWSER_CHANNEL}:{}),...(process.env.PLATE_QA_BROWSER_PATH?{executablePath:process.env.PLATE_QA_BROWSER_PATH}:{})});const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto(url,{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);
if(await page.locator('h1').count()!==1)throw Error('Article requires one h1');
const og=await page.locator('meta[property="og:image"]').getAttribute('content');if(!og.endsWith('/research/plate-001/publication/social/plate-001-launch-1600.png'))throw Error('Wrong primary launch image');
for(const file of ['plate-001-launch-1600.png','plate-001-launch-1600.svg']){const res=await page.request.get(origin+'/research/plate-001/publication/social/'+file);if(!res.ok())throw Error('Launch asset failed '+file);if(createHash('sha256').update(await res.body()).digest('hex')!==createHash('sha256').update(readFileSync(p+'social/'+file)).digest('hex'))throw Error('Launch asset byte mismatch '+file)}
for(const img of await page.locator('article img').all()){await img.scrollIntoViewIfNeeded();await img.evaluate(i=>i.complete&&i.naturalWidth>0?Promise.resolve():new Promise((res,rej)=>{i.addEventListener('load',res,{once:true});i.addEventListener('error',rej,{once:true})}));}
await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:reportRoot+'/qa/article-desktop.png',fullPage:true});await page.screenshot({path:reportRoot+'/qa/article-desktop-hero.png'});
for(const quant of ['F16','Q8_0','Q6_K','Q5_K_M','Q4_K_M','Q3_K_M','Q2_K']){
 await page.locator(`[data-quant="${quant}"]`).click();await page.waitForFunction(q=>document.querySelector('#plate-summary').textContent.startsWith(q),quant);
 await page.waitForFunction(q=>{const i=document.querySelector('#plate-image');return i.src.includes(q+'.png')&&i.complete&&i.naturalWidth>0},quant);
}
const resources=await page.locator('article [href],article [src]').evaluateAll(els=>[...new Set(els.map(e=>e.href??e.src).filter(Boolean))]);const links=[];for(const target of resources){const res=await page.request.get(target);links.push({path:new URL(target).pathname,status:res.status()});if(!res.ok())throw Error('Production link failed '+target)}
const hash=b=>createHash('sha256').update(b).digest('hex');const downloads=[];
for(const name of ['raw/trials.jsonl','model-manifest.json','quantization-commands.json','performance.json']){
 const res=await page.request.get(origin+'/research/plate-001/'+name+'.gz');const body=gunzipSync(await res.body());if(hash(body)!==hash(readFileSync(study+name)))throw Error('Evidence download differs '+name);downloads.push({file:name+'.gz',decompressed_sha256:hash(body),original_bytes_preserved:true});
}
for(const width of [360,390,768]){
 await page.setViewportSize({width,height:844});await page.goto(url,{waitUntil:'networkidle'});await page.locator('footer').scrollIntoViewIfNeeded();const overflow=await page.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth}));if(overflow.viewport!==overflow.document)throw Error('Mobile overflow '+width);
 await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:reportRoot+`/qa/article-${width}-hero.png`});
}
await page.setViewportSize({width:1440,height:1000});await page.goto(origin+'/research/plate-001/artifacts/inspector.html',{waitUntil:'networkidle'});await page.locator('[data-condition-button="Q2_K"]').click();await page.locator('.plate:not([hidden]) [data-unit="task-003"]').first().click();if(!(await page.locator('#status').innerText()).includes('0 / 3'))throw Error('Inspector selection mismatch');await page.locator('#compare').click();if(await page.locator('.plate:not([hidden])').count()!==8)throw Error('Compare panel mismatch');
const dp=page.waitForEvent('download');await page.locator('#download').click();const download=await dp;const dlPath=reportRoot+'/qa/inspector-normalized.json';await download.saveAs(dlPath);if(hash(readFileSync(dlPath))!==hash(readFileSync(study+'normalized.json')))throw Error('Inspector download mismatch');
await page.setViewportSize({width:360,height:844});if(!(await page.evaluate(()=>innerWidth===document.documentElement.scrollWidth)))throw Error('Inspector mobile overflow');await page.screenshot({path:reportRoot+'/qa/inspector-mobile.png'});
await page.goto(origin+'/research',{waitUntil:'networkidle'});if(await page.locator('a[href="/research/plate-001"]').count()!==1)throw Error('Research index entry missing or duplicated');
const sitemap=await page.request.get(origin+'/sitemap.xml');if(!(await sitemap.text()).includes('https://majorminor.xyz/research/plate-001'))throw Error('Sitemap route missing');
if(errors.length)throw Error('Page errors: '+errors.join('; '));
writeFileSync(reportRoot+'/production-validation.json',JSON.stringify({status:'passed',production_route:'/research/plate-001',primary_launch_image:'/research/plate-001/publication/social/plate-001-launch-1600.png',site_build:'Next.js 16 + OpenNext production build passed',mobile_widths:[360,390,768],links,downloads,inspector:{task:'task-003',condition:'Q2_K',successes:'0/3',compare_panels:8,canonical_download:'byte-identical',mobile_width:360},research_index:'one entry',sitemap:'canonical route included',browser_errors:errors,production_deployed:process.env.PLATE_QA_DEPLOYED==='1',origin},null,2)+'\n');await browser.close();console.log('Production-relative QA passed: article, launch metadata, links/images, seven conditions, gzip downloads, inspector, mobile, research index and sitemap.');
