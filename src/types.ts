export const RENDERER_VERSION = '0.1.0';
export const VISUAL_VERSION = '0.1';
export const COLORS = { bone: '#E7DFCC', ink: '#0A0A08', verdigris: '#3DA887', oxide: '#D9643A' } as const;
export const METRICS = {
  success: { type: 'boolean', unit: 'boolean' },
  latency_ms: { type: 'number', unit: 'ms' },
  tokens_per_second: { type: 'number', unit: 'tokens/s' },
  memory_gb: { type: 'number', unit: 'GB' },
  error_category: { type: 'category', unit: 'category' },
} as const;
export const ERRORS = ['instruction', 'schema', 'tool_selection', 'tool_arguments', 'planning', 'state_loss', 'reasoning', 'timeout', 'execution', 'other'] as const;
export type ErrorCategory = typeof ERRORS[number];
export interface Observation {
  id: string; condition: string; unit: string; run: number;
  success: boolean | null; latency_ms: number | null; tokens_per_second: number | null;
  memory_gb: number | null; error_category: ErrorCategory | null;
}
export interface Dataset {
  experiment: { id: string; title: string; model: string; repeats: number; synthetic: boolean; description: string };
  conditions: { id: string; label: string }[];
  units: { id: string; name: string }[];
  metrics: typeof METRICS;
  observations: Observation[];
}
export interface InputBundle { data: Dataset; sourceBase64: string; sourceHash: string; normalizedHash: string; }
export const MAPPINGS = {
  position: 'unit array order; row-major fixed 4-column grid',
  integrity: 'one trace per run; intact=true, fractured=false, open diamond=null',
  latency: 'linear path horizontal extent, 0..series maximum rounded up to 5000 ms',
  throughput: 'floor(tokens_per_second / 10) pulses; pulses equally spaced on the trace',
  resource: 'mean observed memory_gb sets five-run envelope; 24 + 48 * GB / shared maximum',
  variance: 'run latency minus unit/condition median; displacement = 0.15 * lane spacing * difference / shared latency maximum',
  error: 'declared category selects a fixed fracture mask; unclassified failures use other',
  color: 'successful trace=ink, successful endpoint=verdigris, failed trace=oxide, missing=ink',
  missing: 'open diamond for missing outcome; metric-specific open markers for missing numeric channels',
  summary: 'observed-success ratio; medians exclude missing values; coverage reported explicitly',
} as const;
export interface PlateSpec {
  format: 'major-minor/plate-spec@0.1'; input: string; sourceHash: string; normalizedHash: string;
  rendererVersion: string; visualVersion: string; seed: number;
  dimensions: { width: 960; height: 1260 };
  scales: { latency_ms: [number, number]; tokens_per_second: [number, number]; memory_gb: [number, number] };
  mappings: typeof MAPPINGS;
}
export interface Evidence {
  condition: string; unit?: string; runs: number[]; observationIds: string[];
  derived?: Record<string, number | string | boolean | null>;
}
export interface Primitive {
  id: string; tag: 'path' | 'line' | 'rect' | 'circle' | 'text';
  attrs: Record<string, string | number>; text?: string;
  role: 'structure' | 'data'; channels: (keyof typeof MAPPINGS)[]; evidence?: Evidence;
}
export interface UnitGroup {
  id: string; condition: string; unit: string; x: number; y: number; primitives: Primitive[];
}
export interface Scene { condition: string; width: number; height: number; frame: Primitive[]; units: UnitGroup[]; }
export interface Manifest {
  format: 'major-minor/artifact@0.1'; kind: 'plate' | 'contact-sheet' | 'hero';
  experimentId: string; sourceHash: string; normalizedHash: string; specHash: string;
  rendererVersion: string; visualVersion: string; seed: number;
  dimensions: { width: number; height: number }; condition: string | string[];
  mappings: typeof MAPPINGS; bodyHash: string; sceneHash: string; fontHashes: Record<string, string>;
  sourceBase64: string; normalizedData: Dataset; spec: PlateSpec; scenes: Scene[]; compositionPrimitives: Primitive[];
}
