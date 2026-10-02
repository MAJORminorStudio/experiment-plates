import { COLORS as C, Dataset, Evidence, Observation, PlateSpec, Primitive, Scene, UnitGroup } from './types.js';
import { mean, median, round } from './util.js';
export const GRID = { x: 42, y: 364, columns: 4, cellWidth: 219, cellHeight: 143 };
export const FRACTURES: Record<string, [number, number][]> = {
  instruction: [[.48, .63]], schema: [[.31, .37], [.61, .67]],
  tool_selection: [[.23, .45]], tool_arguments: [[.47, .62], [.73, .78]],
  planning: [[.31, .44], [.61, .75]], state_loss: [[.54, .77]],
  reasoning: [[.37, .53]], timeout: [[.72, .94]], execution: [[.22, .31], [.48, .65]], other: [[.43, .59]],
};
export function summarize(obs: Observation[]) {
  const known = obs.filter(o => o.success !== null);
  return { successes: known.filter(o => o.success).length, observed: known.length, total: obs.length,
    latency: median(obs.map(o => o.latency_ms)), throughput: median(obs.map(o => o.tokens_per_second)), memory: median(obs.map(o => o.memory_gb)),
    failures: known.filter(o => o.success === false).length, missing: obs.length - known.length };
}
const ev = (condition: string, observations: Observation[], unit?: string, derived?: Evidence['derived']): Evidence => ({ condition, ...(unit ? { unit } : {}), runs: observations.map(o => o.run), observationIds: observations.map(o => o.id), ...(derived ? { derived } : {}) });
function primitive(id: string, tag: Primitive['tag'], attrs: Primitive['attrs'], text?: string, evidence?: Evidence, channels: Primitive['channels'] = []): Primitive {
  return { id, tag, attrs, ...(text !== undefined ? { text } : {}), role: evidence ? 'data' : 'structure', channels, ...(evidence ? { evidence } : {}) };
}
export const label = (id: string, x: number, y: number, text: string, size = 11, evidence?: Evidence, display = false, fill: string = C.ink): Primitive => primitive(id, 'text', { x, y, 'font-family': display ? 'Anton' : 'IBM Plex Mono', 'font-size': size, fill, 'letter-spacing': display ? 0 : .3 }, text, evidence, evidence ? ['summary'] : []);
export const line = (id: string, x1: number, y1: number, x2: number, y2: number, stroke: string = C.ink, width = 1): Primitive => primitive(id, 'line', { x1, y1, x2, y2, stroke, 'stroke-width': width });
const f = (n: number | null, decimals = 1) => n === null ? 'NA' : n.toFixed(decimals);
function wrapName(name: string): string[] {
  const words = name.toUpperCase().split(' '); const lines: string[] = [''];
  for (const word of words) { const last = lines.length - 1; if ((lines[last] + ' ' + word).trim().length > 24 && lines[last]) lines.push(word); else lines[last] = (lines[last] + ' ' + word).trim(); }
  return lines;
}
/** The pulse trace is the sole data grammar. Every subpath is derived from an observation. */
export function tracePath(x: number, y: number, length: number, pulses: number, failed: boolean, category: string): string {
  const cuts = failed ? FRACTURES[category] ?? FRACTURES.other : [];
  // Break boundaries and pulse shoulders are all in normalized horizontal coordinates.
  const coords = new Set([0, 1, ...cuts.flat()]);
  for (let i = 1; i <= pulses; i++) {
    const t = i / (pulses + 1); const shoulder = Math.min(.018, .24 / (pulses + 1));
    coords.add(t - shoulder); coords.add(t); coords.add(t + shoulder);
  }
  const points = [...coords].sort((a, b) => a - b);
  const height = (t: number) => {
    for (let i = 1; i <= pulses; i++) {
      const peak = i / (pulses + 1), shoulder = Math.min(.018, .24 / (pulses + 1));
      if (Math.abs(t - peak) <= shoulder + 1e-9) return -3 * Math.max(0, 1 - Math.abs(t - peak) / shoulder);
    }
    return 0;
  };
  let path = ''; let open = false;
  for (let i = 0; i < points.length; i++) {
    const t = points[i]; const visible = i === 0 || !cuts.some(([a, b]) => (t + points[i - 1]) / 2 > a && (t + points[i - 1]) / 2 < b);
    if (!visible) { open = false; continue; }
    if (!open) {
      const start = i > 0 ? points[i - 1] : t;
      path += `M${round(x + start * length)},${round(y + height(start))}`;
    }
    path += `L${round(x + t * length)},${round(y + height(t))}`; open = true;
  }
  return path;
}
function diamond(x: number, y: number, radius: number) { return `M${x},${y - radius}L${x + radius},${y}L${x},${y + radius}L${x - radius},${y}Z`; }
export function unitScene(d: Dataset, spec: PlateSpec, condition: string, unitId: string, index: number): UnitGroup {
  const unit = d.units.find(u => u.id === unitId)!;
  const observations = d.observations.filter(o => o.condition === condition && o.unit === unitId);
  const sum = summarize(observations); const groupId = `${condition}-${unitId}`;
  const primitives: Primitive[] = [];
  const unitEvidence = ev(condition, observations, unitId);
  primitives.push(label(`${groupId}-number`, 0, 13, String(index + 1).padStart(3, '0'), 13, unitEvidence));
  primitives.push(label(`${groupId}-count`, 168, 13, `${sum.successes}/${sum.observed}`, 11, ev(condition, observations, unitId, { successes: sum.successes, observed: sum.observed })));
  wrapName(unit.name).forEach((part, i) => primitives.push(label(`${groupId}-name-${i}`, 0, 30 + i * 12, part, 9, unitEvidence)));
  primitives.push(line(`${groupId}-registration`, 0, 49, 199, 49, C.ink, .45));
  const memory = mean(observations.map(o => o.memory_gb));
  const envelope = memory === null ? 24 : 24 + 48 * memory / spec.scales.memory_gb[1];
  const center = 91;
  // Memory extent is a bracket as well as the vertical occupied envelope; missing memory is not zero.
  const resource = ev(condition, observations, unitId, { mean_memory_gb: memory, envelope_px: memory === null ? null : round(envelope) });
  primitives.push(primitive(`${groupId}-envelope`, 'path', { d: memory === null ? diamond(199, center, 4) : `M196,${round(center - envelope / 2)}h3v${round(envelope)}h-3`, fill: 'none', stroke: C.ink, 'stroke-width': .65 }, undefined, resource, ['resource', 'missing']));
  const missingMetrics: Record<string, number[]> = { S: [], L: [], T: [], M: [] };
  observations.forEach((o, i) => {
    const y = center + (i - (d.experiment.repeats - 1) / 2) * envelope / Math.max(1, d.experiment.repeats - 1);
    const displacement = o.latency_ms === null || sum.latency === null ? 0 : .15 * envelope / Math.max(1, d.experiment.repeats - 1) * (o.latency_ms - sum.latency) / spec.scales.latency_ms[1];
    const baseline = round(y + displacement);
    const length = o.latency_ms === null ? null : 183 * o.latency_ms / spec.scales.latency_ms[1];
    const pulses = o.tokens_per_second === null ? null : Math.floor(o.tokens_per_second / 10);
    const evidence = ev(condition, [o], unitId, { length_px: length === null ? null : round(length), pulses, displacement_px: o.latency_ms === null ? null : round(displacement), error_morphology: o.success === false ? o.error_category ?? 'other' : null });
    const stroke = o.success === false ? C.oxide : C.ink;
    if (o.success === null || length === null) {
      primitives.push(primitive(`${groupId}-run-${o.run}-missing`, 'path', { d: diamond(8, baseline, 3.2), fill: 'none', stroke: C.ink, 'stroke-width': 1.1 }, undefined, evidence, ['position', 'missing', 'variance', 'resource']));
      // Numeric latency missing while outcome known: encode known integrity in a separate status mark.
      if (o.success !== null) primitives.push(primitive(`${groupId}-run-${o.run}-status`, 'circle', { cx: 18, cy: baseline, r: 1.8, fill: o.success ? C.verdigris : C.oxide }, undefined, evidence, ['integrity', 'color']));
    } else {
      primitives.push(primitive(`${groupId}-run-${o.run}-trace`, 'path', { d: tracePath(1, baseline, length, pulses ?? 0, o.success === false, o.error_category ?? 'other'), fill: 'none', stroke, 'stroke-width': 1.15, 'stroke-linecap': 'butt', 'stroke-linejoin': 'miter' }, undefined, evidence, ['position', 'latency', 'throughput', 'integrity', 'variance', 'resource', 'error', 'color']));
      if (o.success) primitives.push(primitive(`${groupId}-run-${o.run}-intact`, 'circle', { cx: round(1 + length), cy: baseline, r: 1.65, fill: C.verdigris }, undefined, evidence, ['latency', 'integrity', 'color', 'variance', 'resource']));
      if (pulses === null) primitives.push(primitive(`${groupId}-run-${o.run}-throughput-missing`, 'path', { d: diamond(1 + round(length) / 2, baseline, 3.2), fill: C.bone, stroke: C.ink, 'stroke-width': 1 }, undefined, evidence, ['missing', 'latency', 'resource', 'variance']));
    }
    if (o.memory_gb === null) missingMetrics.M.push(o.run);
    if (o.latency_ms === null) missingMetrics.L.push(o.run);
    if (o.tokens_per_second === null) missingMetrics.T.push(o.run);
    if (o.success === null) missingMetrics.S.push(o.run);
  });
  if (Object.values(missingMetrics).some(runs => runs.length)) primitives.push(label(`${groupId}-missing-label`, 0, 137, `NA ${Object.entries(missingMetrics).filter(([, runs]) => runs.length).map(([metric, runs]) => metric + ':' + runs.join('')).join(' ')}`, 7, unitEvidence));
  return { id: groupId, condition, unit: unitId, x: GRID.x + (index % GRID.columns) * GRID.cellWidth, y: GRID.y + Math.floor(index / GRID.columns) * GRID.cellHeight, primitives };
}
export function buildScene(d: Dataset, spec: PlateSpec, condition: string): Scene {
  const conditionEntry = d.conditions.find(c => c.id === condition);
  if (!conditionEntry) throw new Error(`Unknown condition: ${condition}`);
  const obs = d.observations.filter(o => o.condition === condition); const s = summarize(obs);
  const evidence = ev(condition, obs); const frame: Primitive[] = [];
  const add = (p: Primitive) => frame.push(p);
  add(primitive(`${condition}-background`, 'rect', { x: 0, y: 0, width: 960, height: 1260, fill: C.bone }));
  add(label(`${condition}-brand`, 42, 62, 'MAJOR//MINOR', 40, undefined, true));
  add(label(`${condition}-plate`, 598, 45, `EXPERIMENT PLATE / ${String(d.conditions.findIndex(c => c.id === condition) + 1).padStart(3, '0')}`, 12));
  add(label(`${condition}-version-top`, 598, 64, `STROKE GRAMMAR ${spec.visualVersion} / ${d.experiment.synthetic ? 'SYNTHETIC' : 'MEASURED'}`, 10));
  add(line(`${condition}-header-rule`, 42, 85, 918, 85, C.ink, 1.5));
  add(label(`${condition}-model`, 42, 116, d.experiment.model.toUpperCase(), 12, evidence));
  const title = d.experiment.title.toUpperCase();
  add(label(`${condition}-title`, 42, 170, title, Math.min(48, 850 / (title.length * .56)), evidence, true));
  add(label(`${condition}-condition`, 42, 275, conditionEntry.label, 86, evidence, true));
  add(label(`${condition}-series-position`, 710, 211, `CONDITION ${String(d.conditions.findIndex(c => c.id === condition) + 1).padStart(2, '0')} / ${String(d.conditions.length).padStart(2, '0')}`, 11, evidence));
  add(label(`${condition}-dimensions`, 710, 233, `${d.units.length} TASKS × ${d.experiment.repeats} RUNS`, 11, evidence));
  add(label(`${condition}-coverage`, 710, 255, `${s.observed}/${s.total} OUTCOMES`, 11, evidence));
  const metrics = [
    ['SUCCESS / OBSERVED', s.observed ? `${(100 * s.successes / s.observed).toFixed(0)}%` : 'NA', `${s.successes}/${s.observed} · ${s.missing} MISSING`],
    ['MEDIAN LATENCY', `${f(s.latency === null ? null : s.latency / 1000)}s`, `${obs.filter(o => o.latency_ms !== null).length}/${s.total} MEASURED`],
    ['MEDIAN THROUGHPUT', f(s.throughput), 'TOKENS / SECOND'],
    ['MEDIAN MEMORY', `${f(s.memory)}GB`, 'RESIDENT FOOTPRINT'],
  ];
  metrics.forEach(([name, value, detail], i) => {
    const x = 42 + i * 219;
    add(line(`${condition}-metric-rule-${i}`, x, 290, x + 199, 290, C.ink, .7));
    add(label(`${condition}-metric-label-${i}`, x, 308, name, 9));
    add(label(`${condition}-metric-value-${i}`, x, 340, value, 28, evidence, true));
    add(label(`${condition}-metric-detail-${i}`, x + (i === 0 ? 70 : 87), 337, detail, 7, evidence));
  });
  add(line(`${condition}-grid-rule`, 42, 353, 918, 353, C.ink, 1.2));
  add(line(`${condition}-footer-rule`, 42, 1095, 918, 1095, C.ink, 1.2));
  add(label(`${condition}-reading`, 42, 1120, 'READ THE TRACES', 14, undefined, true));
  add(label(`${condition}-key-1`, 42, 1141, 'POSITION = TASK   /   EACH TRACE = ONE RUN   /   BREAK = FAILURE', 10));
  add(label(`${condition}-key-2`, 42, 1159, 'LENGTH = LATENCY   /   PULSES = THROUGHPUT   /   ENVELOPE = MEMORY', 10));
  add(label(`${condition}-key-3`, 42, 1177, 'OPEN DIAMOND = MISSING   /   SHARED SCALES ACROSS EVERY CONDITION', 10));
  add(label(`${condition}-scale`, 42, 1206, `DOMAINS  L 0–${spec.scales.latency_ms[1] / 1000}s  /  T 0–${spec.scales.tokens_per_second[1]} tok/s  /  M 0–${spec.scales.memory_gb[1]}GB`, 9));
  add(label(`${condition}-hash`, 42, 1231, `${spec.normalizedHash.slice(0, 12)}  /  VISUAL ${spec.visualVersion}  /  SEED ${spec.seed}`, 9));
  add(label(`${condition}-footer-brand`, 739, 1231, 'MAJOR//MINOR', 18, undefined, true));
  return { condition, width: 960, height: 1260, frame, units: d.units.map((u, i) => unitScene(d, spec, condition, u.id, i)) };
}
