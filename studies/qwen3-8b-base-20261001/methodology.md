# Plate 001 methodology

## What we tested

**80 tasks × 3 matched runs × 7 conditions = 1,680 scored trials.** Ten task families each contain eight variants: structured JSON, tool selection, tool arguments, dependency plans, state tracking, context retention, recovery, constraints, completion judgment and code/file reasoning.

We converted one pinned official **Qwen3-8B Base** source into a common F16 GGUF reference, then quantized that reference to Q8_0, Q6_K, Q5_K_M, Q4_K_M, Q3_K_M and Q2_K. No importance matrix was used. The source weights were BF16; F16 is the shared GGUF reference.

All conditions used the same few-shot raw completion prompt, proposed tool definitions, task/run seeds and inference settings: 2,048-token context, 96 new tokens, temperature 0.2, top-k 40, top-p 0.95 and a repeat penalty of 1. No grammar constrained the output, and prompt caching was disabled. The run used one Mac Studio M1 Max with 32 GB of unified memory and a pinned llama.cpp Metal build. Ten calibration responses and seven condition warmups are excluded from the scored denominator.

Deterministic scorers checked the entire output, including JSON syntax and types, expected values, tool arguments and valid plan dependencies. No LLM judged an answer, and no proposed tool was executed. Extra prose, another object or budget exhaustion could fail an otherwise correct opening answer. [Methodology](methodology.md), [task suite](task-suite.json), [scoring definitions](scoring-definitions.json) and [inference settings](inference-settings.json) preserve the details.


## Analysis

Matched paired task-cluster bootstrap, 10000 seeded resamples; three repeats per task are kept together. Category results exploratory, no multiplicity correction.

At least 5 percentage-point paired drop vs F16 and positive lower bound of 95% task-cluster bootstrap interval (10000 resamples). Exploratory categories, no multiplicity-corrected claim.

The full protocol was locked before inference in `study-protocol.json`. Official scores reject the complete response when it violates the contract or exhausts the budget. Prefix correctness is a post hoc diagnostic and never rescues official scores. Warmups, calibration responses and native benchmark samples are separate from the 1,680 scored trials.

## Limitations

- **Strict-output microtasks.** Proposed tools and file operations were scored as responses; nothing was executed. This does not measure autonomous agent success, broad knowledge or maximum-context retention.
- **One model and one system.** The findings apply to this Qwen3-8B Base setup on one M1 Max desktop. The instruction-tuned Qwen3 model was not tested.
- **Three repeats.** Matched task/run seeds support paired comparisons, but few repeats limit conclusions about reversals.
- **Weak F16 categories.** State tracking and constraints started below 50% success. A low reference floor obscures added compression loss.
- **Related task variants.** Eight variants per category reuse ten templates. Task-cluster intervals do not account for dependence among variants within a template; category analyses are exploratory and not multiplicity-corrected.
- **Desktop swapping.** Observed throughput and process-memory results are descriptive. They cannot isolate hardware or quantization effects.
- **Stopping and output discipline.** Q2 may be disproportionately affected by the fixed stopping policy and strict whole-output contract. Correct prefixes remain failed trials.

