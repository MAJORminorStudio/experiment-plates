import { InputBundle, MAPPINGS, PlateSpec, RENDERER_VERSION, VISUAL_VERSION } from './types.js';
import { canonical } from './util.js';
export function makeSpec(input: string, bundle: InputBundle): PlateSpec {
  const max = (metric: 'latency_ms' | 'tokens_per_second' | 'memory_gb', step: number) => Math.max(step, Math.ceil(Math.max(0, ...bundle.data.observations.map(o => o[metric] ?? 0)) / step) * step);
  return { format: 'major-minor/plate-spec@0.1', input, sourceHash: bundle.sourceHash, normalizedHash: bundle.normalizedHash,
    rendererVersion: RENDERER_VERSION, visualVersion: VISUAL_VERSION, seed: 17017,
    dimensions: { width: 960, height: 1260 },
    scales: { latency_ms: [0, max('latency_ms', 5000)], tokens_per_second: [0, max('tokens_per_second', 10)], memory_gb: [0, max('memory_gb', 1)] }, mappings: MAPPINGS };
}
export function validateSpec(spec: PlateSpec, bundle: InputBundle): void {
  if (spec.format !== 'major-minor/plate-spec@0.1' || spec.rendererVersion !== RENDERER_VERSION || spec.visualVersion !== VISUAL_VERSION) throw new Error('Unsupported spec/renderer/visual version');
  if (spec.sourceHash !== bundle.sourceHash || spec.normalizedHash !== bundle.normalizedHash) throw new Error('Input hashes changed; run plate init again');
  if (!Number.isSafeInteger(spec.seed) || spec.seed < 0) throw new Error('Seed must be a nonnegative safe integer');
  if (canonical(spec.mappings) !== canonical(MAPPINGS)) throw new Error('v0.1 has one locked mapping grammar');
  const expected = makeSpec(spec.input, bundle);
  if (canonical(spec.scales) !== canonical(expected.scales)) throw new Error('Scales must be shared across the complete dataset; run plate init');
  if (canonical(spec.dimensions) !== canonical(expected.dimensions)) throw new Error('v0.1 uses a fixed 960 × 1260 frame');
}
