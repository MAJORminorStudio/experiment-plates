import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { bundle, fromCsv, normalize, readInput } from '../src/input.js';
import { makeSpec, validateSpec } from '../src/spec.js';
import { buildScene, FRACTURES, summarize, tracePath } from '../src/scene.js';
import { createArtifact, rasterize, readManifest, verify } from '../src/svg.js';
import { synthetic, toCsv } from '../src/synthetic.js';
import { canonical, hash } from '../src/util.js';
import { COLORS, MAPPINGS } from '../src/types.js';
const data = synthetic(); const input = bundle(Buffer.from(JSON.stringify(data))); const spec = makeSpec('fixture.json', input);

test('700 atomic runs, plausible early reliability, improvements in speed and memory, local reversals', () => {
  assert.equal(data.observations.length, 700);
  const stats = data.conditions.map(c => summarize(data.observations.filter(o => o.condition === c.id)));
  assert(stats.slice(0, 3).every(s => s.successes >= 94));
  assert(stats[3].successes >= 80 && stats[3].successes < stats[2].successes);
  assert(stats[4].successes < stats[3].successes && stats[5].successes < stats[4].successes && stats[6].successes < 30);
  assert(stats.every((s, i) => !i || s.throughput! > stats[i - 1].throughput! && s.memory! < stats[i - 1].memory!));
  assert(data.units.some(u => data.conditions.some((c, i) => i && summarize(data.observations.filter(o => o.unit === u.id && o.condition === c.id)).successes > summarize(data.observations.filter(o => o.unit === u.id && o.condition === data.conditions[i - 1].id)).successes)));
});
test('CSV and JSON normalize to the identical dataset; source hashes retain original bytes', () => {
  assert.equal(canonical(fromCsv(toCsv(data))), canonical(normalize(data)));
  assert.notEqual(bundle(Buffer.from(toCsv(data)), true).sourceHash, input.sourceHash);
  assert.equal(bundle(Buffer.from(toCsv(data)), true).normalizedHash, input.normalizedHash);
});
test('observation row shuffle does not change normalized data or scene geometry', () => {
  const reversed = structuredClone(data); reversed.observations.reverse();
  const shuffled = bundle(Buffer.from(JSON.stringify(reversed)));
  assert.equal(shuffled.normalizedHash, input.normalizedHash);
  assert.equal(canonical(buildScene(shuffled.data, spec, 'FP16')), canonical(buildScene(input.data, spec, 'FP16')));
});
test('renderer is deterministic and does not call Math.random; stable PNG on this runtime', () => {
  const old = Math.random; Math.random = () => { throw new Error('Renderer used randomness'); };
  try {
    const a = createArtifact(input, spec, 'plate', 'FP16'), b = createArtifact(input, spec, 'plate', 'FP16');
    assert.equal(a.svg, b.svg); const png = rasterize(a.svg);
    assert.equal(hash(png), hash(rasterize(b.svg))); assert.equal(png.readUInt32BE(16), 960); assert.equal(png.readUInt32BE(20), 1260);
  } finally { Math.random = old; }
});
test('all seven conditions share fixed unit positions and scales', () => {
  const scenes = data.conditions.map(c => buildScene(input.data, spec, c.id));
  for (const s of scenes) assert.deepEqual(s.units.map(u => [u.unit, u.x, u.y]), scenes[0].units.map(u => [u.unit, u.x, u.y]));
  assert.deepEqual(scenes[0].units[16], scenes[0].units.find(u => u.unit === 'task-017'));
  for (const c of data.conditions) assert.deepEqual(createArtifact(input, spec, 'plate', c.id).manifest.spec.scales, spec.scales);
  const changed = structuredClone(spec); changed.scales.latency_ms[1] /= 2;
  assert.throws(() => validateSpec(changed, input), /shared/);
});
test('quantization names do not directly alter data geometry', () => {
  const d = structuredClone(data); const fp = d.observations.filter(o => o.condition === 'FP16');
  d.observations = d.observations.map(o => o.condition === 'Q2_K' ? { ...fp.find(a => a.unit === o.unit && a.run === o.run)!, condition: 'Q2_K', id: o.id } : o);
  const normalized = normalize(d); const a = buildScene(normalized, spec, 'FP16'), b = buildScene(normalized, spec, 'Q2_K');
  assert.deepEqual(a.units.map(u => u.primitives.map(p => [p.tag, p.attrs, p.text])), b.units.map(u => u.primitives.map(p => [p.tag, p.attrs, p.text])));
});
test('every data primitive declares mappings and links to observations with correct units/runs', () => {
  for (const c of data.conditions) {
    const scene = buildScene(input.data, spec, c.id);
    for (const p of [...scene.frame, ...scene.units.flatMap(u => u.primitives)]) {
      assert(p.channels.every(channel => channel in MAPPINGS));
      if (p.role === 'data') {
        assert(p.channels.length > 0 && p.evidence && p.evidence.observationIds.length > 0, p.id);
        const evidence = p.evidence!;
        for (const id of evidence.observationIds) {
          const o = input.data.observations.find(o => o.id === id)!; assert(o, p.id);
          assert.equal(o.condition, evidence.condition); if (evidence.unit) assert.equal(o.unit, evidence.unit);
          assert(evidence.runs.includes(o.run));
        }
        if (p.evidence?.derived && 'length_px' in p.evidence.derived && p.tag === 'path' && !p.id.includes('missing')) assert(p.channels.includes('latency'));
      } else { assert(!p.evidence); assert.equal(p.channels.length, 0); }
    }
  }
});
test('latency sensitivity changes only affected task traces while fixed positions stay intact', () => {
  const changed = structuredClone(input.data); changed.observations.find(o => o.id === 'FP16-task-001-r1')!.latency_ms! += 1000;
  const a = buildScene(input.data, spec, 'FP16'), b = buildScene(changed, spec, 'FP16');
  assert.notEqual(a.units[0].primitives.find(p => p.id.endsWith('run-1-trace'))!.attrs.d, b.units[0].primitives.find(p => p.id.endsWith('run-1-trace'))!.attrs.d);
  assert.deepEqual(a.units.slice(1), b.units.slice(1)); assert.deepEqual(a.units.map(u => [u.x, u.y]), b.units.map(u => [u.x, u.y]));
});
test('missing outcomes and missing numeric metrics are visible and never counted as failure/zero', () => {
  const changed = structuredClone(data); const o = changed.observations[0]; o.success = null; o.error_category = null; o.latency_ms = null; o.tokens_per_second = null; o.memory_gb = null;
  const normalized = normalize(changed); const scene = buildScene(normalized, spec, 'FP16'); const glyph = scene.units[0];
  const marker = glyph.primitives.find(p => p.id.endsWith('run-1-missing'))!;
  assert.equal(marker.attrs.fill, 'none'); assert.equal(marker.attrs.stroke, COLORS.ink);
  assert(!glyph.primitives.some(p => p.id.endsWith('run-1-trace')));
  assert(glyph.primitives.some(p => p.id.endsWith('missing-label') && p.text!.includes('S:1')));
  assert.equal(summarize(normalized.observations.filter(o => o.condition === 'FP16' && o.unit === 'task-001')).missing, 1);
  changed.observations.splice(0, 1); assert.equal(normalize(changed).observations[0].success, null);
  const metricMissing = structuredClone(data); metricMissing.observations[0].tokens_per_second = null;
  assert(buildScene(normalize(metricMissing), spec, 'FP16').units[0].primitives.some(p => p.id.endsWith('throughput-missing')));
});
test('distinct category fracture masks and continuous success paths', () => {
  assert.equal(new Set(Object.values(FRACTURES).map(canonical)).size, Object.keys(FRACTURES).length);
  assert.equal((tracePath(0, 0, 100, 5, false, 'planning').match(/M/g) ?? []).length, 1);
  assert.equal((tracePath(0, 0, 100, 5, true, 'planning').match(/M/g) ?? []).length, 3);
});
test('reject duplicate slots, bad metrics, invalid outcomes and inconsistent CSV declarations', () => {
  const dupe = structuredClone(data); dupe.observations.push({ ...dupe.observations[0], id: 'duplicate' }); assert.throws(() => normalize(dupe), /Duplicate slot/);
  const bad = structuredClone(data); bad.observations[0].latency_ms = NaN; assert.throws(() => normalize(bad), /Invalid latency/);
  bad.observations[0].latency_ms = -1; assert.throws(() => normalize(bad), /Invalid latency/);
  bad.observations[0].latency_ms = 100; bad.observations[0].error_category = 'planning'; assert.throws(() => normalize(bad), /Successful run/);
  assert.throws(() => fromCsv(toCsv(data).replace('"Qwen3-8B"', '"Different"').replace('Qwen3-8B,5', 'Different,5')), /Inconsistent CSV/);
});
test('SVG manifests verify source, scene, seed, mappings and complete markup; tampering fails', () => {
  for (const kind of ['plate', 'contact-sheet', 'hero'] as const) {
    const artifact = createArtifact(input, spec, kind, 'FP16'); assert.equal(verify(artifact.svg).length, 14);
    assert.equal(readManifest(artifact.svg).normalizedHash, input.normalizedHash);
    assert.throws(() => verify(artifact.svg.replace('fill="#E7DFCC"', 'fill="#ffffff"')), /body hash/);
    assert.throws(() => verify(artifact.svg.replace(/viewBox="0 0 [0-9]+ [0-9]+"/, 'viewBox="0 0 1 1"')), /rerender/);
  }
});
test('all flagship outputs match current source and verify successfully', () => {
  const source = readInput('examples/qwen3-8b.synthetic.json');
  const files = readdirSync('outputs').filter(f => f.endsWith('.svg')); assert.equal(files.length, 9);
  for (const f of files) { const svg = readFileSync(join('outputs', f), 'utf8'); assert.equal(readManifest(svg).normalizedHash, source.normalizedHash); verify(svg); }
});
test('CLI runs from a different working directory and resolves spec input relative to spec', () => {
  const dir = mkdtempSync(join(tmpdir(), 'mm-plate-')); const cli = join(process.cwd(), 'dist/src/cli.js');
  const run = (...args: string[]) => spawnSync(process.execPath, [cli, ...args], { cwd: dir, encoding: 'utf8' });
  try {
    writeFileSync(join(dir, 'source.csv'), toCsv(data)); const init = run('init', 'source.csv', '--out', 'spec.json'); assert.equal(init.status, 0, init.stderr);
    const render = run('render', 'spec.json', '--condition', 'Q2_K', '--out', 'exports', '--no-png'); assert.equal(render.status, 0, render.stderr);
    const check = run('verify', 'exports/Q2_K.svg'); assert.equal(check.status, 0, check.stderr);
    const inspect = run('inspect', 'exports/Q2_K.svg', 'Q2_K-task-017-run-1-trace'); assert.equal(inspect.status, 0, inspect.stderr);
    const output = JSON.parse(inspect.stdout); assert.equal(output.observations[0].condition, 'Q2_K'); assert.equal(output.observations[0].unit, 'task-017');
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
