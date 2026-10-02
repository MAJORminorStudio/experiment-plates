# Experiment Plates / PLATE 0.1

An open-source visualization tool: fixed task addresses, shared scales, trial-derived geometry, embedded provenance and deterministic SVG rendering. **Every mark is a measurement.**

[Renderer documentation](docs/renderer-0.1.md) · [PLATE 0.1 release](https://github.com/MAJORminorStudio/experiment-plates/releases/tag/plate-v0.1.0) · [MIT license](LICENSE).

```sh
npm ci
npm run build
npm test
npm run example
```

Synthetic examples are development fixtures, explicitly marked as synthetic. The renderer is independently usable with a dataset following the schemas in `schemas/`. Visual 0.1 remains frozen.

## Qwen3-8B quantization example

The [Qwen3-8B quantization/compression study](https://majorminor.xyz/research/plate-001) used Experiment Plates to render 1,680 strict-output agent microtask trials, F16 through Q2_K. Its research category is **Model Compression / Qwen3-8B / Quantization**. Plate 001 is its publication/artifact identifier.

The canonical local study lives at `/Volumes/Research/tests/model-compression/qwen3-8b-quantization`, including raw trials, scoring, configs, results, analysis, model/runtime metadata, reproduction and editorial tooling. This repository owns the renderer. [Frozen study references](studies/README.md) preserve public evidence and release links. The local legacy study and editorial-tooling paths are compatibility symlinks; they contain no duplicated canonical data.

The [existing Plate 001 release](https://github.com/MAJORminorStudio/experiment-plates/releases/tag/plate-001-v1.0.0) and all published history remain unchanged. They are historical snapshots; future research ownership belongs to model-compression. `SHA256SUMS` records the original release, rather than the current tool-only checkout.
