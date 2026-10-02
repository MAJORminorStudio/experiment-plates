# MAJOR//MINOR real experiment 001 — Qwen3-8B Base

Complete release: [article](publication/index.html), [GitHub-ready notes](publication/release-notes.md), [three X posts](publication/social-posts.md), [30-second demo](publication/demo/plate-001-demo.mp4), [methodology](methodology.md), [reproduction](reproduction.md) and [publication validation](publication/validation-report.json). Prepared locally; not published.

Ready as a scoped real capability study. Performance comparisons are descriptive: system swapping confounds isolated speed and total-memory claims.

**Measured data only:** 80 tasks × 3 seeds × 7 conditions = **1,680 scored trials**. Ten calibration responses are archived separately. One neutral server warmup per condition is excluded from this denominator; its output is not part of the trial ledger. No synthetic observations are used. Model outputs are untrusted text; the harness never executes proposed tools, code or file operations.

| Condition | Success | Decode tok/s | Prompt tok/s | Peak RSS GB | Model GB |
| --- | ---: | ---: | ---: | ---: | ---: |
| F16 | 174/240 (72.50%) | 16.74 | 95.18 | 9.08 | 16.39 |
| Q8_0 | 177/240 (73.75%) | 33.60 | 426.07 | 8.89 | 8.71 |
| Q6_K | 178/240 (74.17%) | 35.72 | 369.10 | 6.90 | 6.73 |
| Q5_K_M | 169/240 (70.42%) | 29.95 | 335.05 | 6.03 | 5.85 |
| Q4_K_M | 170/240 (70.83%) | 37.56 | 373.63 | 5.21 | 5.03 |
| Q3_K_M | 157/240 (65.42%) | 36.06 | 361.61 | 4.31 | 4.12 |
| Q2_K | 3/240 (1.25%) | 41.36 | 383.21 | 3.46 | 3.28 |


The first condition meeting the predeclared exploratory degradation rule was **Q2_K**. Q3_K_M dropped 7.08 points (95% paired interval -1.25 to 15.42), crossing zero. Q2_K dropped 71.25 points (interval 61.67 to 80.42). The rule required a drop of at least five percentage points versus F16 and a positive lower bound of a 95% paired task-cluster bootstrap interval.

## Reproduce on the same Mac

From the repository root (requires the installed llama.cpp 0.4.1 binaries and ggml 0.24.0 recorded in `environment.json`):

```sh
cd /Volumes/Research/tests/experiment-plates
npm ci
npm run build
python3 -m venv studies/qwen3-8b-base-20261001/.venv
studies/qwen3-8b-base-20261001/.venv/bin/pip install -r studies/qwen3-8b-base-20261001/python-requirements.lock.txt
git init studies/qwen3-8b-base-20261001/runtime/llama.cpp
git -C studies/qwen3-8b-base-20261001/runtime/llama.cpp remote add origin https://github.com/ggml-org/llama.cpp.git
git -C studies/qwen3-8b-base-20261001/runtime/llama.cpp fetch --depth 1 origin b29c606e28a01b1bc8c1351026a0fa6e616bf6c4
git -C studies/qwen3-8b-base-20261001/runtime/llama.cpp checkout --detach FETCH_HEAD
studies/qwen3-8b-base-20261001/.venv/bin/hf download Qwen/Qwen3-8B-Base --revision 49e3418fbbbca6ecbdf9608b4d22e5a407081db4 --local-dir studies/qwen3-8b-base-20261001/weights
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
- `canonical-panels/part-{1,2,3,4}.json`: four datasets conforming to the frozen 20-unit canonical schema, 420 observations each.
- `normalized.json`, `plate-spec.json`: complete 80-task study view and shared-scale spec.
- `experiment-manifest.json`, `model-manifest.json`, `quantization-commands.json`, `environment.json`: exact parameters, model lineage, hashes, commands and environment.
- `task-suite.json`, `scoring-definitions.json`, `scripts/suite.py`: task text, oracle answers, deterministic scoring logic.
- `performance.json`, `raw/bench-*.json`, `raw/bench-*.log`: separate llama-bench pp256/tg64 measurements, three samples each, native process memory reports.
- `artifacts/{F16,Q8_0,Q6_K,Q5_K_M,Q4_K_M,Q3_K_M,Q2_K}.svg/.png`: seven complete 80-task condition plates.
- `artifacts/contact-sheet.svg/.png`: complete ordered series.
- `artifacts/hero.svg/.png`: real publication composition and observed task callout.
- `artifacts/inspector.html`: self-contained real-observation evidence inspector, no network requests.
- `artifacts/panels/`: 28 full-size frozen 20-task detail panels, SVG and PNG.
- `artifacts/verification.json`, `validation.json`, `manual-failure-review.json`: verification, scorer replay and direct failure inspection records.
- `results.json`: overall/category success, paired uncertainty, early/late tasks, reversals, errors, speed/memory tradeoffs.
- `publication/`: final article, social copy, release notes, MP4, edit frames/recipe and publication audit. Earlier working drafts are excluded from the public archive.

## Method and limits

These are agent-relevant microtasks with proposed tools and explicit deterministic oracles. They do not measure autonomous agent success, real tool execution, broad knowledge, or maximum-length context retention. The model is Qwen3-8B **Base**, using one fixed few-shot completion prompt; it is not the instruction-tuned Qwen3 model. Three matched seeds were used for each task, with no automatic expansion to five repeats. Categories have only eight task variants each and are exploratory. Variants reuse ten templates; intervals resampling tasks do not account for dependence between variants within a template or generalize to all agent tasks.

Reference floor warning: state_tracking, constraints. Quantization loss cannot be interpreted cleanly for categories already below 50% in F16.

Source model: `Qwen/Qwen3-8B-Base@49e3418fbbbca6ecbdf9608b4d22e5a407081db4`. Original BF16 safetensors are converted into one F16 GGUF reference; all six quantizations derive from that same reference. No importance matrix is used. F16 is therefore the common GGUF reference, not an assertion of bit-for-bit BF16 inference.

Every request's native generation settings are checked against the declared values. Scorers reject markdown, extra prose, duplicate keys, wrong JSON types/values, missing plan steps and invalid dependencies. A plan can use any valid topological order. Tool names and arguments are checked separately. Exhausting the generation budget fails conservatively under `timeout_loop`; this flag does not prove an actual tool loop. Tool recovery, completion and file operations are simulated reasoning judgments with deterministic expected answers.

Latency is request wall time; trial throughput comes from native generation timings. Controlled performance is measured separately. Plate memory envelopes use 20 Hz sampled process RSS; controlled `/usr/bin/time -l` reports both maximum RSS and peak process footprint where available. These are incomplete measures of total unified-memory/Metal/system occupancy. Model file bytes are reported independently. Thermal and VM snapshots are archived, and fixed sequential condition order/background desktop load remain limitations.

No automatic publication or additional repeats occurred. Category results are exploratory, and observed local reversals are not smoothed. Follow-up experiments must be driven by the observed anomalies, not an assumed monotonic story.

## Observed output-discipline anomaly

Q2_K exhausted the generation budget in 230/240 trials. A post hoc diagnostic found 36/240 Q2_K responses that began with an oracle-correct JSON object but still failed the strict whole-output contract or budget rule. These remain official failures. This separates loss of output discipline from an assumption that every failed answer began with incorrect task reasoning; it does not establish hidden reasoning quality. No stop sequence or prompt was changed for Q2_K.

Specific follow-ups: repeat the performance tests in a quiet desktop session; compare F16, Q3_K_M and Q2_K using a newly predeclared, identical stopping policy that includes unprefixed next-example delimiters, with new independent task variants. Retain the current study unchanged so stopping behavior and task-answer correctness can be compared without retroactively rescuing Q2_K outputs. Calibrate state/constraint variants against the reference before using those categories to infer compression-induced loss.
