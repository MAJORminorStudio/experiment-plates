#!/usr/bin/env python3
"""Package editorial assets from the completed ledger. Never runs inference."""
import json, pathlib, hashlib, html, shutil, subprocess
REPO=pathlib.Path(__file__).resolve().parents[2]
STUDY=REPO/'studies/qwen3-8b-base-20261001'
OUT=STUDY/'publication';OUT.mkdir(exist_ok=True)
def read(n):return json.loads((STUDY/n).read_text())
r=read('results.json');m=read('experiment-manifest.json');cs=r['conditions'];by={c['condition']:c for c in cs}
rows=[json.loads(l) for l in (STUDY/'raw/trials.jsonl').read_text().splitlines()]
example=next(x for x in rows if x['id']=='Q2_K-task-003-r1')
def table(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rows)
def figure(file,alt,caption):return f'<figure><a href="../artifacts/{file}" aria-label="Open full resolution: {html.escape(alt)}"><img src="../artifacts/{file}" alt="{html.escape(alt)}" loading="lazy"></a><figcaption>{caption}</figcaption></figure>\n'
# A conventional plot uses the same verified aggregate values, separate from PLATE grammar.
svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 550" role="img" aria-labelledby="title desc"><title id="title">Strict success across seven quantization levels</title><desc id="desc">Seven observed success rates, denominators 240. Bars start at zero. Exact values are in the adjacent table.</desc><rect width="1000" height="550" fill="#E7DFCC"/>']
for tick in range(0,101,20):
 y=450-tick*3.8;svg.append(f'<path d="M80 {y}H965" stroke="#0A0A08" stroke-opacity=".2"/><text x="65" y="{y+5}" text-anchor="end" font-family="monospace" font-size="15">{tick}%</text>')
for i,c in enumerate(cs):
 x=105+i*120;h=c['success_rate']*380;color='#D9643A' if c['condition']=='Q2_K' else '#0A0A08'
 svg.append(f'<rect x="{x}" y="{450-h}" width="70" height="{h}" fill="{color}"/><text x="{x+35}" y="{435-h}" text-anchor="middle" font-family="monospace" font-size="17">{c["success_rate"]*100:.2f}%</text><text x="{x+35}" y="485" text-anchor="middle" font-family="monospace" font-size="15">{c["condition"]}</text>')
svg.append('<text x="80" y="535" font-family="monospace" font-size="15">OBSERVED STRICT SUCCESS / 240 TRIALS PER CONDITION / ZERO BASELINE</text></svg>')
(OUT/'success-rates.svg').write_text(''.join(svg))
overall=table(['Condition','Strict successes','Success rate','Drop vs F16 (pp)','95% paired interval for drop (pp)'],[[c['condition'],f"{c['successes']}/{c['trials']}",f"{100*c['success_rate']:.2f}%",f"{100*c['paired_drop_vs_f16']:.2f}",' / '.join(f'{100*x:.2f}' for x in c['paired_drop_ci95'])] for c in cs])
category=table(['Task family']+[c['condition'] for c in cs],[[k.replace('_',' ')] + [f"{e['successes']}/{e['trials']}" for e in v] for k,v in r['capability_categories'].items()])
perf=table(['Condition','Model file (GB, decimal)','Observed decode (tok/s)'],[[c['condition'],f"{c['model_bytes']/1e9:.2f}",f"{c['controlled_generation_tokens_per_second']:.2f}"] for c in cs])
reversal=next(x for x in r['non_monotonic_tasks'] if x['task_id']=='task-020')
rt=table(['task-020']+[c['condition'] for c in cs],[['Successes / 3']+[f'{reversal["successes_by_condition"][c["condition"]]}/3' for c in cs]])
article=f'''# We Quantized an 8B Agent From F16 to Q2. It Didn’t Break Gradually.

<div class="deck">1,680 real trials. Seven precision levels. A clear Q2 cliff—and a few awkward reversals on the way down.</div>

<div class="article-meta">PLATE 001 · QWEN3-8B BASE · OCTOBER 1, 2026 · VISUAL 0.1</div>

{figure('hero.png','Existing Plate 001 hero, comparing measured Qwen3-8B Base conditions','The original study hero. All traces come from the completed ledger; the plate grammar remains visual 0.1.')}

## The result

Qwen3-8B Base completed **174/240 trials at F16 (72.50%)** and **3/240 at Q2_K (1.25%)** under a strict whole-output contract. Q8_0 and Q6_K stayed effectively in the same capability range as F16 in this scoped study. Q3_K_M had a lower point estimate, but its paired interval crossed zero. Earlier category-specific losses appeared at Q5_K_M, Q4_K_M and Q3_K_M; the clear overall collapse arrived at Q2_K. Here, “agent” means tasks involving proposed tools, plans, state and files. We measured microtask responses, not an autonomous agent executing tools.

## Seven conditions, one set of addresses

{figure('contact-sheet.png','Contact sheet of seven measured plates in order from F16 through Q2_K','Read left to right, then down: F16 → Q8_0 → Q6_K → Q5_K_M → Q4_K_M → Q3_K_M → Q2_K. Each condition contains all 80 tasks in four fixed panels. Open the image for full resolution.')}

The contact sheet makes the cliff visible. To check a count, read the tables. To investigate a mark, open the inspector.

<div class="explorer" aria-label="Compare individual measured plates">
<div class="condition-tabs" role="group" aria-label="Choose quantization condition">{''.join(f'<button type="button" data-quant="{c["condition"]}" aria-pressed="{str(i==0).lower()}">{c["condition"]}</button>' for i,c in enumerate(cs))}</div>
<p id="plate-summary" aria-live="polite">F16 · 174 / 240 successes · 72.50%</p>
<a id="plate-full" href="../artifacts/F16.png"><img id="plate-image" src="../artifacts/F16.png" alt="F16: four unchanged panels covering all 80 task addresses" loading="lazy"></a>
<p class="small">Task addresses and scales stay fixed across conditions. <a href="../artifacts/inspector.html">Open the evidence inspector →</a></p>
</div>

## What we tested

**80 tasks × 3 matched runs × 7 conditions = 1,680 scored trials.** Ten task families each contain eight variants: structured JSON, tool selection, tool arguments, dependency plans, state tracking, context retention, recovery, constraints, completion judgment and code/file reasoning.

We converted one pinned official **Qwen3-8B Base** source into a common F16 GGUF reference, then quantized that reference to Q8_0, Q6_K, Q5_K_M, Q4_K_M, Q3_K_M and Q2_K. No importance matrix was used. The source weights were BF16; F16 is the shared GGUF reference.

All conditions used the same few-shot raw completion prompt, proposed tool definitions, task/run seeds and inference settings: 2,048-token context, 96 new tokens, temperature 0.2, top-k 40, top-p 0.95 and a repeat penalty of 1. No grammar constrained the output, and prompt caching was disabled. The run used one Mac Studio M1 Max with 32 GB of unified memory and a pinned llama.cpp Metal build. Ten calibration responses and seven condition warmups are excluded from the scored denominator.

Deterministic scorers checked the entire output, including JSON syntax and types, expected values, tool arguments and valid plan dependencies. No LLM judged an answer, and no proposed tool was executed. Extra prose, another object or budget exhaustion could fail an otherwise correct opening answer. [Methodology](../methodology.md), [task suite](../task-suite.json), [scoring definitions](../scoring-definitions.json) and [inference settings](../inference-settings.json) preserve the details.

## Overall results

<figure><img src="success-rates.svg" alt="Zero-based bar plot of the seven success rates; exact counts follow"><figcaption>Observed strict success. The plot shows point estimates; uncertainty for paired differences appears in the table.</figcaption></figure>

{overall}

Q6_K’s 178 successes versus F16’s 174 do **not** establish that Q6 beats F16. Q8/Q6 were effectively in the same capability range on this task set; this is not a formal equivalence test.

Q3_K_M dropped **7.08 percentage points** in the point estimate. Its 95% paired interval for the drop was **−1.25 to 15.42 points**, which crosses zero. We do not present this as confirmed overall degradation.

Q2_K dropped **71.25 percentage points**, with a paired interval of **61.67 to 80.42 points**. It was the first condition to meet the predeclared overall rule: a drop of at least five points and a positive lower bound of the 95% paired interval. Intervals use 10,000 seeded task-cluster bootstrap resamples, retaining each task’s three repeats together. They quantify uncertainty within this task set, not across every possible agent task.

## Where losses appeared first

Tool arguments first met the exploratory category rule at **Q5_K_M**: **5/24**, versus **12/24 at F16**. Code/file reasoning first met it at **Q4_K_M**: **18/24**, versus **22/24 at F16**. Recovery first met it at **Q3_K_M**: **0/24**, versus **12/24 at F16**.

These are category-specific signals from eight variants per family, without correction for multiple comparisons. “First” identifies the earliest qualifying condition in the tested order; it does not imply that every subsequent condition stayed worse. Tool arguments recovered to **24/24 at Q4_K_M and Q3_K_M**.

<details><summary>All category counts (24 trials per cell)</summary>

{category}

</details>

State tracking (**7/24**) and constraint-following (**4/24**) were already weak at F16. Their reference floors make compression-induced loss difficult to interpret. Those weaknesses belong in the baseline story too.

## The Q2 failure mode

<div class="stat-band"><div><strong>3 / 240</strong><span>strict successes</span></div><div><strong>230 / 240</strong><span>generation budgets exhausted</span></div><div><strong>36</strong><span>correct opening objects, rejected outputs</span></div></div>

Q2_K exhausted the 96-token generation budget in **230/240 trials**. The scorer calls this flag `timeout_loop`; it means budget exhaustion, not a demonstrated tool loop or a transport timeout.

A post hoc diagnostic found **36 rejected Q2 responses that began with an oracle-correct JSON object**, then continued beyond it. These remain failures under the original contract. Task 003 is a concrete example: the opening ticket answer is correct, but the response starts inventing further tasks and runs into the token limit.

<details open><summary>Actual response · Q2_K-task-003-r1 · 96 generated tokens · stop: limit</summary><pre class="raw-output">{html.escape(example['raw_output'])}</pre></details>

This is evidence of output-discipline trouble. It does not establish that all Q2 failures hide correct reasoning, and extracting the first object would change the scoring rule. Strict stopping/output behavior may disproportionately affect Q2’s measured collapse. **No task met the late-robustness criterion** of at least two successes out of three at both F16 and Q2_K.

<div class="pair">{figure('F16.png','F16 condition plate with 174 measured successes','F16 · 174/240 strict successes.')}{figure('Q2_K.png','Q2_K condition plate with 3 measured successes','Q2_K · 3/240 strict successes. Every fracture corresponds to a scored failure.')}</div>

[Inspect task 003 and its raw runs](../artifacts/inspector.html), or read the complete [JSONL ledger](../raw/trials.jsonl) and [CSV ledger](../raw/trials.csv).

## Reversals stayed in the data

**14 tasks** improved across at least one adjacent pair of conditions. Task 020, “Build arguments,” is one: it fell from three successes to zero at Q5_K_M, then returned to three at Q4_K_M.

{rt}

We retained the reversals in the ledger and plates. Three repeats do not establish a reproducible quantization advantage, but the observations do rule out telling a cleanly monotonic story about this run. The [results JSON](../results.json) lists every reversal and the early/late task criteria.

## Speed and size: a real tradeoff, with a system caveat

The Q2_K model file was **79.97% smaller** than F16: **3.28 GB versus 16.39 GB**. Separately recorded llama-bench decode throughput was **41.36 versus 16.74 tokens/s**, or **2.47× F16**.

**That ratio is an observed system result. Desktop swapping affected the measurements, so it is not an isolated hardware or quantization speed claim.** Fixed condition order and background desktop load also confound performance comparisons. The smaller file did not preserve strict-output success.

{perf}

These are decimal file sizes and separate, warmed decode tests with three native samples per condition. Plate memory geometry uses sampled process RSS. RSS and native footprint counters do not account for all system or Metal allocations. The complete [performance measurements](../performance.json) and [environment metadata](../environment.json) are available for inspection.

## Experiment Plates / PLATE 0.1

<div class="quote">Every mark is a measurement.</div>

Experiment Plates give repeated tasks a fixed address. The same task sits in the same place at every quantization level, and the conditions share scales. Each run draws a trace: an intact stroke for success, an oxide fracture for a scored failure. Horizontal extent comes from latency, pulses from decode throughput, and the memory bracket/envelope from recorded process RSS. Small displacement records latency variation.

The visual rules are fixed at **version 0.1**. This study composes four unchanged 20-task panels per condition to cover all 80 tasks. SVG artifacts embed provenance, source data, drawing rules and hashes. A deterministic renderer reproduces their geometry; the inspector traces a selected task or mark back to its observations and raw output.

The plates help readers compare many task addresses and investigate individual runs. Conventional tables and plots still carry exact aggregate values and statistical uncertainty. PLATE is a companion to those tools and to experiment tracking. [Frozen renderer details](../../../docs/renderer-0.1.md) and [artifact verification](../artifacts/verification.json) describe the format.

## Limitations

- **Strict-output microtasks.** Proposed tools and file operations were scored as responses; nothing was executed. This does not measure autonomous agent success, broad knowledge or maximum-context retention.
- **One model and one system.** The findings apply to this Qwen3-8B Base setup on one M1 Max desktop. The instruction-tuned Qwen3 model was not tested.
- **Three repeats.** Matched task/run seeds support paired comparisons, but few repeats limit conclusions about reversals.
- **Weak F16 categories.** State tracking and constraints started below 50% success. A low reference floor obscures added compression loss.
- **Related task variants.** Eight variants per category reuse ten templates. Task-cluster intervals do not account for dependence among variants within a template; category analyses are exploratory and not multiplicity-corrected.
- **Desktop swapping.** Observed throughput and process-memory results are descriptive. They cannot isolate hardware or quantization effects.
- **Stopping and output discipline.** Q2 may be disproportionately affected by the fixed stopping policy and strict whole-output contract. Correct prefixes remain failed trials.

## Reproduction and evidence

Start with the [study README](../README.md) and [reproduction commands](../reproduction.md). Replay scoring and verify the existing artifact manifests without starting an inference server:

```sh
npm ci
npm run build
python3 studies/qwen3-8b-base-20261001/scripts/test_suite.py
node studies/qwen3-8b-base-20261001/scripts/export.mjs --verify
python3 scripts/publication/validate.py
```

The release includes the raw ledger, normalized data, results, experiment manifest, scorer definitions, model/source hashes, inference settings, quantization commands, environment metadata, SVG/PNG plates, hero, contact sheet, inspector and demo. Large model weights are reproduced from the pinned source and are not bundled.

<div class="downloads"><a href="../raw/trials.jsonl" download>Raw ledger / JSONL</a><a href="../normalized.json" download>Normalized dataset</a><a href="../results.json" download>Results JSON</a><a href="../experiment-manifest.json" download>Experiment manifest</a><a href="../model-manifest.json" download>Model / source hashes</a><a href="../quantization-commands.json" download>Quantization commands</a><a href="../artifacts/inspector.html">Evidence inspector</a><a href="demo/plate-001-demo.mp4">30-second demo</a><a href="release-notes.md">Release notes</a><a href="../LICENSES.md">Licenses</a></div>

## Next: Plate 002

Compare **F16 vs Q3_K_M vs Q2_K** under a newly predeclared, broader stopping policy applied identically to all three conditions. Test whether Q2’s collapse is partly a failure of termination/output discipline rather than complete capability loss. Keep strict whole-output results and prefix-correctness diagnostics separate, and retain Plate 001 unchanged. **Plate 002 has not been run.**
'''
(OUT/'article.md').write_text(article)
(OUT/'article-data.json').write_text(json.dumps({'results_sha256':hashlib.sha256((STUDY/'results.json').read_bytes()).hexdigest(),'conditions':[{k:c[k] for k in ['condition','successes','trials','success_rate','paired_drop_vs_f16','paired_drop_ci95','model_bytes','controlled_generation_tokens_per_second']} for c in cs],'q2_budget_exhaustions':by['Q2_K']['error_flag_counts']['timeout_loop'],'correct_prefix_q2':r['output_discipline_diagnostic']['correct_initial_object_but_strict_failure_counts']['Q2_K'],'task_reversals':r['non_monotonic_task_count'],'example_trial':example['id']},indent=2)+'\n')
posts=["1,680 real trials. Qwen3-8B Base went from 72.50% strict success at F16 to 1.25% at Q2_K. Q8/Q6 stayed in the same range; Q2 hit a cliff. 80 agent microtasks, 3 runs each, 7 precision levels. Plates, raw outputs and scoring included.","Compression got weird: 14 tasks improved between adjacent quantization levels. And 36 rejected Q2 responses began with correct JSON, then kept going and broke the output contract. The losses weren’t cleanly monotonic. The raw runs are in Plate 001.","Introducing Experiment Plates: every mark comes from trial data. Same task, same position across quantization levels. Shared scales, deterministic rendering, provenance in the SVG. Open the inspector and trace a mark back to its run. Every mark is a measurement."]
assert all(len(x)<=280 for x in posts)
(OUT/'social-posts.json').write_text(json.dumps([{'post':i+1,'text':p,'characters':len(p),'attach':['social/plate-001-launch-1600.png','../artifacts/contact-sheet.png','../artifacts/F16.png'][i]} for i,p in enumerate(posts)],indent=2)+'\n')
(OUT/'social-posts.md').write_text('# Three X posts\n\nPrepared copy; not posted. Add the eventual article URL as a reply, so no placeholder URL is published.\n\n'+''.join(f'## Post {i+1}\n\n{p}\n\nAttach: '+['`social/plate-001-launch-1600.png`','`../artifacts/contact-sheet.png`','`../artifacts/F16.png`'][i]+f'. {len(p)} characters.\n\n' for i,p in enumerate(posts)))
notes='''# Plate 001 — Qwen3-8B Base quantization study · 1.0.0

A common-source F16-to-Q2 quantization series produced 1,680 real strict-output trials: 80 agent-relevant microtasks, three matched runs, seven conditions on one Mac Studio M1 Max / 32 GB.

| Condition | Successes | Rate |
| --- | ---: | ---: |
'''+''.join(f'| {c["condition"]} | {c["successes"]}/240 | {100*c["success_rate"]:.2f}% |\n' for c in cs)+'''
Q8/Q6 stayed effectively in the F16 capability range for this scoped study. Q3’s 7.08-point drop had a paired interval crossing zero (−1.25 to 15.42 points); it is not confirmed overall degradation. Q2 showed a clear collapse: 3/240 successes, 230 budget exhaustions, and 36 rejected responses with oracle-correct opening JSON. Fourteen task-level reversals remain in the data. No task met the Q2 late-robustness criterion.

Earlier exploratory category losses: tool arguments at Q5_K_M, code/file reasoning at Q4_K_M, recovery at Q3_K_M. State tracking and constraints were already weak at F16. Q2 files were 79.97% smaller. Observed decode throughput was 2.47× F16, affected by desktop swapping; this is an observed system result, not an isolated hardware claim.

Includes the article, three X posts, 30-second MP4 and exact edit recipe; raw JSONL/CSV ledgers; normalized dataset and canonical panels; results and manifests; scorer definitions and replay; source/model hashes; inference and quantization commands; environment and performance records; 37 verified SVG/PNG artifacts; offline evidence inspector; reproduction and licensing notes.

Limits: strict-output microtasks, one Base model, one system, three repeats, related task templates, exploratory category comparisons, weak baseline categories, swapping, and potentially disproportionate Q2 stopping/output-contract effects. Plate 002 is described but has not run.

Publication destinations: [MAJOR//MINOR article](https://majorminor.xyz/research/plate-001), [public repository](https://github.com/MAJORminorStudio/experiment-plates), [Plate 001 release](https://github.com/MAJORminorStudio/experiment-plates/releases/tag/plate-001-v1.0.0), and [PLATE visual 0.1 release](https://github.com/MAJORminorStudio/experiment-plates/releases/tag/plate-v0.1.0). The site integration is isolated on a clean origin/main checkout; publishing commands are in publication/PUBLISH.md. Model weights, runtime copies, synthetic examples and synthetic output artifacts are excluded from the public archive.

# PLATE / Experiment Plates — visual 0.1

The first frozen visual format gives tasks fixed addresses and uses common scales across conditions. One trace represents one measured run; intact strokes show successes and oxide fractures show failures. Latency, throughput, process RSS and within-task latency variation determine the geometry.

The study adapter composes four unchanged 20-task panels per condition. SVGs contain observations, geometry rules, provenance and hashes; deterministic verification reproduces every artifact. The self-contained inspector exposes each task’s runs and raw outputs.

No stroke grammar, fonts, colors, layout mappings or renderer version changed in this release. Tables and conventional plots accompany the plates for exact aggregate values and uncertainty. PLATE complements charts and experiment tracking.

Code and study materials: MIT, subject to the third-party notices. Anton and IBM Plex Mono: SIL OFL 1.1. Model weights are not distributed in this archive; consult the pinned upstream model license before redistribution.
'''
(OUT/'release-notes.md').write_text(notes)
# Public methods and commands are separated from earlier working drafts.
readme=(STUDY/'README.md').read_text();start=readme.index('## Reproduce on the same Mac');end=readme.index('## Input, renderer and evidence')
(STUDY/'reproduction.md').write_text('# Reproduction\n\n## Verify existing data without inference\n\n```sh\ncd '+str(REPO)+'\nnpm ci\nnpm run build\npython3 studies/qwen3-8b-base-20261001/scripts/test_suite.py\nnode studies/qwen3-8b-base-20261001/scripts/export.mjs --verify\npython3 scripts/publication/validate.py\n```\n\nFor the publication page builder: `npm ci --prefix scripts/publication`, then `python3 scripts/publication/build.py`. To preview, run `python3 -m http.server 4173 --bind 127.0.0.1` from the repository root and open `/studies/qwen3-8b-base-20261001/publication/`.\n\n## Independent inference replication\n\nThe following commands run models. They were not run during release preparation. Back up the completed study and use a fresh ledger/workspace for an independent replication. Historical manifests retain the recorded command paths. The runner and release validator resolve those model filenames under the current study directory’s `models/` folder; the original model and runtime files are excluded from the public archive.\n\n'+readme[start:end])
(STUDY/'methodology.md').write_text('# Plate 001 methodology\n\n'+article[article.index('## What we tested'):article.index('## Overall results')].replace('../','')+ '\n## Analysis\n\n'+r['uncertainty_method']+'\n\n'+r['meaningful_drop_rule']+'\n\nThe full protocol was locked before inference in `study-protocol.json`. Official scores reject the complete response when it violates the contract or exhausts the budget. Prefix correctness is a post hoc diagnostic and never rescues official scores. Warmups, calibration responses and native benchmark samples are separate from the 1,680 scored trials.\n\n'+article[article.index('## Limitations'):article.index('## Reproduction and evidence')])
(STUDY/'inference-settings.json').write_text(json.dumps({k:m[k] for k in ['model','source_revision','llama_revision','inference','context_size','server_args','seed_rule','request_timeout_seconds','prompt_caching','grammar_constrained_output','trial_order','condition_order']},indent=2)+'\n')
(STUDY/'LICENSES.md').write_text('''# Licenses and third-party notices

Repository code, original study material, ledger, article and rendered study assets are supplied under the root MIT LICENSE. The source model’s generated outputs are preserved as observations, without adding rights to any independently protected text they might reproduce.

Anton and IBM Plex Mono are distributed under SIL Open Font License 1.1; copies are in `../../assets/fonts/Anton-OFL.txt` and `../../assets/fonts/IBMPlexMono-OFL.txt`, alongside the fonts. Publication assets include identical font files and notices.

The pinned source model card declares `apache-2.0`; its archived copy is `source-model-card.md` (matching the source manifest hash). The study uses Qwen/Qwen3-8B-Base at revision `49e3418fbbbca6ecbdf9608b4d22e5a407081db4`. No weights are bundled. Consult the pinned source model card and upstream license when obtaining or redistributing weights. Source hashes and attribution are in model-manifest.json. This archive’s MIT grant does not license upstream weights.

llama.cpp is an upstream MIT project. No upstream runtime source or binaries are bundled; reproduction fetches the recorded revision. npm dependencies have their own licenses and are installed from lockfiles. The publication builder uses marked (MIT). The original renderer uses @resvg/resvg-js, csv-parse and TypeScript; consult installed package notices. FFmpeg encodes the optional demo on the development system and is not redistributed here. The MP4 contains original study images and real output text, without audio or third-party footage.
''')
fonts=OUT/'fonts';fonts.mkdir(exist_ok=True)
for f in (REPO/'assets/fonts').iterdir():shutil.copy2(f,fonts/f.name)
shutil.copy2(STUDY/'weights/README.md',STUDY/'source-model-card.md') if (STUDY/'weights/README.md').exists() else None
subprocess.run(['node',str(REPO/'scripts/publication/render.mjs')],check=True)
print('Built article, methods, settings, release notes and three X posts from completed results.')
if __name__=='__main__':pass
