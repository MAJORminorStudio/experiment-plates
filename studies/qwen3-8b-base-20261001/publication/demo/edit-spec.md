# Plate 001 — exact 30-second edit

1920×1080, 30 fps, H.264/yuv420p, silent, 900 frames. Hard cuts preserve the unchanged task geometry; no transitions, altered strokes or invented telemetry. All source plates are visual 0.1. The inspector shots use actual browser captures; the pointer and response callout are editorial overlays. The green snippet is explicitly the correct opening object, not the full response or an official success.

| Time | Frames (end exclusive) | Shot |
| --- | --- | --- |
| 0.000–4.000s | 0–120 | 00-F16.png |
| 4.000–5.833s | 120–175 | 01-Q8_0.png |
| 5.833–7.667s | 175–230 | 02-Q6_K.png |
| 7.667–9.500s | 230–285 | 03-Q5_K_M.png |
| 9.500–11.333s | 285–340 | 04-Q4_K_M.png |
| 11.333–13.167s | 340–395 | 05-Q3_K_M.png |
| 13.167–15.000s | 395–450 | 06-Q2_K.png |
| 15.000–22.000s | 450–660 | 07-Q2-collapse.png |
| 22.000–23.000s | 660–690 | 08-inspector-open.png |
| 23.000–25.000s | 690–750 | 09-inspector-select.png |
| 25.000–27.000s | 750–810 | 10-inspector-raw.png |
| 27.000–30.000s | 810–900 | 11-contact-sheet.png |

0–4s: F16, “80 agent tasks. 3 runs each.” 4–15s: step through Q8_0, Q6_K, Q5_K_M, Q4_K_M, Q3_K_M and Q2_K at identical positions (55 frames each). 15–22s: hold on Q2, “3 / 240 successes.” 22–27s: actual inspector opening, selected failed task 003, then the correct opening JSON and its rejected status. 27–30s: contact sheet + MAJOR//MINOR, “1,680 real trials” and “Every mark is a measurement.”

From this demo directory:

```sh
ffmpeg -y -f concat -safe 0 -i shots.ffconcat -r 30 -frames:v 900 \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -movflags +faststart -an plate-001-demo.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames,duration -of json plate-001-demo.mp4
```

`demo-manifest.json` maps shots to frames, source assets, trial ID and hashes. `scripts/publication/demo.py` rebuilds all compositions from the same real assets and inspector captures. No benchmark is run.
