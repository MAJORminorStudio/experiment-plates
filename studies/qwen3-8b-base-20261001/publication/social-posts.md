# Three X posts

Prepared copy; not posted. Add the eventual article URL as a reply, so no placeholder URL is published.

## Post 1

1,680 real trials. Qwen3-8B Base went from 72.50% strict success at F16 to 1.25% at Q2_K. Q8/Q6 stayed in the same range; Q2 hit a cliff. 80 agent microtasks, 3 runs each, 7 precision levels. Plates, raw outputs and scoring included.

Attach: `social/plate-001-launch-1600.png`. 233 characters.

## Post 2

Compression got weird: 14 tasks improved between adjacent quantization levels. And 36 rejected Q2 responses began with correct JSON, then kept going and broke the output contract. The losses weren’t cleanly monotonic. The raw runs are in Plate 001.

Attach: `../artifacts/contact-sheet.png`. 248 characters.

## Post 3

Introducing Experiment Plates: every mark comes from trial data. Same task, same position across quantization levels. Shared scales, deterministic rendering, provenance in the SVG. Open the inspector and trace a mark back to its run. Every mark is a measurement.

Attach: `../artifacts/F16.png`. 262 characters.

