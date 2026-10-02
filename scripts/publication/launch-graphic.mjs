/** Dedicated Plate 001 social artwork; canonical visual-0.1 renderer/data stay unchanged. */
import {readFileSync, writeFileSync, mkdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {Resvg} from '../../node_modules/@resvg/resvg-js/index.js';
import {unitScene} from '../../dist/src/scene.js';
const root=fileURLToPath(new URL('../../',import.meta.url));
const study=root+'studies/qwen3-8b-base-20261001/';
const out=study+'publication/social/'; mkdirSync(out+'qa/',{recursive:true});
const read=p=>readFileSync(p,'utf8');
const hash=b=>createHash('sha256').update(b).digest('hex');
const dataset=JSON.parse(read(study+'normalized.json'));
const spec=JSON.parse(read(study+'plate-spec.json'));
const results=JSON.parse(read(study+'results.json'));
const ledger=read(study+'raw/trials.jsonl').trim().split('\n').map(JSON.parse);
const conditions=['F16','Q8_0','Q6_K','Q5_K_M','Q4_K_M','Q3_K_M','Q2_K'];
assert.deepEqual(dataset.conditions.map(c=>c.id),conditions);
assert.equal(dataset.experiment.synthetic,false); assert.equal(results.synthetic,false);
assert.equal(dataset.experiment.repeats,3); assert.equal(dataset.units.length,80);
assert.equal(dataset.observations.length,1680); assert.equal(ledger.length,1680);
assert.equal(new Set(ledger.map(o=>o.id)).size,1680);
const raw=new Map(ledger.map(o=>[o.id,o]));
for(const o of dataset.observations){
 assert.equal(raw.get(o.id)?.success,o.success);
 assert.equal(raw.get(o.id)?.task_id,o.unit);
 for(const key of ['latency_ms','tokens_per_second','memory_gb']) assert.equal(raw.get(o.id)[key],o[key]);
}
const aggregates=conditions.map(condition=>{
 const obs=dataset.observations.filter(o=>o.condition===condition);
 const successes=obs.filter(o=>o.success===true).length;
 assert.equal(obs.length,240); assert.equal(obs.filter(o=>o.success===null).length,0);
 const r=results.conditions.find(c=>c.condition===condition);
 assert.equal(r.successes,successes); assert.equal(r.trials,obs.length);
 assert.equal(r.success_rate,successes/obs.length);
 return {condition,successes,trials:obs.length,success_rate:successes/obs.length,display_rate:(100*successes/obs.length).toFixed(2)+'%'};
});
const C={bone:'#E7DFCC',ink:'#0A0A08',verdigris:'#3DA887',oxide:'#D9643A'};
const fontFiles=[root+'assets/fonts/Anton-Regular.ttf',root+'assets/fonts/IBMPlexMono-Regular.ttf'];
const fontOptions={loadSystemFonts:false,fontFiles};
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const text=(x,y,s,size=28,font='IBM Plex Mono',fill=C.ink,extra='')=>`<text x="${x}" y="${y}" font-family="${font}" font-size="${size}" fill="${fill}" ${extra}>${esc(s)}</text>`;
const rect=(x,y,w,h,fill)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}"/>`;
const line=(x1,y1,x2,y2,stroke=C.ink,width=1)=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${stroke}" stroke-width="${width}"/>`;
const round=x=>Number(x.toFixed(3));
let body=rect(0,0,1600,1600,C.bone);
// Baseline aligned wordmark: the literal font-size ratio is 39.2 / 56 = 0.70.
const measure=(s,size,font='Anton')=>{
 const tmp=new Resvg(`<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="300">${text(0,200,s,size,font)}</svg>`,{font:fontOptions});
 const box=tmp.getBBox(); return box.x+box.width;
};
const majorWidth=measure('MAJOR',56); const slashWidth=measure('//',56);
body+=text(72,106,'MAJOR',56,'Anton');
body+=text(72+majorWidth+3,106,'//',56,'Anton',C.verdigris);
body+=text(72+majorWidth+3+slashWidth+3,106,'MINOR',39.2,'Anton');
body+=text(1528,80,'EXPERIMENT PLATES',25,'IBM Plex Mono',C.ink,'text-anchor="end"');
body+=text(1528,113,'PLATE 001 / VISUAL 0.1',25,'IBM Plex Mono',C.ink,'text-anchor="end"');
body+=line(72,146,1528,146,C.ink,2);
body+=text(72,285,'1,680 real trials',126,'Anton');
body+=text(75,353,'Qwen3-8B Base / 1,680 trials / M1 Max 32 GB',40);
body+=text(75,402,'80 tasks × 3 repeats × 7 conditions',40);
body+=line(72,435,1528,435,C.ink,2);
body+=text(72,475,'CONDITION',26);
body+=text(410,475,'STRICT SUCCESS',26);
body+=text(744,475,'TASKS 001 → 080 / FIXED ORDER',26);
const evidence=[]; let traceCount=0; let successEndpointCount=0;
const mapping={columns:10,rows:8,cell_width:78.4,cell_height:14,x_scale:.37,y_scale:.25,trace_width:2.4,endpoint_radius:2.4,envelope_width:.78,optical_stroke_increase:1.2};
for(const [i,a] of aggregates.entries()){
 const top=493+i*128; const collapsed=a.condition==='Q2_K';
 if(collapsed){
  body+=rect(60,top,1480,130,C.ink);
  body+=rect(732,top+6,800,118,C.bone);
 }else body+=line(72,top+127,1528,top+127,C.ink,.75);
 const labelColor=collapsed?C.bone:C.ink;
 body+=text(72,top+69,a.condition,60,'IBM Plex Mono',labelColor);
 body+=text(410,top+76,a.display_rate,84,'Anton',labelColor);
 body+=text(413,top+112,`${a.successes} / ${a.trials}`,27,'IBM Plex Mono',labelColor);
 if(collapsed) body+=text(72,top+111,'COLLAPSE',36,'Anton',C.oxide);
 for(const [taskIndex,unit] of dataset.units.entries()){
  const group=unitScene(dataset,spec,a.condition,unit.id,taskIndex);
  const gx=744+(taskIndex%10)*mapping.cell_width;
  const gy=top+7+Math.floor(taskIndex/10)*mapping.cell_height;
  const px=x=>round(gx+x*mapping.x_scale);
  const py=y=>round(gy+7+(y-91)*mapping.y_scale);
  const obs=dataset.observations.filter(o=>o.condition===a.condition&&o.unit===unit.id);
  assert.equal(obs.length,3); assert.deepEqual(obs.map(o=>o.run),[1,2,3]);
  evidence.push({condition:a.condition,task:unit.id,task_index:taskIndex+1,x:gx,y:gy,observations:obs.map(o=>o.id),primitives:[]});
  for(const p of group.primitives){
   if(p.id.endsWith('-envelope')){
    const env=p.evidence.derived.envelope_px; assert.ok(env!==null);
    const x=px(196),y=py(91-env/2),height=round(env*mapping.y_scale);
    body+=`<path id="${p.id}" d="M${x},${y}h1.11v${height}h-1.11" fill="none" stroke="${C.ink}" stroke-width="${mapping.envelope_width}"/>`;
    evidence.at(-1).primitives.push(p);
   }else if(p.id.endsWith('-trace')){
    // Frozen M/L path geometry, uniformly projected to this social composition.
    const d=p.attrs.d.replace(/([ML])(-?[\d.]+),(-?[\d.]+)/g,(_,cmd,x,y)=>`${cmd}${px(Number(x))},${py(Number(y))}`);
    body+=`<path id="${p.id}" d="${d}" fill="none" stroke="${p.attrs.stroke}" stroke-width="${mapping.trace_width}" stroke-linecap="butt" stroke-linejoin="miter"/>`;
    evidence.at(-1).primitives.push(p); traceCount++;
   }else if(p.id.endsWith('-intact')){
    body+=`<circle id="${p.id}" cx="${px(p.attrs.cx)}" cy="${py(p.attrs.cy)}" r="${mapping.endpoint_radius}" fill="${C.verdigris}"/>`;
    evidence.at(-1).primitives.push(p); successEndpointCount++;
   }
  }
 }
}
assert.equal(traceCount,1680);
assert.equal(successEndpointCount,aggregates.reduce((s,a)=>s+a.successes,0));
body+=line(72,1425,1528,1425,C.ink,2);
body+=text(72,1501,'Every mark is a measurement.',64,'Anton');
body+=`<circle cx="82" cy="1548" r="6" fill="${C.verdigris}"/>`;
body+=text(100,1557,'SUCCESS',25);
body+=`<path d="M290,1548h24m10,0h16" stroke="${C.oxide}" stroke-width="3"/>`;
body+=text(355,1557,'FAILURE',25);
body+=text(1528,1557,'Strict-output microtasks / 3 repeats',25,'IBM Plex Mono',C.ink,'text-anchor="end"');
const provenance={format:'major-minor/launch-graphic@1.0',plate:'001',dimensions:{width:1600,height:1600},visual_version:spec.visualVersion,renderer_version:spec.rendererVersion,experiment:dataset.experiment,synthetic:false,aggregates,trace_count:traceCount,success_endpoint_count:successEndpointCount,task_order:dataset.units.map(u=>u.id),simplification:{...mapping,description:'Dedicated row composition, all 80 tasks and 3 repeats per condition. Existing frozen unitScene geometry projected with shared affine scales. Uniform optical stroke/endpoint sizes; no random or invented damage. Task labels and cell registrations omitted. Original latency, throughput, envelope, displacement and categorical fracture geometry retained.'},wordmark:{major_font_size:56,minor_font_size:39.2,minor_to_major:.7,font:'Anton'},fonts:fontFiles.map(p=>({file:p.split('/').at(-1),sha256:hash(readFileSync(p))})),sources:['normalized.json','results.json','raw/trials.jsonl','plate-spec.json'].map(p=>({file:p,sha256:hash(readFileSync(study+p))})),frozen_geometry:{file:'src/scene.ts',sha256:hash(readFileSync(root+'src/scene.ts'))},evidence};
const metadata=`<metadata id="major-minor-launch-manifest">${esc(JSON.stringify(provenance))}</metadata>`;
const style=`<style>@font-face{font-family:Anton;src:url(data:font/ttf;base64,${readFileSync(fontFiles[0]).toString('base64')})} @font-face{font-family:'IBM Plex Mono';src:url(data:font/ttf;base64,${readFileSync(fontFiles[1]).toString('base64')})}</style>`;
const accessible=`<title>Plate 001 — Qwen3-8B Base: 1,680 real trials</title><desc>${esc(aggregates.map(a=>`${a.condition}: ${a.display_rate}, ${a.successes} of ${a.trials} successes`).join('; '))}. Every mark is a measurement. All 80 tasks appear in the same row-major order for each condition, with three measured traces per task.</desc>`;
const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1600" viewBox="0 0 1600 1600" role="img">${accessible}${metadata}<defs>${style}</defs>${body}</svg>`;
const renderer=new Resvg(svg,{font:fontOptions});
assert.equal(renderer.width,1600); assert.equal(renderer.height,1600);
// resvg's normalized SVG outlines the exact bundled font glyphs for portable display.
const outlined=renderer.toString().replace('<defs/>',`${accessible}${metadata}<defs/>`);
assert.ok(!outlined.includes('<text '));
assert.ok(outlined.includes('major-minor-launch-manifest'));
const base='plate-001-launch-1600';
writeFileSync(out+base+'.editable.svg',svg);
writeFileSync(out+base+'.svg',outlined);
const image=new Resvg(outlined,{font:{loadSystemFonts:false}}).render();
assert.equal(image.width,1600); assert.equal(image.height,1600);
writeFileSync(out+base+'.png',image.asPng());
for(const width of [400,360]) writeFileSync(out+`qa/${base}-${width}.png`,new Resvg(outlined,{fitTo:{mode:'width',value:width},font:{loadSystemFonts:false}}).render().asPng());
writeFileSync(out+'validation.json',JSON.stringify({format:provenance.format,dimensions:provenance.dimensions,checks:{real_ledger_normalized_results_agree:true,all_1680_trials_rendered:true,no_missing_outcomes:true,all_80_tasks_same_order:true,three_repeats_each_task_condition:true,shared_geometry_projection:true,seven_exact_rates:true,minor_70_percent_major:true,fonts_outlined:true},aggregates,sources:provenance.sources,trace_count:traceCount,success_endpoint_count:successEndpointCount,outputs:[base+'.svg',base+'.png',base+'.editable.svg'].map(file=>({file,sha256:hash(readFileSync(out+file))})),visual_review:'pending'},null,2)+'\n');
console.log(JSON.stringify({out,aggregates,traceCount,successEndpointCount},null,2));
