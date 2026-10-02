import { mkdirSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { Dataset, ErrorCategory, METRICS } from './types.js';
import { round } from './util.js';
// Seeded generator only creates source observations; the renderer contains no randomness.
function rng(seed: number) { let x = seed >>> 0; return () => { x += 0x6D2B79F5; let t = Math.imul(x ^ x >>> 15, 1 | x); t ^= t + Math.imul(t ^ t >>> 7, 61 | t); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
export function synthetic(seed = 20261001): Dataset {
  const random = rng(seed);
  const names = ['Instruction following', 'Structured output / JSON', 'Tool selection', 'Tool arguments', 'Multi-step planning', 'State tracking', 'Context retention', 'Error recovery', 'Web navigation', 'File operations', 'Code generation', 'Code execution', 'Data analysis', 'Mathematical reasoning', 'Information synthesis', 'Long-context QA', 'Multi-tool workflow', 'Constraint following', 'Ambiguous instruction', 'Completion judgment'];
  const fragility = [.25, .68, .29, .65, .94, .79, .76, .83, .55, .23, .70, .58, .84, .97, .47, .96, .98, .69, .88, .45];
  const categories: ErrorCategory[] = ['instruction', 'schema', 'tool_selection', 'tool_arguments', 'planning', 'state_loss', 'state_loss', 'planning', 'tool_selection', 'tool_arguments', 'execution', 'execution', 'reasoning', 'reasoning', 'reasoning', 'state_loss', 'planning', 'instruction', 'instruction', 'planning'];
  const conditionIds = ['FP16', 'Q8_0', 'Q6_K', 'Q5_K_M', 'Q4_K_M', 'Q3_K_M', 'Q2_K'];
  const throughput = [32, 45, 54, 63, 74, 92, 113];
  const memory = [16.8, 9.2, 7.1, 6.1, 5.2, 4.2, 3.35];
  const pressure = [0, .004, .018, .095, .245, .44, .72];
  const d: Dataset = {
    experiment: { id: 'mm-qwen3-8b-quant-001', title: 'Capability under compression', model: 'Qwen3-8B', repeats: 5, synthetic: true,
      description: `Synthetic illustration, not a Qwen benchmark. Generator seed ${seed}; five independent outcome draws per task and condition. Assumes fixed workload/token budgets, matched runtime, and identical task definitions. Memory includes runtime overhead. No real hardware or model was evaluated.` },
    conditions: conditionIds.map(id => ({ id, label: id })), units: names.map((name, i) => ({ id: `task-${String(i + 1).padStart(3, '0')}`, name })), metrics: METRICS, observations: [],
  };
  d.conditions.forEach((c, ci) => d.units.forEach((u, ui) => {
    for (let run = 1; run <= 5; run++) {
      // Lower precision raises task-dependent failure risk, with stochastic local reversals.
      const failureRisk = Math.min(.97, .005 + fragility[ui] * .014 + pressure[ci] * (.35 + 1.0 * fragility[ui]));
      const success = random() >= failureRisk;
      const timeout = !success && random() < .10;
      const tps = throughput[ci] * (.88 + random() * .24) * (1 - .10 * fragility[ui]);
      const tokenBudget = 330 + ui * 23 + (ui % 4) * 120;
      const retries = !success ? .78 + random() * .8 : .90 + random() * .22;
      const latency = timeout ? 45000 : tokenBudget / tps * 1000 * retries + 1400 + random() * 1600;
      d.observations.push({ id: `${c.id}-${u.id}-r${run}`, condition: c.id, unit: u.id, run, success,
        latency_ms: Math.round(latency), tokens_per_second: round(tps), memory_gb: round(memory[ci] + .1 + random() * .45 + (ui >= 15 ? .42 : 0)), error_category: success ? null : timeout ? 'timeout' : categories[ui] });
    }
  }));
  return d;
}
export function toCsv(d: Dataset): string {
  const headers = ['experiment_id', 'experiment_title', 'model', 'repeats', 'synthetic', 'description', 'condition', 'condition_label', 'condition_order', 'unit', 'unit_name', 'unit_order', 'observation_id', 'run', 'success', 'latency_ms', 'tokens_per_second', 'memory_gb', 'error_category'];
  const escape = (v: unknown) => { const s = v === null ? '' : String(v); return /[",\n\r]/.test(s) ? '"' + s.replaceAll('"', '""') + '"' : s; };
  return [headers.join(','), ...d.observations.map(o => {
    const c = d.conditions.find(c => c.id === o.condition)!; const u = d.units.find(u => u.id === o.unit)!;
    return [d.experiment.id, d.experiment.title, d.experiment.model, d.experiment.repeats, d.experiment.synthetic, d.experiment.description, c.id, c.label, d.conditions.indexOf(c), u.id, u.name, d.units.indexOf(u), o.id, o.run, o.success, o.latency_ms, o.tokens_per_second, o.memory_gb, o.error_category].map(escape).join(',');
  })].join('\n') + '\n';
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  mkdirSync('examples', { recursive: true }); const d = synthetic();
  writeFileSync('examples/qwen3-8b.synthetic.json', JSON.stringify(d, null, 2) + '\n');
  writeFileSync('examples/qwen3-8b.synthetic.csv', toCsv(d));
  console.log('Wrote 700 synthetic observations in canonical JSON and long CSV.');
}
