import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { InputBundle, Manifest, PlateSpec } from './types.js';
import { createArtifact, rasterize } from './svg.js';
import { inspector } from './inspector.js';
import { canonical, hash } from './util.js';
export function writeArtifact(input: InputBundle, spec: PlateSpec, out: string, condition?: string, png = true, kind: Manifest['kind'] = 'plate') {
  mkdirSync(out, { recursive: true });
  const artifact = createArtifact(input, spec, kind, condition);
  const name = kind === 'plate' ? condition ?? input.data.conditions[0].id : kind;
  writeFileSync(join(out, `${name}.svg`), artifact.svg);
  if (png) writeFileSync(join(out, `${name}.png`), rasterize(artifact.svg));
  return artifact;
}
export function writeSeries(input: InputBundle, spec: PlateSpec, out: string, png = true) {
  const artifacts = input.data.conditions.map(c => writeArtifact(input, spec, out, c.id, png));
  const contact = writeArtifact(input, spec, out, undefined, png, 'contact-sheet');
  const hero = writeArtifact(input, spec, out, undefined, png, 'hero');
  writeFileSync(join(out, 'inspector.html'), inspector(input, spec, artifacts.map(a => a.manifest)));
  writeFileSync(join(out, 'normalized.json'), JSON.stringify(input.data, null, 2) + '\n');
  const index = { format: 'major-minor/series@0.1', experimentId: input.data.experiment.id, sourceHash: input.sourceHash, normalizedHash: input.normalizedHash, specHash: hash(canonical(spec)), conditions: input.data.conditions.map(c => c.id), artifacts: [...artifacts, contact, hero].map(a => ({ file: `${a.manifest.kind === 'plate' ? a.manifest.condition : a.manifest.kind}.svg`, svgHash: hash(a.svg), bodyHash: a.manifest.bodyHash })) };
  writeFileSync(join(out, 'series-manifest.json'), JSON.stringify(index, null, 2) + '\n');
  return index;
}
