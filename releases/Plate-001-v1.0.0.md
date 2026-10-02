# Plate 001 — Qwen3-8B Base quantization study · 1.0.0

A common-source F16-to-Q2 quantization series produced 1,680 real strict-output trials: 80 agent-relevant microtasks, three matched runs, seven conditions on one Mac Studio M1 Max / 32 GB.

| Condition | Successes | Rate |
| --- | ---: | ---: |
| F16 | 174/240 | 72.50% |
| Q8_0 | 177/240 | 73.75% |
| Q6_K | 178/240 | 74.17% |
| Q5_K_M | 169/240 | 70.42% |
| Q4_K_M | 170/240 | 70.83% |
| Q3_K_M | 157/240 | 65.42% |
| Q2_K | 3/240 | 1.25% |

Q8/Q6 stayed effectively in the F16 capability range for this scoped study. Q3’s 7.08-point drop had a paired interval crossing zero (−1.25 to 15.42 points); it is not confirmed overall degradation. Q2 showed a clear collapse: 3/240 successes, 230 budget exhaustions, and 36 rejected responses with oracle-correct opening JSON. Fourteen task-level reversals remain in the data. No task met the Q2 late-robustness criterion.

Earlier exploratory category losses: tool arguments at Q5_K_M, code/file reasoning at Q4_K_M, recovery at Q3_K_M. State tracking and constraints were already weak at F16. Q2 files were 79.97% smaller. Observed decode throughput was 2.47× F16, affected by desktop swapping; this is an observed system result, not an isolated hardware claim.

Includes the article, three X posts, 30-second MP4 and exact edit recipe; raw JSONL/CSV ledgers; normalized dataset and canonical panels; results and manifests; scorer definitions and replay; source/model hashes; inference and quantization commands; environment and performance records; 37 verified SVG/PNG artifacts; offline evidence inspector; reproduction and licensing notes.

Limits: strict-output microtasks, one Base model, one system, three repeats, related task templates, exploratory category comparisons, weak baseline categories, swapping, and potentially disproportionate Q2 stopping/output-contract effects. Plate 002 is described but has not run.

Publication destinations: [MAJOR//MINOR article](https://majorminor.xyz/research/plate-001), [public repository](https://github.com/MAJORminorStudio/experiment-plates), [Plate 001 release](https://github.com/MAJORminorStudio/experiment-plates/releases/tag/plate-001-v1.0.0), and [PLATE visual 0.1 release](https://github.com/MAJORminorStudio/experiment-plates/releases/tag/plate-v0.1.0). The site integration is isolated on a clean origin/main checkout; publishing commands are in publication/PUBLISH.md. Model weights, runtime copies, synthetic examples and synthetic output artifacts are excluded from the public archive.

Final launch: 1600×1600 PNG/SVG with a 20% optical-weight increase, model/trial/hardware label and stronger oxide COLLAPSE treatment. Integrated into the existing mm-labs research index and sitemap at `/research/plate-001`. Production-relative links, images, inspector, gzip downloads and 360/390/768 layouts passed. No benchmark rerun or Plate 002 execution.
