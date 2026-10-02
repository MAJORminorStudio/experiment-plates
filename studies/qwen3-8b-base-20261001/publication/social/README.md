# Plate 001 social launch graphic

Dedicated 1600 × 1600 artwork for the X feed. It is composed from real trial data, not a reduced contact sheet.

- `plate-001-launch-1600.png`: final 1600 × 1600 raster export.
- `plate-001-launch-1600.svg`: final portable SVG; Anton and IBM Plex Mono lettering is outlined.
- `plate-001-launch-1600.editable.svg`: editable text counterpart with embedded fonts.
- `validation.json`: source/output hashes, exact counts/rates and validation results.
- `qa/`: 400 px and 360 px feed-size checks.

Every condition includes all 80 tasks in the same ten-column, eight-row order, with three measured traces per task. Success rates use the exact successes divided by 240, displayed to two decimal places. The raw ledger, normalized observations and study results agree for all seven conditions.

The unmodified visual-0.1 `unitScene` renderer supplies latency, throughput, memory envelope, variance and category-specific fracture geometry. This social adaptation uses the same affine projection across conditions, omits small task labels/registrations, and applies uniform optical stroke widths and endpoint radii for feed downsampling. Successful paths remain ink with verdigris endpoints; failed paths remain oxide. The Q2_K evidence field retains the bone substrate within the emphasized ink row. Fine task/run geometry is intended for full-resolution inspection; phone viewing prioritizes condition names, rates and the Q2 collapse.

The wordmark sets MAJOR at 56 and MINOR at 39.2, a font-size ratio of exactly 70%, on a shared baseline. Palette: bone `#E7DFCC`, ink `#0A0A08`, verdigris `#3DA887`, oxide `#D9643A`.

Regenerate from the data-art repository root:

```sh
node scripts/publication/launch-graphic.mjs
```

The generator uses the existing compiled frozen renderer and installed resvg dependency. It exports the final outlined SVG, rasterizes that SVG without system fonts, and produces both phone-size proofs. Re-running resets the visual-review field to pending; inspect the proofs before marking a new export reviewed. No canonical plate, frozen source, font, study result or raw ledger was changed. The freeze manifest was checked successfully after export. This is a separate publication adaptation requested for the launch graphic, not a new canonical visual version.

Final packaging adjustments: 20% thicker task traces/endpoints/envelopes, the compact model/trial/hardware label, and a larger oxide Anton COLLAPSE label. This is the primary X launch and Open Graph image. The canonical renderer and measurements remain unchanged.
