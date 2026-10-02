/** Study composition adapter. The frozen renderer's source and stroke construction are unchanged. */
import { readFileSync,writeFileSync,mkdirSync,readdirSync,existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve,join } from 'node:path';
import { normalize } from '../../../dist/src/input.js';
import { makeSpec } from '../../../dist/src/spec.js';
import { buildScene,unitScene,label,line,summarize } from '../../../dist/src/scene.js';
import { renderPrimitive,renderUnit,fonts,rasterize } from '../../../dist/src/svg.js';
import { inspector } from '../../../dist/src/inspector.js';
import { canonical,hash,xml,unxml } from '../../../dist/src/util.js';
import { COLORS as C,VISUAL_VERSION,RENDERER_VERSION,MAPPINGS } from '../../../dist/src/types.js';
const root=fileURLToPath(new URL('../',import.meta.url)),repo=resolve(root,'../..'),out=join(root,'artifacts');
const load=p=>JSON.parse(readFileSync(join(root,p),'utf8'));
const freeze=JSON.parse(readFileSync(join(repo,'releases/visual-0.1.freeze.json'),'utf8'));
function assert(ok,message){if(!ok)throw new Error(message)}
function checkFreeze(){for(const [file,expected] of Object.entries(freeze.files))assert(hash(readFileSync(join(repo,file)))===expected,'Frozen renderer changed: '+file);}
/** Validate existing canonical fields in 20-unit chunks, then retain all 80 atomic tasks. */
function normalizeStudy(raw){
 assert(raw.experiment.synthetic===false,'Synthetic study input forbidden');assert(raw.units.length===80,'Require exactly 80 tasks');assert(raw.conditions.length===7,'Require all seven conditions');
 const chunks=[];for(let part=0;part<4;part++){
  const units=raw.units.slice(part*20,(part+1)*20),ids=new Set(units.map(u=>u.id));
  chunks.push(normalize({...raw,units,observations:raw.observations.filter(o=>ids.has(o.unit))}));
 }
 const observations=chunks.flatMap(d=>d.observations),bySlot=new Map(observations.map(o=>[`${o.condition}/${o.unit}/${o.run}`,o]));
 const expected=raw.conditions.flatMap(c=>raw.units.flatMap(u=>[1,2,3].map(run=>bySlot.get(`${c.id}/${u.id}/${run}`))));
 assert(expected.length===1680&&expected.every(o=>o&&o.success!==null),'Missing or incomplete real trial slots');assert(observations.length===raw.observations.length,'Unknown/extra trial observations');
 return {...raw,observations:expected};
}
const bytes=readFileSync(join(root,'normalized.json'));const data=normalizeStudy(JSON.parse(bytes));
const canonicalPanels=Array.from({length:4},(_,part)=>{
 const units=data.units.slice(part*20,(part+1)*20),ids=new Set(units.map(u=>u.id));
 return normalize({...data,units,observations:data.observations.filter(o=>ids.has(o.unit))});
});
const input={data,sourceBase64:bytes.toString('base64'),sourceHash:hash(bytes),normalizedHash:hash(canonical(data))};
const spec=makeSpec('normalized.json',input),results=load('results.json'),study=load('experiment-manifest.json');
assert(VISUAL_VERSION==='0.1'&&RENDERER_VERSION==='0.1.0','Wrong frozen versions');assert(results.trial_count===1680&&results.synthetic===false,'Real results required');
const evidence=(condition,unit,derived={})=>{
 const obs=data.observations.filter(o=>(condition==='series'||o.condition===condition)&&(!unit||o.unit===unit));
 return {condition,...(unit?{unit}:{}),runs:[...new Set(obs.map(o=>o.run))],observationIds:obs.map(o=>o.id),derived};
};
function scenesFor(condition){return Array.from({length:4},(_,part)=>{
 const units=data.units.slice(part*20,(part+1)*20),ids=new Set(units.map(u=>u.id)),partial={...data,units,observations:data.observations.filter(o=>ids.has(o.unit))};
 const scene=buildScene(partial,spec,condition);scene.part=part+1;
 scene.frame=scene.frame.map(p=>({...p,id:`p${part+1}-${p.id}`}));
 scene.units=units.map((u,localIndex)=>{
  const group=unitScene(data,spec,condition,u.id,part*20+localIndex);
  return {...group,y:group.y-part*5*143};
 });
 return scene;
});}
const allScenes=data.conditions.flatMap(c=>scenesFor(c.id));
const getScene=(condition,taskId)=>allScenes.find(s=>s.condition===condition&&s.units.some(u=>u.unit===taskId));
const sceneBody=s=>s.frame.map(p=>renderPrimitive(p)).join('')+s.units.map(u=>renderUnit(s,u.unit)).join('');
const bg=(id,width,height)=>({id,tag:'rect',attrs:{x:0,y:0,width,height,fill:C.bone},role:'structure',channels:[]});
const text=(id,x,y,value,size=14,display=false,ev)=>label(id,x,y,String(value),size,ev,display);
const dimensions={panel:{width:960,height:1260},plate:{width:2064,height:2844},'contact-sheet':{width:4800,height:3720},hero:{width:2400,height:1500}};
function conditionComposition(condition,prefix=''){
 const s=summarize(data.observations.filter(o=>o.condition===condition)),e=evidence(condition,null,{successes:s.successes,total:s.total});
 const p=[bg(prefix+condition+'-composition-bg',2064,2844),text(prefix+condition+'-composition-brand',48,76,'MAJOR//MINOR',48,true),text(prefix+condition+'-composition-title',700,73,condition+' / QWEN3-8B BASE',45,true,e),text(prefix+condition+'-composition-detail',48,127,`80 TASKS / 3 REPEATS / ${s.successes}/240 SUCCESSES / FOUR FROZEN PANELS / MEMORY = RSS / MEASURED`,19,false,e),line(prefix+condition+'-composition-rule',48,155,2016,155,C.ink,2)];
 const panels=scenesFor(condition).map((scene,i)=>`<g data-part="${i+1}" transform="translate(${48+(i%2)*1008} ${180+Math.floor(i/2)*1308})">${sceneBody(scene)}</g>`).join('');
 return {body:p.map(p=>renderPrimitive(p,prefix)).join('')+panels,primitives:p};
}
function contactComposition(){
 const all=evidence('series'),p=[bg('sheet-bg',4800,3720),text('sheet-brand',80,85,'MAJOR//MINOR',58,true),text('sheet-series',3030,67,'REAL EXPERIMENT / 001 / VISUAL 0.1',24,false,all),text('sheet-count',3030,106,'80 TASKS × 3 RUNS × 7 CONDITIONS = 1,680 TRIALS',21,false,all),line('sheet-top-rule',80,141,4660,141,C.ink,3),text('sheet-title',80,246,'AGENT CAPABILITY UNDER COMPRESSION',110,true,all),text('sheet-subtitle',84,302,'QWEN3-8B BASE / M1 MAX · 32 GB / MATCHED PROMPTS AND SEEDS / STRICT WHOLE-OUTPUT SCORING',23,false,all)];
 let panels='';data.conditions.forEach((c,i)=>{const composed=conditionComposition(c.id);p.push(...composed.primitives);panels+=`<g transform="translate(${80+(i%4)*1160} ${360+Math.floor(i/4)*1550}) scale(.52)">${composed.body}</g>`;});
 const taskId=results.hero_task_id,u=data.units.find(u=>u.id===taskId),x=3580,y=1910;
 p.push(text('sheet-follow',x+22,y+80,'FOLLOW '+taskId.toUpperCase(),64,true,evidence('series',taskId)),text('sheet-follow-name',x+22,y+124,u.name.toUpperCase(),25,false,evidence('series',taskId)),text('sheet-follow-note',x+22,y+167,'SAME ADDRESS. STRICT WHOLE-OUTPUT SCORING.',19,false,evidence('series',taskId)),line('sheet-key-rule',x+22,y+196,x+1040,y+196,C.ink,2));
 let traces='';data.conditions.forEach((c,i)=>{
  const sum=summarize(data.observations.filter(o=>o.condition===c.id&&o.unit===taskId));const yy=y+238+i*171;
  p.push(text(`sheet-key-${c.id}`,x+22,yy+43,c.label,42,true,evidence(c.id,taskId)),text(`sheet-key-count-${c.id}`,x+22,yy+76,`${sum.successes}/3 INTACT`,19,false,evidence(c.id,taskId,{successes:sum.successes})));
  traces+=renderUnit(getScene(c.id,taskId),taskId,x+430,yy,1.18,'key-');
 });
 p.push(line('sheet-bottom-rule',80,3590,4660,3590,C.ink,3),text('sheet-bottom-source',80,3640,`SOURCE ${input.sourceHash.slice(0,12)} / LEDGER ${study.ledger_sha256.slice(0,12)} / VISUAL 0.1 / NO SYNTHETIC OBSERVATIONS / MEMORY = PROCESS RSS`,20,false,all),text('sheet-bottom-note',3330,3646,'ALL 80 TASK ADDRESSES PRESERVED.',40,true));
 // Headers/legend are rendered here; condition frame primitives are already inside each panel.
 const conditionIds=new Set(data.conditions.map(c=>c.id));const headers=p.filter(p=>!conditionIds.has(p.id.split('-composition')[0]));
 return {body:headers.map(p=>renderPrimitive(p)).join('')+panels+traces,primitives:p};
}
function heroComposition(){
 const all=evidence('series'),first=results.conditions[0],last=results.conditions.at(-1),taskId=results.hero_task_id,unit=data.units.find(u=>u.id===taskId);
 const p=[bg('hero-bg',2400,1500),text('hero-brand',64,77,'MAJOR//MINOR',48,true),text('hero-label',1560,58,'REAL EXPERIMENT / QWEN3-8B BASE',17,false,all),text('hero-meta',1560,86,'M1 MAX · 32 GB / VISUAL 0.1 / 1,680 TRIALS',13,false,all),line('hero-top-rule',64,113,2336,113,C.ink,2),text('hero-title-1',64,276,'80 TASKS.',128,true,all),text('hero-title-2',64,428,'SEVEN QUANTS.',112,true,all),text('hero-model',69,487,'QWEN3-8B BASE / F16 → Q2_K',20,false,all),text('hero-rate-f16',69,544,`F16: ${(first.success_rate*100).toFixed(1)}% SUCCESS`,24,false,evidence('F16')),text('hero-rate-q2',69,584,`Q2_K: ${(last.success_rate*100).toFixed(2)}% SUCCESS`,24,false,evidence('Q2_K')),text('hero-method',69,633,'Matched prompts. Three seeds per task.',17,false,all),text('hero-no-judge',69,665,'Strict whole-output scoring. No LLM judge.',17),text('hero-caveat',69,710,'MICROTASKS / PROPOSED TOOLS / BASE MODEL',13),text('hero-memory-note',69,748,'MEMORY: PROCESS RSS, NOT TOTAL UNIFIED MEMORY',13),line('hero-mid-rule',64,857,2336,857,C.ink,2),text('hero-follow',64,915,'FOLLOW ONE TASK THROUGH COMPRESSION',43,true),text('hero-task',67,954,`${taskId.toUpperCase()} / ${unit.name.toUpperCase()} / SAME TASK ADDRESS`,16,false,evidence('series',taskId)),line('hero-bottom-rule',64,1410,2336,1410,C.ink,2),text('hero-source',64,1450,`1,680 MEASURED TRIALS / LEDGER ${study.ledger_sha256.slice(0,12)} / VISUAL 0.1`,14,false,all),text('hero-footer-brand',1970,1454,'MAJOR//MINOR',35,true)];
 let panels='',details='';results.hero_conditions.forEach((condition,i)=>{
  const composition=conditionComposition(condition);p.push(...composition.primitives);panels+=`<g transform="translate(${848+i*493} 155) scale(.235)">${composition.body}</g>`;
  const x=67+i*770,sum=summarize(data.observations.filter(o=>o.condition===condition&&o.unit===taskId));
  p.push(text(`hero-detail-label-${condition}`,x,1021,condition,43,true,evidence(condition,taskId)),text(`hero-detail-stat-${condition}`,x+270,1019,`${sum.successes}/3 RUNS INTACT`,18,false,evidence(condition,taskId,{successes:sum.successes})));
  details+=renderUnit(getScene(condition,taskId),taskId,x,1035,2.7,`detail-${i}-`);
 });
 const headers=p.filter(p=>!p.id.includes('-composition-'));return {body:headers.map(p=>renderPrimitive(p)).join('')+panels+details,primitives:p};
}
function construct(kind,condition,part){
 const size=dimensions[kind];let scenes,composition;
 if(kind==='panel'){scenes=[scenesFor(condition)[part-1]];composition={body:sceneBody(scenes[0]),primitives:[]};}
 else if(kind==='plate'){scenes=scenesFor(condition);composition=conditionComposition(condition);}
 else if(kind==='contact-sheet'){scenes=allScenes;composition=contactComposition();}
 else {scenes=results.hero_conditions.flatMap(c=>scenesFor(c));composition=heroComposition();}
 const body=`<defs><style>${fonts().css}</style></defs>`+composition.body;
 const manifest={format:'major-minor/study-artifact@1.0',kind,condition:condition??(kind==='hero'?results.hero_conditions:data.conditions.map(c=>c.id)),...(part?{part}:{}),experimentId:data.experiment.id,rendererVersion:RENDERER_VERSION,visualVersion:VISUAL_VERSION,seed:spec.seed,dimensions:size,sourceHash:input.sourceHash,normalizedHash:input.normalizedHash,specHash:hash(canonical(spec)),bodyHash:hash(body),sceneHash:hash(canonical({scenes,compositionPrimitives:composition.primitives})),fontHashes:fonts().hashes,mappings:MAPPINGS,sourceBase64:input.sourceBase64,normalizedData:data,spec,scenes,compositionPrimitives:composition.primitives,provenance:{synthetic:false,trial_count:1680,raw_ledger_sha256:study.ledger_sha256,experiment_manifest_sha256:hash(readFileSync(join(root,'experiment-manifest.json'))),model_manifest_sha256:hash(readFileSync(join(root,'model-manifest.json'))),results_sha256:hash(readFileSync(join(root,'results.json'))),renderer_freeze_sha256:hash(readFileSync(join(repo,'releases/visual-0.1.freeze.json'))),task_suite_sha256:study.suite_sha256,source_model_revision:study.source_revision,llama_revision:study.llama_revision,studyAdapter:'Four unchanged 20-task panels; same stroke renderer and shared global scales. All 80 trial-level units retained. Composite manifests use the study verifier.'}};
 const title=`MAJOR//MINOR / ${kind} / ${condition??'F16 → Q2_K'}${part?' / part '+part:''}`;
 const svg=`<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="${size.width}" height="${size.height}" viewBox="0 0 ${size.width} ${size.height}" role="img" aria-labelledby="artifact-title artifact-description"><title id="artifact-title">${xml(title)}</title><desc id="artifact-description">Real Qwen3-8B-Base experiment. 80 tasks, three matched runs, seven common-source GGUF conditions. All marks derive from measured trial observations.</desc><metadata id="major-minor-manifest">${xml(canonical(manifest))}</metadata>\n${body}\n</svg>\n`;
 return {svg,manifest};
}
function verifyFile(path){
 const svg=readFileSync(path,'utf8'),match=svg.match(/<metadata id="major-minor-manifest">([\s\S]*?)<\/metadata>/);assert(match,'Missing embedded manifest');const m=JSON.parse(unxml(match[1]));
 assert(m.format==='major-minor/study-artifact@1.0','Wrong artifact format');assert(m.visualVersion==='0.1'&&m.rendererVersion==='0.1.0','Wrong frozen version');assert(m.provenance.synthetic===false&&m.normalizedData.experiment.synthetic===false,'Synthetic artifact rejected');
 assert(hash(Buffer.from(m.sourceBase64,'base64'))===m.sourceHash,'Source hash failed');assert(hash(canonical(normalizeStudy(JSON.parse(Buffer.from(m.sourceBase64,'base64').toString()))))===m.normalizedHash,'Normalized hash failed');assert(hash(canonical(m.spec))===m.specHash,'Spec hash failed');assert(hash(canonical({scenes:m.scenes,compositionPrimitives:m.compositionPrimitives}))===m.sceneHash,'Scene hash failed');assert(m.seed===spec.seed&&canonical(m.spec.scales)===canonical(spec.scales),'Seed/shared scales failed');
 const body=svg.match(/<\/metadata>\n([\s\S]*)\n<\/svg>\n$/)?.[1];assert(body&&hash(body)===m.bodyHash,'Body hash failed');
 const expected=construct(m.kind,typeof m.condition==='string'?m.condition:undefined,m.part);assert(svg===expected.svg,'Complete deterministic rerender failed');
 const ids=[...svg.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);assert(new Set(ids).size===ids.length,'Duplicate SVG IDs');
 const byId=new Map(data.observations.map(o=>[o.id,o]));for(const p of [...m.compositionPrimitives,...m.scenes.flatMap(s=>[...s.frame,...s.units.flatMap(u=>u.primitives)])]){
  assert(p.channels.every(k=>k in MAPPINGS),'Undeclared mapping');if(p.role==='data'){assert(p.evidence&&p.evidence.observationIds.length,'Unlinked data primitive');for(const id of p.evidence.observationIds){const o=byId.get(id);assert(o,'Unknown observation');assert(p.evidence.condition==='series'||p.evidence.condition===o.condition,'Evidence condition mismatch');assert(!p.evidence.unit||p.evidence.unit===o.unit,'Evidence unit mismatch');}}
 }
 return {file:path.slice(out.length+1),checks:14,dimensions:m.dimensions,svgHash:hash(svg),bodyHash:m.bodyHash};
}
function validatePositions(){
 const reference=allScenes.filter(s=>s.condition==='F16').flatMap(s=>s.units.map(u=>({unit:u.unit,part:s.part,x:u.x,y:u.y})));
 for(const c of data.conditions)assert(canonical(allScenes.filter(s=>s.condition===c.id).flatMap(s=>s.units.map(u=>({unit:u.unit,part:s.part,x:u.x,y:u.y}))))===canonical(reference),'Unstable task positions');
 return reference;
}
checkFreeze();validatePositions();
if(process.argv.includes('--verify')){
 canonicalPanels.forEach((panel,i)=>assert(canonical(normalize(load(`canonical-panels/part-${i+1}.json`)))===canonical(panel),'Canonical panel dataset mismatch'));
 const paths=[...readdirSync(out).filter(f=>f.endsWith('.svg')).map(f=>join(out,f)),...readdirSync(join(out,'panels')).filter(f=>f.endsWith('.svg')).map(f=>join(out,'panels',f))];
 const report=paths.map(verifyFile);assert(report.length===37,'Expected 9 release SVGs + 28 frozen panels');writeFileSync(join(out,'verification.json'),JSON.stringify({status:'passed',renderer_freeze:'unchanged',visualVersion:'0.1',artifacts:report,stable_positions:validatePositions(),scales:spec.scales,trial_count:1680,synthetic:false},null,2)+'\n');console.log('Verified 37 real SVG artifacts, renderer freeze, shared scales and all 80 stable addresses.');
}else{
 mkdirSync(join(root,'canonical-panels'),{recursive:true});canonicalPanels.forEach((panel,i)=>writeFileSync(join(root,'canonical-panels',`part-${i+1}.json`),JSON.stringify(panel,null,2)+'\n'));
 mkdirSync(join(out,'panels'),{recursive:true});const index=[];const panelManifests=[];
 for(const c of data.conditions){
  const a=construct('plate',c.id);writeFileSync(join(out,c.id+'.svg'),a.svg);writeFileSync(join(out,c.id+'.png'),rasterize(a.svg));index.push({file:c.id+'.svg',svgHash:hash(a.svg)});
  for(let part=1;part<=4;part++){const panel=construct('panel',c.id,part);writeFileSync(join(out,'panels',`${c.id}-p${part}.svg`),panel.svg);writeFileSync(join(out,'panels',`${c.id}-p${part}.png`),rasterize(panel.svg));panelManifests.push(panel.manifest);}
 }
 for(const kind of ['contact-sheet','hero']){const a=construct(kind);writeFileSync(join(out,kind+'.svg'),a.svg);writeFileSync(join(out,kind+'.png'),rasterize(a.svg));index.push({file:kind+'.svg',svgHash:hash(a.svg)});}
 // Part-major ordering pairs corresponding reference/current panels in comparison mode.
 panelManifests.sort((a,b)=>a.part-b.part||data.conditions.findIndex(c=>c.id===a.condition)-data.conditions.findIndex(c=>c.id===b.condition));
 const ledgerRows=readFileSync(join(root,'raw/trials.jsonl'),'utf8').trim().split('\n').map(JSON.parse);const rawById=new Map(ledgerRows.map(r=>[r.id,r]));
 const inspectorInput={...input,data:{...data,observations:data.observations.map(o=>{const r=rawById.get(o.id);return {...o,prompt_tokens:r.prompt_tokens,generated_tokens:r.generated_tokens,raw_output:r.raw_output,detailed_error_category:r.error_category,error_flags:r.error_flags,raw_row_id:r.id};})}};
 let html=inspector(inspectorInput,spec,panelManifests);html=html.replace(/(<script id="evidence" type="application\/json">)([\s\S]*?)(<\/script>)/,(_all,open,json,close)=>{const state=JSON.parse(json);state.provenance.raw_ledger_sha256=study.ledger_sha256;state.provenance.memory_metric='Sampled process RSS; not total unified-memory occupancy';state.provenance.timeout_mapping='Generation budget exhausted; no transport timeouts occurred in the scored run';state.provenance.extra_evidence='Token counts, raw outputs and detailed error flags join by observation ID to the preserved real ledger.';return open+JSON.stringify(state).replaceAll('<','\\u003c')+close;});
 // Initialize all four reference panels; keep canonical download free of the raw-evidence join.
 html=html.replace('Measured experiment observations. Hover to read.','Measured observations. Memory is sampled process RSS, not total unified memory. Hover to read.');
 html=html.replace('</script></body>',`updatePlates();el('download').onclick=()=>{const url=URL.createObjectURL(new Blob([${JSON.stringify(bytes.toString()).replaceAll('<','\\u003c')}],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='normalized-experiment.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};</script></body>`);
 writeFileSync(join(out,'inspector.html'),html);writeFileSync(join(root,'plate-spec.json'),JSON.stringify(spec,null,2)+'\n');writeFileSync(join(out,'series-manifest.json'),JSON.stringify({format:'major-minor/real-series@1.0',visualVersion:'0.1',rendererVersion:'0.1.0',experimentId:data.experiment.id,sourceHash:input.sourceHash,normalizedHash:input.normalizedHash,specHash:hash(canonical(spec)),observations:1680,conditions:data.conditions.map(c=>c.id),task_positions:validatePositions(),artifacts:index},null,2)+'\n');
 console.log('Exported 7 four-panel condition plates, contact sheet, hero, inspector, and 28 frozen detail panels.');
}
