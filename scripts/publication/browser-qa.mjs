import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE ?? 'playwright');
const out=fileURLToPath(new URL('../../studies/qwen3-8b-base-20261001/publication/',import.meta.url));
mkdirSync(out+'qa',{recursive:true});
const base='http://127.0.0.1:4173/studies/qwen3-8b-base-20261001/';
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto(base+'publication/',{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);
for(const image of await page.locator('img').all()){await image.scrollIntoViewIfNeeded();await image.evaluate(i=>i.complete&&i.naturalWidth>0?Promise.resolve():new Promise((resolve,reject)=>{i.addEventListener('load',resolve,{once:true});i.addEventListener('error',reject,{once:true})}));}await page.waitForLoadState('networkidle');
let images=await page.locator('img').evaluateAll(imgs=>imgs.map(i=>({src:i.getAttribute('src'),loaded:i.complete&&i.naturalWidth>0})));
if(images.some(i=>!i.loaded))throw Error('Image failed to load');
await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:out+'qa/article-desktop.png',fullPage:true});
await page.screenshot({path:out+'qa/article-desktop-hero.png'});
for(const quant of ['F16','Q8_0','Q6_K','Q5_K_M','Q4_K_M','Q3_K_M','Q2_K']){await page.locator(`[data-quant="${quant}"]`).click();await page.waitForFunction(()=>{const i=document.querySelector('#plate-image');return i.complete&&i.naturalWidth>0});if(!(await page.locator('#plate-summary').innerText()).startsWith(quant))throw Error('Plate selector failed');}
const links=await page.locator('a[href]').evaluateAll(as=>[...new Set(as.map(a=>a.href).filter(h=>h.startsWith('http')&&!h.includes('#')))]);
const linkResults=[];for(const url of links){const res=await page.request.get(url);linkResults.push({url,status:res.status()});if(!res.ok())errors.push('Link failure '+url);}
await page.getByRole('heading',{name:'Limitations',exact:true}).scrollIntoViewIfNeeded();await page.screenshot({path:out+'qa/limitations-desktop.png'});
const responsive=[];for(const width of [390,768]){await page.setViewportSize({width,height:844});await page.goto(base+'publication/',{waitUntil:'networkidle'});await page.locator('footer').scrollIntoViewIfNeeded();await page.evaluate(()=>scrollTo(0,0));const sizes=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,fonts:document.fonts.check('16px Anton')&&document.fonts.check('16px "IBM Plex Mono"')}));if(sizes.width!==sizes.scroll||!sizes.fonts)throw Error('Responsive overflow or font failure '+JSON.stringify(sizes));responsive.push(sizes);await page.screenshot({path:out+`qa/article-${width}.png`,fullPage:true});await page.screenshot({path:out+`qa/article-${width}-hero.png`});}
await page.setViewportSize({width:1440,height:1000});await page.goto(base+'artifacts/inspector.html',{waitUntil:'networkidle'});await page.evaluate(()=>document.fonts.ready);
await page.locator('[data-condition-button="Q2_K"]').click();await page.screenshot({path:out+'demo/inspector-unselected.png'});
const task=page.locator('.plate:not([hidden]) [data-unit="task-003"]').first();await task.scrollIntoViewIfNeeded();await task.click();
if(!(await page.locator('#condition').innerText()).includes('Q2_K / task-003'))throw Error('Inspector selection failed');
if(!(await page.locator('#status').innerText()).includes('0 / 3'))throw Error('Wrong task outcomes');
await page.locator('summary').filter({hasText:'Underlying observations'}).click();if(!(await page.locator('#raw').innerText()).includes('Q2_K-task-003-r1'))throw Error('Raw evidence missing');
await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:out+'demo/inspector-selection.png'});
await page.locator('#compare').click();if(await page.locator('.plate:not([hidden])').count()!==8)throw Error('Inspector comparison failed');
const downloadPromise=page.waitForEvent('download');await page.locator('#download').click();const download=await downloadPromise;await download.saveAs(out+'qa/downloaded-normalized.json');if(readFileSync(out+'qa/downloaded-normalized.json','utf8')!==readFileSync(out+'../normalized.json','utf8'))throw Error('Inspector download mismatch');
await page.setViewportSize({width:390,height:844});const inspectorWidth=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));if(inspectorWidth.width!==inspectorWidth.scroll)throw Error('Inspector mobile overflow');
await page.screenshot({path:out+'qa/inspector-mobile.png'});
if(errors.length)throw Error('Browser errors '+errors.join('; '));
writeFileSync(out+'qa/browser-report.json',JSON.stringify({status:'passed',article_images:images,local_links:linkResults,responsive,inspector:{task:'task-003',condition:'Q2_K',successes:'0/3',comparison_panels:8,canonical_download:'byte-identical',mobile:inspectorWidth},browser_errors:errors},null,2)+'\n');
await browser.close();console.log('Browser QA passed: images, links, seven selectors, 390/768 layouts, inspector pin/compare/download/mobile.');
