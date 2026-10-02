#!/usr/bin/env node
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, isAbsolute, relative, resolve } from 'node:path';
import { readInput } from './input.js';
import { makeSpec, validateSpec } from './spec.js';
import { writeArtifact, writeSeries } from './outputs.js';
import { readManifest, verify } from './svg.js';
import { summarize } from './scene.js';
import { PlateSpec } from './types.js';
const help = `MAJOR//MINOR / PLATE v0.1
plate init <input.json|input.csv> [--out spec.json]
plate render <spec.json> [--condition FP16] [--out outputs] [--no-png]
plate series <spec.json> [--out outputs] [--no-png]
plate inspect <artifact.svg> [primitive-or-unit]
plate verify <artifact.svg>
SVG is canonical. Use --help to print this message.`;
try {
  const args = process.argv.slice(2); const command = args.shift();
  if (!command || command === '--help' || command === '-h') { console.log(help); process.exit(0); }
  const target = args.shift(); if (!target || target.startsWith('--')) throw new Error('Input path required');
  const options = new Map<string, string>(); const positional: string[] = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--no-png') options.set('no-png', 'true');
    else if (args[i] === '--out' || args[i] === '--condition') { const key = args[i].slice(2); const value = args[++i]; if (!value || value.startsWith('--')) throw new Error(`Missing --${key} value`); options.set(key, value); }
    else if (args[i].startsWith('--')) throw new Error(`Unknown option ${args[i]}`);
    else positional.push(args[i]);
  }
  if (command === 'init') {
    const input = readInput(target); const out = resolve(options.get('out') ?? target.replace(/\.(json|csv)$/i, '') + '.plate.json');
    const spec = makeSpec(relative(dirname(out), resolve(target)), input); mkdirSync(dirname(out), { recursive: true }); writeFileSync(out, JSON.stringify(spec, null, 2) + '\n'); console.log(out);
  } else if (command === 'render' || command === 'series') {
    const spec = JSON.parse(readFileSync(target, 'utf8')) as PlateSpec;
    const input = readInput(isAbsolute(spec.input) ? spec.input : resolve(dirname(resolve(target)), spec.input));
    validateSpec(spec, input); const out = resolve(options.get('out') ?? 'outputs');
    if (command === 'render') { const condition = options.get('condition') ?? input.data.conditions[0].id; writeArtifact(input, spec, out, condition, !options.has('no-png')); console.log(`${out}/${condition}.svg`); }
    else { const index = writeSeries(input, spec, out, !options.has('no-png')); console.log(`Wrote ${index.conditions.length} plates, contact sheet, hero, inspector, and provenance to ${out}`); }
  } else if (command === 'inspect') {
    const svg = readFileSync(target, 'utf8'); const m = readManifest(svg); const selector = positional[0];
    if (!selector) console.log(JSON.stringify({ experimentId: m.experimentId, kind: m.kind, condition: m.condition, sourceHash: m.sourceHash, normalizedHash: m.normalizedHash, specHash: m.specHash, rendererVersion: m.rendererVersion, visualVersion: m.visualVersion, seed: m.seed, dimensions: m.dimensions, mappings: m.mappings }, null, 2));
    else {
      const primitives = [...m.compositionPrimitives, ...m.scenes.flatMap(s => [...s.frame, ...s.units.flatMap(u => u.primitives)])];
      const instance = [...svg.matchAll(/\bid="([^"]+)" data-primitive="([^"]+)"/g)].find(match => match[1] === selector);
      const sourceId = instance?.[2] ?? selector;
      const p = primitives.find(p => p.id === sourceId);
      const group = [...svg.matchAll(/<g id="([^"]+)" data-unit="([^"]+)" data-condition="([^"]+)"/g)].find(match => match[1] === selector);
      const units = m.scenes.flatMap(s => s.units).filter(u => u.unit === selector || u.id === selector || (group && u.unit === group[2] && u.condition === group[3]));
      if (p) console.log(JSON.stringify({ primitive: p, observations: m.normalizedData.observations.filter(o => p.evidence?.observationIds.includes(o.id)) }, null, 2));
      else if (units.length) console.log(JSON.stringify(units.map(u => { const observations = m.normalizedData.observations.filter(o => o.condition === u.condition && o.unit === u.unit); return { condition: u.condition, unit: m.normalizedData.units.find(unit => unit.id === u.unit), position: { x: u.x, y: u.y }, summary: summarize(observations), observations, primitiveIds: u.primitives.map(p => p.id) }; }), null, 2));
      else throw new Error(`Unknown primitive or unit: ${selector}`);
    }
  } else if (command === 'verify') { const checks = verify(readFileSync(target, 'utf8')); console.log(`VERIFIED / ${checks.length} checks\n${checks.join('\n')}`); }
  else throw new Error(`Unknown command: ${command}`);
} catch (error) { console.error(`plate: ${error instanceof Error ? error.message : String(error)}`); process.exitCode = 1; }
