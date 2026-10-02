# MAJOR//MINOR Experiment Plates · 0.1

The first real experiment is complete: [Qwen3-8B Base compression study](../studies/qwen3-8b-base-20261001/README.md), 1,680 scored trials on Mac Studio M1 Max / 32 GB. Visual grammar 0.1 is frozen. The study includes real plates, raw outputs, validation and unpublished release drafts.

A working TypeScript renderer for one fixed technical experiment format: **conditions × tasks × repeats**. Every task has an address; every run has a trace. A failed capability becomes a visible fracture at that address.

Historical synthetic examples described below are development fixtures. Their images and datasets are excluded from the clean Plate 001 archive; use the real study assets linked above.

The included Qwen3-8B experiment is **synthetic illustration**, not measured model performance. No hardware or model was evaluated. The source has 20 task families, seven quantization conditions, and five runs per task: 700 atomic observations. It illustrates a plausible relationship between compression, throughput, memory, and task reliability without claiming a benchmark result.

## Reproduce

Requires Node.js 22+ and npm. Bundled fonts are used offline; no font service is needed.

```sh
npm ci
npm run example
npm test
npm run preview
```

`example` builds TypeScript, creates the seeded dataset in JSON and CSV, initializes the spec, and exports all plates, PNGs, contact sheet, hero, and inspector. Generation takes a few seconds on the development machine. `preview` serves `outputs/` on loopback at http://127.0.0.1:4173. The inspector also opens directly from its HTML file.

Use the CLI with `npm run plate -- …`. Optionally, `npm link` registers the package's literal `plate` binary. All examples below work with `npm run plate --` in place of `plate`.

```sh
plate init examples/qwen3-8b.synthetic.json --out examples/qwen3-8b.plate.json
plate render examples/qwen3-8b.plate.json --condition Q2_K --out outputs
plate series examples/qwen3-8b.plate.json --out outputs
plate inspect outputs/Q2_K.svg task-017
plate inspect outputs/Q2_K.svg Q2_K-task-017-run-1-trace
plate verify outputs/contact-sheet.svg
```

`render` defaults to the first condition. `render` and `series` accept `--no-png`. Specs resolve their input path relative to the spec file, so they work from another current directory. `inspect` with no selector prints provenance. Unknown selectors, bad inputs, changed source hashes, and failed verification return a nonzero exit code.

For long CSV:

```sh
plate init examples/qwen3-8b.synthetic.csv --out examples/csv.plate.json
plate render examples/csv.plate.json --condition FP16 --out outputs-csv
```

## The frozen stroke grammar

A 960 × 1260 bone frame carries the MAJOR//MINOR identity, plate number, title, condition, task/repeat counts, outcome coverage, four summary metrics, shared domains, short hash, seed, and visual version. Anton sets display text; IBM Plex Mono sets the evidence. There are no gradients, textures, noise, or condition-dependent damage effects.

Twenty addresses form a four-column, five-row grid. `units` array order determines the addresses. Task 017 is always at `(42, 936)` in plate coordinates. The trace grammar is identical in every condition; condition names only identify the plate.

| Channel | Fixed rule |
| --- | --- |
| Task position | Row-major grid, fixed 219 × 143 cell spacing |
| Run / reliability | One trace for each repeat; five intact traces mean 5/5 observed successes |
| Success | Continuous ink path with a verdigris endpoint |
| Failure | Oxide path with category-specific breaks; never a missing-data diamond |
| Latency | Horizontal extent = `183 × latency_ms / shared_latency_max` pixels |
| Throughput | `floor(tokens_per_second / 10)` triangular pulses, evenly spaced on the full trace |
| Memory | Mean observed task/condition memory sets the bracket and run envelope: `24 + 48 × mean_GB / shared_memory_max` pixels |
| Variance | Vertical displacement = `0.15 × lane_spacing × (run_latency − task_median_latency) / shared_latency_max` |
| Missing | Open diamond plus `NA S:… L:… T:… M:…` labels showing missing run numbers by metric |

Pulse height is a fixed three pixels; it is a drawing convention, not a metric. Breaks mask parts of a trace, including any pulses within a gap. Exact throughput is available in the inspector. Missing latency produces a diamond and a separate known-outcome status dot if available. Missing throughput adds a hollow diamond on the otherwise intact/fractured trace. Partial memory coverage is flagged; an all-missing memory envelope becomes a diamond with a fixed neutral lane spacing. These drawing conventions are explicit in the mapping manifest.

Memory records resident footprint including runtime overhead. The bracket is the memory envelope; the 960 × 1260 publication frame remains fixed. The latency displacement is intentionally small enough to preserve run separation. Envelope and displacement use task/condition-derived measurements, with common scales across the whole series.

All numeric domains start at zero. Series maxima round upward to 5,000 ms, 10 tokens/s, and 1 GB. No condition is normalized independently. The flagship domains are 0–55 s, 0–130 tokens/s, and 0–18 GB. Summary latency, throughput, and memory are medians of recorded values, including failed runs. Success rate uses observed outcomes, with missing coverage reported separately.

### Fracture morphology

Ranges are fractions of the unbroken trace extent. A category encodes failure type, not severity.

| Category | Gaps |
| --- | --- |
| instruction | 0.48–0.63 |
| schema | 0.31–0.37, 0.61–0.67 |
| tool_selection | 0.23–0.45 |
| tool_arguments | 0.47–0.62, 0.73–0.78 |
| planning | 0.31–0.44, 0.61–0.75 |
| state_loss | 0.54–0.77 |
| reasoning | 0.37–0.53 |
| timeout | 0.72–0.94; a final stub preserves the latency extent |
| execution | 0.22–0.31, 0.48–0.65 |
| other / unclassified failure | 0.43–0.59 |

Verdigris only marks known successful endpoints. Oxide only marks known failures. Ink supplies labels, structure, neutral measurements, and missing markers. Bone is the substrate. The hero reuses the same plate glyphs and enlarges Task 017; it introduces no second grammar.

## Canonical data and CSV

The schema is `schemas/experiment.schema.json`; `schemas/plate-spec.schema.json` documents the generated spec. Runtime validation additionally checks IDs, unique condition/unit/run slots, references, valid run bounds, finite nonnegative numeric values, and coherent outcome/error pairs.

Canonical JSON has exactly the five conceptual sections: `experiment`, `conditions`, `units`, `metrics`, and `observations`. See the complete synthetic JSON for a runnable example. An observation is:

```json
{
  "id": "FP16-task-001-r1",
  "condition": "FP16",
  "unit": "task-001",
  "run": 1,
  "success": true,
  "latency_ms": 13000,
  "tokens_per_second": 31.5,
  "memory_gb": 17.1,
  "error_category": null
}
```

`success` is boolean or null. All numeric channels are nonnegative numbers or null. `error_category` is a declared category or null. A known failed run with null category uses the `other` fracture and remains explicitly unclassified in evidence. A successful or missing outcome cannot declare an error category. Omitted run slots become deterministic `missing-{condition}-{unit}-{run}` observations with null values. Unknown categories are rejected; map new failures explicitly to `other` for this version.

The long CSV is self-describing. It repeats experiment metadata so it requires no sidecar. Headers:

```text
experiment_id,experiment_title,model,repeats,synthetic,description,condition,condition_label,condition_order,unit,unit_name,unit_order,observation_id,run,success,latency_ms,tokens_per_second,memory_gb,error_category
```

Condition/unit order columns are explicit nonnegative integers. CSV row order never establishes spatial position. Blank, `NA`, or `null` metric cells are missing; success is `true`, `false`, or a missing token. Standard quoted fields and embedded newlines are supported. JSON and CSV normalize to the same dataset hash; their exact source hashes differ.

## Evidence and reproducibility

Pipeline: **input → normalization → plate specification → scene graph → SVG → optional resvg PNG**.

Scene primitives have stable IDs such as `Q2_K-task-017-run-1-trace`. Data primitives declare their mappings and carry condition, task, run numbers, source observation IDs, and derived geometric values. Corresponding units use common deterministic construction, without random texture. The renderer never calls `Math.random`. The source generator has its own seeded PRNG (`20261001`). The spec seed (`17017`) is recorded for future drawing changes; v0.1 geometry contains no stochastic effects and does not depend on it.

Each SVG embeds the original source bytes, normalized dataset, spec, scene graph, composite annotation primitives, exact font hashes, and provenance in `<metadata id="major-minor-manifest">`. The body and scene have separate hashes. The manifest records experiment ID, exact source hash, normalized hash, spec hash, renderer/visual versions, seed, dimensions, condition(s), and mappings. Source hashing includes whitespace; reformatting a file requires reinitializing its spec. Observation-row shuffling leaves normalized hashes and geometry unchanged.

`plate verify` performs 14 checks, including source re-normalization, spec and font hashes, renderer/visual version, seed, scene derivation, body hash, unique SVG IDs, and complete deterministic rerender. It works from the SVG alone with the matching local renderer and bundled fonts. This is integrity and derivation evidence, not cryptographic proof of who ran an experiment. SHA-256 is not a signature. PNG is a convenience export; verify its canonical SVG sibling. `outputs/series-manifest.json` additionally indexes exact SVG hashes.

The self-contained HTML inspector has condition switching, comparison with the first condition, hover evidence, click/Enter pinning, per-run observations, fracture categories, primitive derivation, provenance, and normalized JSON download. Task selection is keyboard accessible. It makes no network requests and contains its own fonts/data/SVG markup.

## Repository and outputs

```text
src/
  types.ts       canonical data, versions, palette, locked mappings
  input.ts       JSON/CSV validation and normalization
  spec.ts        shared domains and spec validation
  scene.ts       task glyphs, fractures, frame, primitive evidence
  svg.ts         SVG compositions, embedded manifest, PNG, verification
  inspector.ts   offline evidence inspector
  outputs.ts     series/export orchestration
  cli.ts         the five plate commands
  synthetic.ts   seeded 700-observation source generator
  preview.ts     optional loopback artifact server
schemas/         JSON schemas for dataset and spec
assets/fonts/    Anton and IBM Plex Mono TTFs and OFL licenses
examples/        synthetic JSON, equivalent long CSV, initialized spec
test/            14 automated behavior/integrity checks
outputs/         nine canonical SVGs, nine PNGs, inspector and manifests
dist/            generated JavaScript after build (ignored)
```

Generated files are under `outputs/`:

- `FP16.svg/.png`, `Q8_0.svg/.png`, `Q6_K.svg/.png`, `Q5_K_M.svg/.png`, `Q4_K_M.svg/.png`, `Q3_K_M.svg/.png`, `Q2_K.svg/.png` — 960 × 1260.
- `contact-sheet.svg/.png` — 2400 × 1860, FP16 → Q2_K order, plus an enlarged evidence key.
- `hero.svg/.png` — 2400 × 1500 editorial composition, FP16/Q4_K_M/Q2_K and Task 017 detail.
- `inspector.html` — portable, offline inspector.
- `normalized.json`, `series-manifest.json` — normalized data and artifact index.
- `quality-report.json` — checks on the delivered artifacts and recorded visual/browser review.

The synthetic dataset and spec are `examples/qwen3-8b.synthetic.json`, `examples/qwen3-8b.synthetic.csv`, and `examples/qwen3-8b.plate.json`.

## Validation and scope

`npm test` checks reproducible SVG/PNG on the current runtime, observation shuffle control, identical JSON/CSV normalization, fixed addresses, shared domains, mappings and evidence references, invariance to quantization names when observations match, latency sensitivity, missing-vs-failure treatment, input rejection, distinct fracture categories, tamper detection, every generated flagship SVG, and CLI use from another directory. The inspector was also tested interactively for task/mark selection, keyboard pinning, condition switching, and reference comparison. The contact sheet and hero were inspected as raster exports and refined to remove label collisions and outlier lane overlap.

**Visual 0.1 is frozen** for this scope. The contact sheet and hero are ready for publication as explicitly synthetic MAJOR//MINOR illustrations.

Deliberate limits: 1–20 units and 1–5 repeats; the fixed contact-sheet/hero compositions accept at most seven conditions. The hero's editorial headline targets the initial compression study. Short task names and titles are expected; unusually long labels need editorial shortening. Tiny publication thumbnails cannot expose exact run values, so use the full-size SVG or inspector. Envelope encodes mean memory, not within-task memory variance. Pulses quantize throughput in 10-token/s steps. Fracture masks are categorical conventions. No cross-platform PNG byte identity is promised; raster/font engines can differ. Source, fonts, and evidence increase SVG size (roughly 1–4 MB); this is intentional for portability. No external benchmark validation, confidence interval inference, hosting, visual editor, alternate grammars, telemetry, or general ontology is included.

Fonts: [Anton from Google Fonts](https://github.com/google/fonts/tree/main/ofl/anton) and [IBM Plex Mono](https://github.com/google/fonts/tree/main/ofl/ibmplexmono), licensed under the bundled SIL OFL notices. Rasterization uses [resvg-js](https://github.com/thx/resvg-js). The project source is MIT licensed.
