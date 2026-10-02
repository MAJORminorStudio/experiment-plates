import { readFileSync } from 'node:fs';
import { parse } from 'csv-parse/sync';
import { Dataset, ERRORS, InputBundle, METRICS, Observation } from './types.js';
import { canonical, hash } from './util.js';
function assert(ok: unknown, message: string): asserts ok { if (!ok) throw new Error(message); }
function id(value: unknown, kind: string): asserts value is string { assert(typeof value === 'string' && /^[A-Za-z0-9_-]+$/.test(value), `${kind}: IDs must use letters, digits, _ or -`); }
export function normalize(raw: unknown): Dataset {
  assert(raw !== null && typeof raw === 'object', 'Expected a dataset object');
  const d = structuredClone(raw) as Dataset;
  assert(d.experiment && typeof d.experiment.title === 'string' && typeof d.experiment.model === 'string', 'experiment.title and experiment.model required');
  id(d.experiment.id, 'experiment');
  assert(Number.isInteger(d.experiment.repeats) && d.experiment.repeats > 0 && d.experiment.repeats <= 5, 'v0.1 supports 1..5 repeats');
  assert(typeof d.experiment.synthetic === 'boolean' && typeof d.experiment.description === 'string', 'experiment.synthetic and description required');
  assert(Array.isArray(d.conditions) && d.conditions.length > 0 && Array.isArray(d.units) && d.units.length > 0 && d.units.length <= 20, 'Require conditions and 1..20 units');
  for (const [key, list, label] of [['condition', d.conditions, 'label'], ['unit', d.units, 'name']] as const) {
    const ids = new Set<string>();
    for (const entry of list) {
      id(entry.id, key); assert(!ids.has(entry.id), `Duplicate ${key}: ${entry.id}`); ids.add(entry.id);
      assert(typeof (entry as unknown as Record<string, unknown>)[label] === 'string', `${key}.${label} required`);
    }
  }
  assert(canonical(d.metrics) === canonical(METRICS), 'metrics must declare the five canonical metrics with correct units/types');
  assert(Array.isArray(d.observations), 'observations required');
  const slots = new Map<string, Observation>(); const ids = new Set<string>();
  for (const o of d.observations) {
    id(o.id, 'observation'); assert(!ids.has(o.id), `Duplicate observation ID: ${o.id}`); ids.add(o.id);
    assert(d.conditions.some(c => c.id === o.condition) && d.units.some(u => u.id === o.unit), `Unknown condition/unit in ${o.id}`);
    assert(Number.isInteger(o.run) && o.run >= 1 && o.run <= d.experiment.repeats, `Invalid run in ${o.id}`);
    const key = `${o.condition}/${o.unit}/${o.run}`; assert(!slots.has(key), `Duplicate slot: ${key}`);
    assert(o.success === true || o.success === false || o.success === null, `success must be boolean or null: ${o.id}`);
    for (const metric of ['latency_ms', 'tokens_per_second', 'memory_gb'] as const) {
      assert(o[metric] === null || (typeof o[metric] === 'number' && Number.isFinite(o[metric]) && o[metric]! >= 0), `Invalid ${metric}: ${o.id}`);
    }
    assert(o.error_category === null || ERRORS.includes(o.error_category), `Unknown error_category: ${o.id}`);
    assert(o.success !== true || o.error_category === null, `Successful run cannot have error_category: ${o.id}`);
    assert(o.success !== null || o.error_category === null, `Missing outcome cannot have error_category: ${o.id}`);
    slots.set(key, o);
  }
  d.observations = d.conditions.flatMap(c => d.units.flatMap(u => Array.from({ length: d.experiment.repeats }, (_, i) => {
    const key = `${c.id}/${u.id}/${i + 1}`;
    const o = slots.get(key);
    if (o) return { id: o.id, condition: o.condition, unit: o.unit, run: o.run, success: o.success, latency_ms: o.latency_ms, tokens_per_second: o.tokens_per_second, memory_gb: o.memory_gb, error_category: o.error_category };
    const missingId = `missing-${c.id}-${u.id}-${i + 1}`;
    assert(!ids.has(missingId), `Generated missing-slot ID conflicts: ${missingId}`);
    return { id: missingId, condition: c.id, unit: u.id, run: i + 1, success: null, latency_ms: null, tokens_per_second: null, memory_gb: null, error_category: null };
  })));
  return d;
}
const numeric = (s: string, key: string) => { if (s === '' || s === 'NA' || s === 'null') return null; const n = Number(s); assert(Number.isFinite(n), `CSV invalid ${key}: ${s}`); return n; };
export function fromCsv(source: string): Dataset {
  const rows = parse(source, { columns: true, skip_empty_lines: true, bom: true }) as Record<string, string>[];
  assert(rows.length > 0, 'CSV has no rows');
  const required = ['experiment_id', 'experiment_title', 'model', 'repeats', 'synthetic', 'description', 'condition', 'condition_label', 'condition_order', 'unit', 'unit_name', 'unit_order', 'observation_id', 'run', 'success', 'latency_ms', 'tokens_per_second', 'memory_gb', 'error_category'];
  assert(required.every(k => k in rows[0]), `CSV columns required: ${required.join(',')}`);
  const conditions = new Map<string, { id: string; label: string; order: number }>();
  const units = new Map<string, { id: string; name: string; order: number }>();
  const r = rows[0];
  for (const row of rows) {
    for (const k of ['experiment_id', 'experiment_title', 'model', 'repeats', 'synthetic', 'description']) assert(row[k] === r[k], `Inconsistent CSV ${k}`);
    for (const [map, key, label, order] of [[conditions, 'condition', 'condition_label', 'condition_order'], [units, 'unit', 'unit_name', 'unit_order']] as const) {
      assert(Number.isInteger(Number(row[order])) && Number(row[order]) >= 0, `Invalid ${order}`);
      const previous = map.get(row[key]);
      assert(!previous || (previous.order === Number(row[order]) && ('label' in previous ? previous.label : previous.name) === row[label]), `Inconsistent CSV ${key}`);
    }
    conditions.set(row.condition, { id: row.condition, label: row.condition_label, order: Number(row.condition_order) });
    units.set(row.unit, { id: row.unit, name: row.unit_name, order: Number(row.unit_order) });
  }
  assert(new Set([...conditions.values()].map(c => c.order)).size === conditions.size, 'Duplicate condition_order');
  assert(new Set([...units.values()].map(u => u.order)).size === units.size, 'Duplicate unit_order');
  assert(r.synthetic === 'true' || r.synthetic === 'false', 'CSV synthetic must be true or false');
  return normalize({
    experiment: { id: r.experiment_id, title: r.experiment_title, model: r.model, repeats: Number(r.repeats), synthetic: r.synthetic === 'true', description: r.description },
    conditions: [...conditions.values()].sort((a, b) => a.order - b.order).map(({ id, label }) => ({ id, label })),
    units: [...units.values()].sort((a, b) => a.order - b.order).map(({ id, name }) => ({ id, name })), metrics: METRICS,
    observations: rows.map(row => {
      assert(['true', 'false', '', 'NA', 'null'].includes(row.success), `CSV invalid success: ${row.success}`);
      return { id: row.observation_id, condition: row.condition, unit: row.unit, run: Number(row.run), success: row.success === 'true' ? true : row.success === 'false' ? false : null,
        latency_ms: numeric(row.latency_ms, 'latency_ms'), tokens_per_second: numeric(row.tokens_per_second, 'tokens_per_second'), memory_gb: numeric(row.memory_gb, 'memory_gb'), error_category: row.error_category || null };
    }),
  });
}
export function bundle(source: Buffer, csv = false): InputBundle {
  const data = csv ? fromCsv(source.toString('utf8')) : normalize(JSON.parse(source.toString('utf8')));
  return { data, sourceBase64: source.toString('base64'), sourceHash: hash(source), normalizedHash: hash(canonical(data)) };
}
export function readInput(path: string): InputBundle { return bundle(readFileSync(path), path.toLowerCase().endsWith('.csv')); }
