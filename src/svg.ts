import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { Resvg } from '@resvg/resvg-js';
import { COLORS as C, InputBundle, Manifest, PlateSpec, Primitive, RENDERER_VERSION, Scene, VISUAL_VERSION } from './types.js';
import { canonical, hash, unxml, xml } from './util.js';
import { buildScene, label, line, summarize } from './scene.js';
import { bundle } from './input.js';
import { validateSpec } from './spec.js';
export const fontPaths = {
  Anton: fileURLToPath(new URL('../../assets/fonts/Anton-Regular.ttf', import.meta.url)),
  'IBM Plex Mono': fileURLToPath(new URL('../../assets/fonts/IBMPlexMono-Regular.ttf', import.meta.url)),
};
export function fonts() {
  const bytes = Object.fromEntries(Object.entries(fontPaths).map(([name, path]) => [name, readFileSync(path)]));
  return { hashes: Object.fromEntries(Object.entries(bytes).map(([name, b]) => [name, hash(b)])),
    css: Object.entries(bytes).map(([name, b]) => `@font-face{font-family:'${name}';src:url(data:font/ttf;base64,${b.toString('base64')}) format('truetype');font-weight:400;font-style:normal;}`).join('') };
}
export function renderPrimitive(p: Primitive, prefix = ''): string {
  const evidence = p.evidence;
  const attrs = { id: prefix + p.id, 'data-primitive': p.id, 'data-role': p.role, ...(evidence ? { 'data-condition': evidence.condition, ...(evidence.unit ? { 'data-unit': evidence.unit } : {}) } : {}), ...p.attrs };
  const attributes = Object.entries(attrs).map(([k, v]) => `${k}="${xml(v)}"`).join(' ');
  return p.tag === 'text' ? `<text ${attributes}>${xml(p.text)}</text>` : `<${p.tag} ${attributes}/>`;
}
export function renderUnit(scene: Scene, unitId: string, x?: number, y?: number, scale = 1, prefix = ''): string {
  const u = scene.units.find(u => u.unit === unitId)!;
  return `<g id="${prefix + u.id}" data-unit="${xml(u.unit)}" data-condition="${xml(u.condition)}" transform="translate(${x ?? u.x} ${y ?? u.y}) scale(${scale})">${u.primitives.map(p => renderPrimitive(p, prefix)).join('')}</g>`;
}
function sceneBody(scene: Scene): string { return scene.frame.map(p => renderPrimitive(p)).join('') + scene.units.map(u => renderUnit(scene, u.unit)).join(''); }
const background = (w: number, h: number) => `<rect id="composition-background" data-role="structure" x="0" y="0" width="${w}" height="${h}" fill="${C.bone}"/>`;
function contactBody(scenes: Scene[], input: InputBundle, spec: PlateSpec): { body: string; primitives: Primitive[] } {
  const d = input.data;
  const allEvidence = { condition: 'series', runs: [], observationIds: d.observations.map(o => o.id) };
  const heading = [label('sheet-brand', 60, 70, 'MAJOR//MINOR', 42, undefined, true), label('sheet-label', 1470, 57, `EXPERIMENT PLATES / 001–${String(d.conditions.length).padStart(3, '0')}`, 18), label('sheet-evidence', 1470, 86, `${d.experiment.synthetic ? 'SYNTHETIC STUDY' : 'MEASURED STUDY'} / ${d.observations.length} RUN SLOTS / VISUAL ${spec.visualVersion}`, 13),
    line('sheet-header-rule', 60, 108, 2338, 108, C.ink, 2), label('sheet-title', 60, 213, d.experiment.title.toUpperCase(), 102, undefined, true), label('sheet-subtitle', 63, 246, `${d.experiment.model.toUpperCase()}  /  IDENTICAL TASK POSITIONS · FIVE RUNS PER TASK · ONE SHARED SCALE`, 16)];
  const plates = scenes.map((s, i) => `<g transform="translate(${60 + (i % 4) * 580} ${280 + Math.floor(i / 4) * 744}) scale(.56)">${sceneBody(s)}</g>`).join('');
  const keyX = 1800, keyY = 1024;
  const key = [label('key-title', keyX + 20, keyY + 53, 'A CAPABILITY HAS AN ADDRESS.', 31, undefined, true),
    label('key-subtitle', keyX + 20, keyY + 88, `FOLLOW TASK ${String(Math.min(17, d.units.length)).padStart(3, '0')} THROUGH THE SERIES.`, 12), line('key-rule', keyX + 20, keyY + 109, keyX + 525, keyY + 109, C.ink, 1),
    label('key-fp', keyX + 20, keyY + 145, `${d.conditions[0].label} / ${d.units[16]?.name.toUpperCase() ?? d.units[0].name.toUpperCase()}`, 13), label('key-q2', keyX + 20, keyY + 339, `${d.conditions.at(-1)!.label} / ${d.units[16]?.name.toUpperCase() ?? d.units[0].name.toUpperCase()}`, 13),
    label('key-encoding-title', keyX + 20, keyY + 535, 'THE STROKE IS THE RECORD.', 29, undefined, true),
    label('key-encoding-1', keyX + 20, keyY + 565, 'Length   → latency', 13), label('key-encoding-2', keyX + 20, keyY + 589, 'Pulses   → tokens per second', 13), label('key-encoding-3', keyX + 20, keyY + 613, 'Envelope → memory in GB', 13), label('key-encoding-4', keyX + 20, keyY + 637, 'Fracture → failed run / error category', 13),
    label('key-encoding-5', keyX + 20, keyY + 661, 'Diamond  → missing, never failure', 13), label('key-disclaimer', keyX + 20, keyY + 701, d.experiment.synthetic ? 'GENERATED DATA. NOT A MODEL BENCHMARK.' : 'ALL MARKS LINK TO SOURCE OBSERVATIONS.', 11)];
  const task = d.units[16]?.id ?? d.units[0].id;
  for (const p of [...heading, ...key]) { if (['sheet-title','sheet-subtitle','sheet-evidence','key-subtitle','key-fp','key-q2'].includes(p.id)) { p.role = 'data'; p.channels = ['summary']; p.evidence = allEvidence; } }
  for (const [id, condition] of [['key-fp', scenes[0].condition], ['key-q2', scenes.at(-1)!.condition]]) {
    const p = key.find(p => p.id === id)!; const obs = d.observations.filter(o => o.condition === condition && o.unit === task);
    p.evidence = { condition, unit: task, runs: obs.map(o => o.run), observationIds: obs.map(o => o.id) };
  }
  const samples = renderUnit(scenes[0], task, keyX + 20, keyY + 153, 1.32, 'legend-fp-') + renderUnit(scenes[scenes.length - 1], task, keyX + 20, keyY + 347, 1.32, 'legend-q2-');
  const foot = [line('sheet-footer-rule', 60, 1781, 2338, 1781, C.ink, 2), label('sheet-footer', 60, 1818, `SOURCE ${spec.sourceHash.slice(0, 12)} / NORMALIZED ${spec.normalizedHash.slice(0, 12)} / SEED ${spec.seed}`, 13), label('sheet-footer-right', 1660, 1818, 'SAME TASKS. DIFFERENT OUTCOMES.', 25, undefined, true)];
  return { body: background(2400, 1860) + heading.map(p => renderPrimitive(p)).join('') + plates + key.map(p => renderPrimitive(p)).join('') + samples + foot.map(p => renderPrimitive(p)).join(''), primitives: [...heading, ...key, ...foot] };
}
function heroBody(scenes: Scene[], input: InputBundle, spec: PlateSpec): { body: string; primitives: Primitive[] } {
  const d = input.data;
  const allEvidence = { condition: 'series', runs: [], observationIds: d.observations.map(o => o.id) };
  const task = d.units[16]?.id ?? d.units[0].id;
  const header = [label('hero-brand', 64, 77, 'MAJOR//MINOR', 48, undefined, true), label('hero-identifier', 1530, 54, 'EXPERIMENT PLATE / 001', 16), label('hero-synthetic', 1530, 81, `${d.experiment.synthetic ? 'SYNTHETIC STUDY' : 'MEASURED STUDY'} / VISUAL ${spec.visualVersion}`, 13), line('hero-header', 64, 113, 2336, 113, C.ink, 2),
    label('hero-title-1', 64, 265, 'WHAT SURVIVES', 112, undefined, true), label('hero-title-2', 64, 410, 'COMPRESSION?', 112, undefined, true), label('hero-model', 69, 464, `${d.experiment.model.toUpperCase()} / ${d.conditions[0].label} → ${d.conditions.at(-1)!.label}`, 20),
    label('hero-body-1', 69, 523, `${d.units.length} tasks. ${d.experiment.repeats} runs. Fixed positions.`, 18), label('hero-body-2', 69, 554, 'Each fracture names a failed run.', 18), label('hero-body-3', 69, 585, 'Each pulse records throughput.', 18),
    label('hero-note', 69, 665, d.experiment.synthetic ? 'ILLUSTRATIVE DATA / NO MODEL WAS EVALUATED' : 'EVIDENCE-LINKED MARKS / SHARED SCALES', 14),
    line('hero-divider', 64, 847, 2336, 847, C.ink, 2), label('hero-detail-title', 64, 906, 'FOLLOW A SINGLE CAPABILITY', 44, undefined, true),
    label('hero-detail-subtitle', 67, 944, `${d.units.find(u => u.id === task)!.name.toUpperCase()} / SAME ADDRESS IN EVERY CONDITION`, 15),
    line('hero-footer-rule', 64, 1410, 2336, 1410, C.ink, 2), label('hero-footer', 64, 1450, `${d.observations.length} ${d.experiment.synthetic ? 'SYNTHETIC' : 'MEASURED'} RUN SLOTS / NORMALIZED ${spec.normalizedHash.slice(0, 12)} / GRAMMAR ${spec.visualVersion}`, 13), label('hero-footer-brand', 1975, 1454, 'MAJOR//MINOR', 35, undefined, true)];
  const plates = scenes.map((s, i) => `<g transform="translate(${848 + i * 493} 155) scale(.495)">${sceneBody(s)}</g>`).join('');
  for (const p of header) { if (['hero-model','hero-body-1','hero-note','hero-detail-subtitle','hero-footer','hero-synthetic'].includes(p.id)) { p.role = 'data'; p.channels = ['summary']; p.evidence = allEvidence; } }
  const detailPrimitives: Primitive[] = [];
  const details = scenes.map((s, i) => {
    const x = 67 + i * 770; const summary = summarize(d.observations.filter(o => o.condition === s.condition && o.unit === task));
    const title = [label(`hero-detail-${i}-condition`, x, 1008, s.condition, 43, undefined, true), label(`hero-detail-${i}-stat`, x + 270, 1006, `${summary.successes}/${summary.observed} RUNS INTACT`, 17)];
    for (const p of title) { p.role = 'data'; p.channels = ['summary']; p.evidence = { condition: s.condition, unit: task, runs: Array.from({ length: d.experiment.repeats }, (_, i) => i + 1), observationIds: d.observations.filter(o => o.condition === s.condition && o.unit === task).map(o => o.id), derived: { successes: summary.successes, observed: summary.observed } }; }
    detailPrimitives.push(...title);
    return title.map(p => renderPrimitive(p)).join('') + renderUnit(s, task, x, 1030, 2.75, `detail-${i}-`);
  }).join('');
  return { body: background(2400, 1500) + header.map(p => renderPrimitive(p)).join('') + plates + details, primitives: [...header, ...detailPrimitives] };
}
export function bodyFor(kind: Manifest['kind'], scenes: Scene[], input: InputBundle, spec: PlateSpec): string {
  const defs = `<defs><style>${fonts().css}</style></defs>`;
  return defs + (kind === 'plate' ? sceneBody(scenes[0]) : kind === 'contact-sheet' ? contactBody(scenes, input, spec).body : heroBody(scenes, input, spec).body);
}
export function createArtifact(input: InputBundle, spec: PlateSpec, kind: Manifest['kind'] = 'plate', condition?: string): { svg: string; manifest: Manifest } {
  validateSpec(spec, input);
  const conditions = kind === 'plate' ? [condition ?? input.data.conditions[0].id] : kind === 'hero' ? [...new Set([input.data.conditions[0].id, input.data.conditions[Math.floor(input.data.conditions.length * .65)].id, input.data.conditions.at(-1)!.id])] : input.data.conditions.map(c => c.id);
  // This fixed contact-sheet composition supports up to seven conditions.
  if (kind !== 'plate' && input.data.conditions.length > 7) throw new Error('v0.1 compositions support up to seven conditions; individual plates are available');
  const scenes = conditions.map(c => buildScene(input.data, spec, c));
  const dimensions = kind === 'plate' ? spec.dimensions : kind === 'hero' ? { width: 2400, height: 1500 } : { width: 2400, height: 1860 };
  const body = bodyFor(kind, scenes, input, spec);
  const compositionPrimitives = kind === 'plate' ? [] : (kind === 'contact-sheet' ? contactBody(scenes, input, spec) : heroBody(scenes, input, spec)).primitives;
  const manifest: Manifest = {
    format: 'major-minor/artifact@0.1', kind, experimentId: input.data.experiment.id, sourceHash: input.sourceHash, normalizedHash: input.normalizedHash,
    specHash: hash(canonical(spec)), rendererVersion: RENDERER_VERSION, visualVersion: VISUAL_VERSION, seed: spec.seed, dimensions,
    condition: kind === 'plate' ? conditions[0] : conditions, mappings: spec.mappings, bodyHash: hash(body), sceneHash: hash(canonical({ scenes, compositionPrimitives })), fontHashes: fonts().hashes,
    sourceBase64: input.sourceBase64, normalizedData: input.data, spec, scenes, compositionPrimitives,
  };
  const svg = `<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="${dimensions.width}" height="${dimensions.height}" viewBox="0 0 ${dimensions.width} ${dimensions.height}" role="img" aria-labelledby="artifact-title artifact-description"><title id="artifact-title">${xml(input.data.experiment.title)} / ${xml(conditions.join(' → '))}</title><desc id="artifact-description">${xml(input.data.experiment.synthetic ? 'Synthetic illustration, not measured model performance. ' : '')}${input.data.units.length} stable task addresses, one stroke per run. Embedded provenance and source observations.</desc><metadata id="major-minor-manifest">${xml(canonical(manifest))}</metadata>\n${body}\n</svg>\n`;
  return { svg, manifest };
}
export function rasterize(svg: string, width?: number): Buffer {
  const r = new Resvg(svg, { font: { fontFiles: Object.values(fontPaths), loadSystemFonts: false, defaultFontFamily: 'IBM Plex Mono' }, ...(width ? { fitTo: { mode: 'width' as const, value: width } } : {}) });
  return r.render().asPng();
}
export function readManifest(svg: string): Manifest {
  const match = svg.match(/<metadata id="major-minor-manifest">([\s\S]*?)<\/metadata>/);
  if (!match) throw new Error('No MAJOR//MINOR provenance metadata in SVG');
  return JSON.parse(unxml(match[1])) as Manifest;
}
export function verify(svg: string): string[] {
  const m = readManifest(svg); const checks: string[] = [];
  const check = (ok: boolean, name: string) => { if (!ok) throw new Error(`Verification failed: ${name}`); checks.push(name); };
  check(m.format === 'major-minor/artifact@0.1' && ['plate', 'contact-sheet', 'hero'].includes(m.kind), 'manifest format');
  const source = Buffer.from(m.sourceBase64, 'base64');
  const input = bundle(source, source.toString('utf8').trimStart()[0] !== '{');
  check(input.sourceHash === m.sourceHash, 'source hash');
  check(input.normalizedHash === m.normalizedHash && hash(canonical(m.normalizedData)) === m.normalizedHash, 'normalized dataset hash');
  check(hash(canonical(m.spec)) === m.specHash, 'spec hash');
  check(m.rendererVersion === RENDERER_VERSION && m.visualVersion === VISUAL_VERSION, 'renderer and visual versions');
  check(m.seed === m.spec.seed, 'seed'); validateSpec(m.spec, input);
  check(canonical(m.mappings) === canonical(m.spec.mappings), 'declared mappings');
  check(canonical(m.fontHashes) === canonical(fonts().hashes), 'bundled font hashes');
  check(m.experimentId === m.normalizedData.experiment.id, 'experiment identity');
  check(hash(canonical({ scenes: m.scenes, compositionPrimitives: m.compositionPrimitives })) === m.sceneHash, 'scene hash');
  const body = svg.match(/<\/metadata>\n([\s\S]*)\n<\/svg>\n$/)?.[1];
  check(body !== undefined && hash(body) === m.bodyHash, 'rendered body hash');
  const fresh = createArtifact(input, m.spec, m.kind, typeof m.condition === 'string' ? m.condition : undefined);
  check(canonical(fresh.manifest) === canonical(m), 'manifest consistency and scene derivation');
  check(fresh.svg === svg, 'deterministic complete rerender');
  const primitiveIds = [...svg.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
  check(new Set(primitiveIds).size === primitiveIds.length, 'unique SVG IDs');
  return checks;
}
