#!/usr/bin/env python3
"""Write draft release copy from validated real results; never publish."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 r=json.loads((ROOT/'results.json').read_text());v=json.loads((ROOT/'validation.json').read_text());m=json.loads((ROOT/'experiment-manifest.json').read_text())
 by={e['condition']:e for e in r['conditions']};first=by['F16'];last=by['Q2_K'];point=r['first_meaningful_degradation']
 table='| Condition | Success | Decode tok/s | Prompt tok/s | Peak RSS GB | Model GB |\n| --- | ---: | ---: | ---: | ---: | ---: |\n'+''.join(f'| {e["condition"]} | {e["successes"]}/240 ({100*e["success_rate"]:.2f}%) | {e["controlled_generation_tokens_per_second"]:.2f} | {e["controlled_prompt_processing_tokens_per_second"]:.2f} | {(e["bench_peak_memory_bytes"] or 0)/1e9:.2f} | {e["model_bytes"]/1e9:.2f} |\n' for e in r['conditions'])
 category_table='| Capability | F16 | Q8 | Q6 | Q5 | Q4 | Q3 | Q2 |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n'+''.join('| '+category.replace('_',' ')+' | '+' | '.join(f'{e["successes"]}/24' for e in entries)+' |\n' for category,entries in r['capability_categories'].items())
 significant='The first condition meeting the predeclared exploratory degradation rule was **'+point+'**.' if point else 'No condition met the predeclared degradation rule; this study does not support a clean threshold claim.'
 q3=by['Q3_K_M'];q2ci=last['paired_drop_ci95'];q3ci=q3['paired_drop_ci95']
 significant+=f' Q3_K_M dropped {100*q3["paired_drop_vs_f16"]:.2f} points (95% paired interval {100*q3ci[0]:.2f} to {100*q3ci[1]:.2f}), crossing zero. Q2_K dropped {100*last["paired_drop_vs_f16"]:.2f} points (interval {100*q2ci[0]:.2f} to {100*q2ci[1]:.2f}).'
 significant+=' The rule required a drop of at least five percentage points versus F16 and a positive lower bound of a 95% paired task-cluster bootstrap interval.'
 category_points='; '.join(e['category'].replace('_',' ')+' at '+e['first_condition'] for e in r['category_first_exploratory_degradation'] if e['first_condition'] and not e['reference_floor']) or 'No category with a usable reference met the exploratory rule.'
 prefix_counts=r['output_discipline_diagnostic']['correct_initial_object_but_strict_failure_counts']
 output_discipline=f"Q2_K exhausted the generation budget in {last['error_flag_counts']['timeout_loop']}/240 trials. A post hoc diagnostic found {prefix_counts['Q2_K']}/240 Q2_K responses that began with an oracle-correct JSON object but still failed the strict whole-output contract or budget rule. These remain official failures. This separates loss of output discipline from an assumption that every failed answer began with incorrect task reasoning; it does not establish hidden reasoning quality. No stop sequence or prompt was changed for Q2_K."
 early=', '.join(t['task_id'] for t in r['unusually_early_failures']) or 'none under the fixed criterion';late=', '.join(t['task_id'] for t in r['unusually_late_robust_tasks']) or 'none under the fixed criterion'
 caveat='These are agent-relevant microtasks with proposed tools and explicit deterministic oracles. They do not measure autonomous agent success, real tool execution, broad knowledge, or maximum-length context retention. The model is Qwen3-8B **Base**, using one fixed few-shot completion prompt; it is not the instruction-tuned Qwen3 model. Three matched seeds were used for each task, with no automatic expansion to five repeats. Categories have only eight task variants each and are exploratory. Variants reuse ten templates; intervals resampling tasks do not account for dependence between variants within a template or generalize to all agent tasks.'
 floors=r['reference_floor_categories'];floor_text='Reference floor warning: '+', '.join(floors)+'. Quantization loss cannot be interpreted cleanly for categories already below 50% in F16.' if floors else 'No category was below 50% success in the F16 reference.'
 review_done=v.get('manual_failure_review')=='passed';artifacts_done=v.get('artifact_verification')=='passed'
 readiness='Ready as a scoped real capability study. Performance comparisons are descriptive: system swapping confounds isolated speed and total-memory claims.' if review_done and artifacts_done and first['success_rate']>=.5 else 'Publication readiness requires the remaining validation or explicit treatment of the reference floor; avoid a general agent-capability claim.'
 summary=f'''# What survives compression? A real Qwen3-8B Base microtask study

Draft for MAJOR//MINOR. Not published.

We ran **1,680 scored trials** on one Mac Studio M1 Max with 32 GB of unified memory: 80 tasks, three matched seeds, and seven GGUF precision conditions. All six quantizations were generated locally from one F16 reference converted from the same pinned official Base-model weights. Prompts, tool definitions, context size, sampling, generation budget and evaluation stayed constant.

F16 succeeded in **{first['successes']}/240** trials ({100*first['success_rate']:.1f}%). Q2_K succeeded in **{last['successes']}/240** ({100*last['success_rate']:.2f}%). {significant}

{table}

The task families cover structured JSON, tool selection and arguments, dependency plans, state and context retention, tool-error recovery, constraint following, completion judgment, and file-operation reasoning. Scorers were programmatic; no LLM judged the outputs.

{category_table}

First qualifying category losses, excluding reference-floor categories: {category_points}. These are exploratory signals with eight variants per category.

{output_discipline}

Under the fixed early-failure rule (F16 at least 2/3, Q8 or Q6 at most 1/3), the early task IDs were **{early}**. Under the late-robustness rule (F16 and Q2_K both at least 2/3), the robust task IDs were **{late}**. There were **{r['non_monotonic_task_count']} tasks with at least one adjacent-condition improvement**. These local reversals are retained in the ledger and plates rather than smoothed away; three seeds cannot establish that every reversal is a reproducible quantization advantage.

Observed llama-bench generation throughput at Q2_K was **{last['controlled_generation_gain_vs_f16']:.2f}× F16**. Model-file size fell by **{100*last['model_size_saving_vs_f16']:.1f}%**. Measured process RSS and the anomalously small native footprint counter are reported separately from model bytes; neither should be read as a complete accounting of all system or Metal allocations. Trial throughput is preserved but is not substituted for the controlled benchmark.

{floor_text}

The MAJOR//MINOR plates retain visual grammar 0.1. Four unchanged 20-task panels cover all 80 task addresses per condition, with global shared scales. Every trace corresponds to one measured run. Fractures identify scored failures; pulse density, path extent and memory envelopes derive from recorded measurements. The inspector exposes full outputs and provenance. No synthetic observations appear in this release.

{caveat}

VM snapshots recorded substantial system-wide swapping in the F16 and Q2_K intervals. F16 startup was unusually slow. Fixed condition order and the running desktop confound isolated performance claims; repeat the benchmark in a quiet session before generalizing the observed speed ratio. Benchmarks were serial and warmed; VM and thermal snapshots are archived. Category differences are exploratory and are not multiplicity-corrected. Reported paired intervals resample whole task clusters, keeping the three repeats together. Tasks were constructed programmatically; every released observation came from a real local inference request.

Validation: {v.get('status')}; manual review {v.get('manual_failure_review')}; artifact checks {v.get('artifact_verification')}. {readiness}

Reproduction, source revision, commands, exact model hashes, raw responses, scorer definitions and release artifacts are included locally. Nothing has been published automatically.
'''
 (ROOT/'research-summary.draft.md').write_text(summary)
 notes=f'''# Qwen3-8B Base precision study — release draft

- 80 deterministic agent-relevant microtasks, 3 matched runs, 7 common-source GGUF conditions: 1,680 real observations scored under a strict whole-output contract.
- Fixed Mac Studio M1 Max / 32 GB, llama.cpp Metal revision `{m['llama_revision']}`.
- F16 {100*first['success_rate']:.1f}% success; Q2_K {100*last['success_rate']:.2f}%. First qualifying degradation: {point or 'none'}.
- Observed Q2_K decode throughput {last['controlled_generation_gain_vs_f16']:.2f}× F16; {r['non_monotonic_task_count']} task-level local reversals retained. Desktop swapping confounds isolated speed and memory claims.
- Visual grammar 0.1 unchanged; four frozen panels per condition, contact sheet, hero, offline inspector, all SVG/PNG exports.
- Raw ledger, source/model hashes, scorer replay, controlled benchmarks and draft analysis included.
- Scope: Base-model microtasks, not autonomous agent or maximum-context performance. {floor_text}
- Draft only. No automatic publication.
'''
 (ROOT/'release-notes.draft.md').write_text(notes)
 x=f'''Qwen3-8B Base: 80 microtasks × 3 runs × 7 quants on M1 Max.
Strict success: F16 {100*first['success_rate']:.1f}% → Q2_K {100*last['success_rate']:.2f}%.
1,680 measured runs. No LLM judge.
Observed Q2 decode: {last['controlled_generation_gain_vs_f16']:.1f}× F16 (desktop swapping).
Simulated tools. Every fracture is a scored failure.
'''
 assert len(x)<=280,'X draft exceeds single-post limit'
 (ROOT/'x-post.draft.txt').write_text(x)
 storyboard=f'''# 26-second demo storyboard — draft

| Time | View | Caption / narration |
| --- | --- | --- |
| 0–4 s | Hero, hold on MAJOR//MINOR identity and Base-model label | “80 tasks. Seven precisions. Same M1 Max.” |
| 4–9 s | Contact sheet, pan F16 → Q2_K | “1,680 measured runs. Same prompts, tools, and three seeds.” |
| 9–15 s | Enlarge {r['hero_task_id']} in F16 and Q2_K | “One task keeps its address. Each fracture is one failed run.” |
| 15–21 s | Inspector, select a fractured trace and show raw output and scorer evidence | “Strict whole-output scoring. Inspect the exact run.” |
| 21–26 s | Return to hero / controlled benchmark table | “F16 {100*first['success_rate']:.1f}% vs Q2 {100*last['success_rate']:.2f}%. Scope: Base-model microtasks.” |

Use exported SVG/PNG and the real inspector. No fabricated animations or telemetry. Publication needs user approval.
'''
 (ROOT/'demo-storyboard.draft.md').write_text(storyboard)
 readme=f'''# MAJOR//MINOR real experiment 001 — Qwen3-8B Base

{readiness}

**Measured data only:** 80 tasks × 3 seeds × 7 conditions = **1,680 scored trials**. Ten calibration responses are archived separately. One neutral server warmup per condition is excluded from this denominator; its output is not part of the trial ledger. No synthetic observations are used. Model outputs are untrusted text; the harness never executes proposed tools, code or file operations.

{table}

{significant}

## Reproduce on the same Mac

From the repository root (requires the installed llama.cpp 0.4.1 binaries and ggml 0.24.0 recorded in `environment.json`):

```sh
cd {ROOT.parents[1]}
npm ci
npm run build
python3 -m venv studies/qwen3-8b-base-20261001/.venv
studies/qwen3-8b-base-20261001/.venv/bin/pip install -r studies/qwen3-8b-base-20261001/python-requirements.lock.txt
git init studies/qwen3-8b-base-20261001/runtime/llama.cpp
git -C studies/qwen3-8b-base-20261001/runtime/llama.cpp remote add origin https://github.com/ggml-org/llama.cpp.git
git -C studies/qwen3-8b-base-20261001/runtime/llama.cpp fetch --depth 1 origin {m['llama_revision']}
git -C studies/qwen3-8b-base-20261001/runtime/llama.cpp checkout --detach FETCH_HEAD
studies/qwen3-8b-base-20261001/.venv/bin/hf download Qwen/Qwen3-8B-Base --revision {m['source_revision']} --local-dir studies/qwen3-8b-base-20261001/weights
studies/qwen3-8b-base-20261001/.venv/bin/python studies/qwen3-8b-base-20261001/scripts/prepare.py
studies/qwen3-8b-base-20261001/.venv/bin/python studies/qwen3-8b-base-20261001/scripts/run.py --calibrate
studies/qwen3-8b-base-20261001/.venv/bin/python studies/qwen3-8b-base-20261001/scripts/run.py
studies/qwen3-8b-base-20261001/.venv/bin/python studies/qwen3-8b-base-20261001/scripts/analyze.py
node studies/qwen3-8b-base-20261001/scripts/export.mjs
node studies/qwen3-8b-base-20261001/scripts/export.mjs --verify
```

Preparation and inference must run serially. The preflight log records one aborted overlapping F16 startup before any scored trials; this was not counted as a model failure. A reference startup can take minutes when loading from external storage. The runner resumes an existing ledger only if the suite and scorer hashes match; for an independent replication, use a fresh study directory/ledger rather than mixing observations. Reproduction commands and server/benchmark arguments are also stored verbatim in the manifests.

## Input, renderer and evidence

`canonical-panels/part-1.json` through `part-4.json` conform to the unchanged canonical schema: each contains 20 tasks, all seven conditions and 420 atomic measured observations. `normalized.json` is their complete 80-task study view; it retains the canonical five sections but exceeds the original schema’s 20-unit limit and is validated as four partitions. The frozen renderer's 20-task input validation is applied per panel, and the study adapter retains 80 task IDs with common domains in one four-panel plate per condition. `plate-spec.json` records the global shared scales. No observation is aggregated into a replacement trial. A separate study artifact format records the composition; run `export.mjs --verify` for these composite manifests. The original `plate verify` remains appropriate for original 20-task artifacts.

`../../releases/visual-0.1.freeze.json` records exact renderer/schema/font/dependency source hashes. Export refuses a changed frozen source. No original renderer code or stroke grammar is modified. Pages and enlarged callouts reuse its scene builder and SVG primitives. The inspector uses the frozen evidence UI with all four panels available for each condition. Error categories map to the existing morphology via `error-category-mapping.json`; original detailed error flags remain in the ledger.

## Release files

- `raw/trials.jsonl`: append-only complete raw requests, native responses, model/prompt hashes, timing, sampled RSS, deterministic scores.
- `raw/trials.csv`: flat trial ledger with all requested error flags.
- `canonical-panels/part-{{1,2,3,4}}.json`: four datasets conforming to the frozen 20-unit canonical schema, 420 observations each.
- `normalized.json`, `plate-spec.json`: complete 80-task study view and shared-scale spec.
- `experiment-manifest.json`, `model-manifest.json`, `quantization-commands.json`, `environment.json`: exact parameters, model lineage, hashes, commands and environment.
- `task-suite.json`, `scoring-definitions.json`, `scripts/suite.py`: task text, oracle answers, deterministic scoring logic.
- `performance.json`, `raw/bench-*.json`, `raw/bench-*.log`: separate llama-bench pp256/tg64 measurements, three samples each, native process memory reports.
- `artifacts/{{F16,Q8_0,Q6_K,Q5_K_M,Q4_K_M,Q3_K_M,Q2_K}}.svg/.png`: seven complete 80-task condition plates.
- `artifacts/contact-sheet.svg/.png`: complete ordered series.
- `artifacts/hero.svg/.png`: real publication composition and observed task callout.
- `artifacts/inspector.html`: self-contained real-observation evidence inspector, no network requests.
- `artifacts/panels/`: 28 full-size frozen 20-task detail panels, SVG and PNG.
- `artifacts/verification.json`, `validation.json`, `manual-failure-review.json`: verification, scorer replay and direct failure inspection records.
- `results.json`: overall/category success, paired uncertainty, early/late tasks, reversals, errors, speed/memory tradeoffs.
- `research-summary.draft.md`, `release-notes.draft.md`, `x-post.draft.txt`, `demo-storyboard.draft.md`: unpublished release copy.

## Method and limits

{caveat}

{floor_text}

Source model: `Qwen/Qwen3-8B-Base@{m['source_revision']}`. Original BF16 safetensors are converted into one F16 GGUF reference; all six quantizations derive from that same reference. No importance matrix is used. F16 is therefore the common GGUF reference, not an assertion of bit-for-bit BF16 inference.

Every request's native generation settings are checked against the declared values. Scorers reject markdown, extra prose, duplicate keys, wrong JSON types/values, missing plan steps and invalid dependencies. A plan can use any valid topological order. Tool names and arguments are checked separately. Exhausting the generation budget fails conservatively under `timeout_loop`; this flag does not prove an actual tool loop. Tool recovery, completion and file operations are simulated reasoning judgments with deterministic expected answers.

Latency is request wall time; trial throughput comes from native generation timings. Controlled performance is measured separately. Plate memory envelopes use 20 Hz sampled process RSS; controlled `/usr/bin/time -l` reports both maximum RSS and peak process footprint where available. These are incomplete measures of total unified-memory/Metal/system occupancy. Model file bytes are reported independently. Thermal and VM snapshots are archived, and fixed sequential condition order/background desktop load remain limitations.

No automatic publication or additional repeats occurred. Category results are exploratory, and observed local reversals are not smoothed. Follow-up experiments must be driven by the observed anomalies, not an assumed monotonic story.

## Observed output-discipline anomaly

{output_discipline}

Specific follow-ups: repeat the performance tests in a quiet desktop session; compare F16, Q3_K_M and Q2_K using a newly predeclared, identical stopping policy that includes unprefixed next-example delimiters, with new independent task variants. Retain the current study unchanged so stopping behavior and task-answer correctness can be compared without retroactively rescuing Q2_K outputs. Calibrate state/constraint variants against the reference before using those categories to infer compression-induced loss.
'''
 (ROOT/'README.md').write_text(readme)
 error_map={'malformed_structured_output':'schema','wrong_tool':'tool_selection','wrong_arguments':'tool_arguments','incomplete_plan':'planning','state_loss':'state_loss','failure_to_recover':'planning','premature_completion':'planning','constraint_violation':'instruction','reasoning':'reasoning','timeout_loop':'timeout','other':'other'}
 (ROOT/'error-category-mapping.json').write_text(json.dumps({'version':'1.0','mapping':error_map,'note':'Raw flags preserved separately. Mapping selects frozen visual 0.1 fracture masks; it does not alter scoring.'},indent=2)+'\n')
 if v['status']=='passed':
  files=[p for p in ROOT.iterdir() if p.is_file() and p.name!='release-manifest.json' and not p.name.startswith('.')]
  for folder in ['scripts','raw','artifacts','canonical-panels']:
   files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='inspector-preview.log')
  index={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
  release={'format':'major-minor/release@1.0','status':'complete','publication_status':'draft_unpublished','experiment_id':m['id'],'visualVersion':'0.1','rendererVersion':'0.1.0','scored_trials':1680,'calibration_trials_excluded':10,'neutral_condition_warmups_excluded':7,'native_benchmark_samples_excluded':42,'validation_status':'passed','publication_readiness':readiness,'strict_whole_output_successes':{e['condition']:e['successes'] for e in r['conditions']},'files_sha256':index,'weights':'Original and GGUF model blobs remain local in weights/ and models/; exact revisions, commands and hashes are in model-manifest.json.'}
  (ROOT/'release-manifest.json').write_text(json.dumps(release,indent=2)+'\n')
 print('Wrote draft summary, release notes, X copy, 26-second storyboard and reproduction README. No publication performed.')
if __name__=='__main__':main()
