# MAJOR//MINOR — Plate 001 / PLATE 0.1

**We Quantized an 8B Agent From F16 to Q2. It Didn’t Break Gradually.**

A complete release from **1,680 real Qwen3-8B Base trials**: 80 strict-output agent microtasks × 3 matched runs × 7 common-source GGUF conditions. Read the [MAJOR//MINOR article](https://majorminor.xyz/research/plate-001). Public repository: [MAJORminorStudio/experiment-plates](https://github.com/MAJORminorStudio/experiment-plates).

![Plate 001 launch image](studies/qwen3-8b-base-20261001/publication/social/plate-001-launch-1600.png)

| Condition | Strict successes | Rate |
| --- | ---: | ---: |
| F16 | 174/240 | 72.50% |
| Q8_0 | 177/240 | 73.75% |
| Q6_K | 178/240 | 74.17% |
| Q5_K_M | 169/240 | 70.42% |
| Q4_K_M | 170/240 | 70.83% |
| Q3_K_M | 157/240 | 65.42% |
| Q2_K | 3/240 | 1.25% |

Q8/Q6 stayed effectively in the F16 capability range on this task set. Q6 does not establish an improvement over F16. Q3’s lower point estimate had a paired interval crossing zero; it is not confirmed overall degradation. Q2 showed a clear collapse. Fourteen task-level reversals are preserved; 230 Q2 trials exhausted the budget and 36 rejected Q2 outputs began with correct JSON.

Q2’s file was 79.97% smaller. Its observed decode throughput was 2.47× F16 **on a desktop affected by swapping**; this is an observed system result, not an isolated hardware claim. One model, one system, three repeats, related task variants and strict-output behavior limit generalization. State tracking and constraints were already weak at F16.

## Read, inspect, reproduce

- [Article page](studies/qwen3-8b-base-20261001/publication/index.html) and [article source](studies/qwen3-8b-base-20261001/publication/article.md)
- [Study README](studies/qwen3-8b-base-20261001/README.md), [methodology](studies/qwen3-8b-base-20261001/methodology.md), [reproduction](studies/qwen3-8b-base-20261001/reproduction.md)
- [Raw JSONL ledger](studies/qwen3-8b-base-20261001/raw/trials.jsonl), [raw CSV](studies/qwen3-8b-base-20261001/raw/trials.csv), [normalized dataset](studies/qwen3-8b-base-20261001/normalized.json), [results](studies/qwen3-8b-base-20261001/results.json)
- [Experiment manifest](studies/qwen3-8b-base-20261001/experiment-manifest.json), [model/source hashes](studies/qwen3-8b-base-20261001/model-manifest.json), [inference settings](studies/qwen3-8b-base-20261001/inference-settings.json), [quantization commands](studies/qwen3-8b-base-20261001/quantization-commands.json), [environment](studies/qwen3-8b-base-20261001/environment.json), [scoring](studies/qwen3-8b-base-20261001/scoring-definitions.json)
- [Contact sheet](studies/qwen3-8b-base-20261001/artifacts/contact-sheet.png), [individual plates and panels](studies/qwen3-8b-base-20261001/artifacts/series-manifest.json), [offline inspector](studies/qwen3-8b-base-20261001/artifacts/inspector.html)
- [Three X posts](studies/qwen3-8b-base-20261001/publication/social-posts.md), [demo MP4](studies/qwen3-8b-base-20261001/publication/demo/plate-001-demo.mp4), [exact edit recipe](studies/qwen3-8b-base-20261001/publication/demo/edit-spec.md)
- [GitHub-ready release notes](studies/qwen3-8b-base-20261001/publication/release-notes.md), [release validation](studies/qwen3-8b-base-20261001/publication/validation-report.json), [licenses](studies/qwen3-8b-base-20261001/LICENSES.md)

The canonical local checkout is `/Volumes/Research/tests/experiment-plates`. It retains the published Git history and remote. Original trial/command records and tagged release archives retain their recorded historical paths; local runners resolve model files under the current study directory. `SHA256SUMS` describes the original published snapshot, before these local migration edits.

Serve the repository to preview the article:

```sh
cd /Volumes/Research/tests/experiment-plates
python3 -m http.server 4173 --bind 127.0.0.1
```

Open `http://127.0.0.1:4173/studies/qwen3-8b-base-20261001/publication/`. The inspector is self-contained and also works directly from its HTML file. No third-party fonts or services are required by the page.

Verify existing results without running inference:

```sh
cd /Volumes/Research/tests/experiment-plates
npm ci
npm run build
python3 studies/qwen3-8b-base-20261001/scripts/test_suite.py
node studies/qwen3-8b-base-20261001/scripts/export.mjs --verify
python3 scripts/publication/validate.py
```

Rebuild editorial assets: `npm ci --prefix scripts/publication`, then `python3 scripts/publication/build.py`. Build the clean archive with `python3 scripts/publication/package.py`; its public contents exclude weights, runtime copies, dependency folders, earlier drafts and synthetic examples/outputs. These commands do not start a model or rerun throughput tests.

## Experiment Plates

**Every mark is a measurement.** Fixed task addresses, shared scales, trial-derived geometry, embedded provenance and deterministic SVG rendering let the inspector connect marks to observations. Visual 0.1 remains frozen. Tables and ordinary plots accompany the plates for exact values and uncertainty.

[Renderer documentation](docs/renderer-0.1.md) describes the original 20-task format. Plate 001 composes four unchanged panels per condition. Historical synthetic examples remain explicitly marked in the development checkout; they are excluded from the clean public archive and never feed the article or real study assets.

Plate 002 is planned, not run: F16 vs Q3_K_M vs Q2_K with a broader, identical stopping policy to test termination/output discipline separately from capability loss.

Code and original study materials: [MIT](LICENSE). Fonts: SIL OFL 1.1. Upstream model weights and dependencies retain their own licenses; weights are not distributed here.

Final site integration and exact publishing commands: [publication guide](studies/qwen3-8b-base-20261001/publication/PUBLISH.md). The final square social PNG/SVG are in `studies/qwen3-8b-base-20261001/publication/social/`.
