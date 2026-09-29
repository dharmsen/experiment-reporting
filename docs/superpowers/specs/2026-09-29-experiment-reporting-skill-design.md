# Experiment Reporting Skill — Design Spec

Date: 2026-09-29
Status: Approved design (brainstorming complete; ready for implementation planning)

## 1. Goal

A Claude Code skill that turns experimental results — given in conversation context, a
markdown table, or CSV/JSON files — into a rigorous, lab-notebook-style report of what the
experiment was about and what the results are. Default output: clean markdown. On request:
a fully offline, self-contained interactive HTML report.

## 2. Requirements (user decisions)

| Decision | Choice |
|---|---|
| Primary domain | ML/AI experiments (benchmarks, ablations, sweeps, evals) |
| Audience | Future-self lab notebook; legible to colleagues less involved in the work |
| Statistics | Compute when given raw run-level data (Python via `uv`); present as-is when input is already aggregated, flagging what's missing |
| Output policy | Markdown by default; interactive HTML on demand or when interaction genuinely helps |
| HTML tech | Single self-contained `.html`, plotly.js embedded inline (~3–5 MB), works offline from `file://` |
| Structure | Approach B: lean `SKILL.md` + `references/` + `scripts/` + `templates/` + `assets/` |

Standing constraint from user global config: **always use `uv`** for Python environment
commands (`uv run --with numpy,scipy …` — no persistent environment needed).

## 3. Evidence base

The skill's rules are traceable to these sources; the distillation lives in
`references/reporting-standards.md`.

Standards & checklists:
- Pineau et al. 2021, "Improving Reproducibility in ML Research (NeurIPS 2019 Reproducibility Program)" — https://www.jmlr.org/papers/v22/20-303.html
- NeurIPS Paper Checklist — https://neurips.cc/public/guides/PaperChecklist (experimental
  details; error bars must state what variability they capture, how computed, std vs SEM; compute resources)
- ML Reproducibility Checklist v2.0 — https://www.cs.mcgill.ca/~jpineau/ReproducibilityChecklist.pdf
- Sandve et al. 2013, "Ten Simple Rules for Reproducible Computational Research" (PLOS Comp Bio)

Statistical rigor:
- Henderson et al. 2018, "Deep RL That Matters" — https://arxiv.org/abs/1709.06560 (report all results, many trials, never single runs)
- Reimers & Gurevych 2017, "Reporting Score Distributions Makes a Difference" — https://arxiv.org/abs/1707.09861 (compare distributions, watch bimodality)
- Bouthillier et al. 2021, "Accounting for Variance in ML Benchmarks" — https://arxiv.org/abs/2103.03098 (variance: sampling, init, hyperparameters)
- Agarwal et al. 2021, "Deep RL at the Edge of the Statistical Precipice" — https://arxiv.org/abs/2108.13264 (IQM/median over mean/max, stratified bootstrap CIs, point + interval)
- Colas et al. 2018, "How Many Random Seeds Should I Use?" — https://arxiv.org/abs/1806.08295 (~10+ seeds; 3 is too few)
- Dror et al. 2018, "The Hitchhiker's Guide to Testing Statistical Significance in NLP" — https://aclanthology.org/D18-1242/ (test-selection protocol)
- Picard 2021, "torch.manual_seed(3407) is all you need" — https://arxiv.org/abs/2109.08203 (seed choice flips rankings; no implicit cherry-picking)
- Appelbaum et al. 2018, JARS-Quant (APA) — effect sizes + CIs for every claim, not just significance

Structure & writing style:
- Gopen & Swan 1990, "The Science of Scientific Writing" — https://cseweb.ucsd.edu/~swanson/papers/science-of-writing.pdf (old-before-new, topic/stress position)
- Schimel 2012, *Writing Science* (OCAR: Opening, Challenge, Action, Resolution)
- Pinker 2014, "Why Academics Stink at Writing" / *The Sense of Style* (classic style, curse of knowledge)
- Sand-Jensen 2007, "How to write consistently boring scientific literature" (Oikos; inverse guide)
- Tufte, *The Visual Display of Quantitative Information* (tables for lookup, figures for comparison, sparklines, small multiples)

Tooling conventions:
- HELM (Liang et al. 2022) — https://arxiv.org/abs/2211.09110 (per-instance data released, uncertainty on aggregates)
- Biderman et al. 2024, "Lessons from the Trenches on Reproducible Evaluation of LLMs" (lm-eval-harness; bootstrapped stderr by default) — https://arxiv.org/abs/2404.01543
- W&B Reports (panels + markdown notes structure)

One-line distillation: **lead with the decision; every number carries its uncertainty and
its baseline; per-run values stay visible; the claim states its test; negatives are
reported; the setup is complete enough to rerun.**

## 4. File layout

```
experiment-reporting/
├── SKILL.md                 # workflow + quality checklist, kept lean
├── references/
│   ├── reporting-standards.md  # Section 3's distillation with citations
│   ├── statistics.md           # decision recipes analyze.py encodes
│   ├── writing-style.md        # Section 7's guidelines, sourced
│   └── html-report.md          # HTML report spec: structure, dataviz deferral, embedding rules
├── scripts/
│   ├── analyze.py           # stats computation
│   └── render_html.py       # single-file offline HTML builder
├── templates/
│   └── report-template.md   # markdown skeleton with guidance comments
├── assets/
│   └── plotly.min.js        # vendored, pinned version, embedded per report
└── docs/superpowers/specs/  # this spec
```

Install: symlink `~/.claude/skills/experiment-reporting` → this directory.

## 5. SKILL.md

Frontmatter:
- `name: experiment-reporting`
- `description:` trigger on reporting results of experiments the agent ran or was given
  (benchmarks, ablations, evals, sweeps) from in-context results, markdown tables, or
  CSV/JSON run data; produces markdown (default) or interactive HTML.

Workflow (numbered steps in the skill body):
1. **Ingest** — locate results (context / `.md` / `.csv` / `.json`); identify: question,
   variants/configs, metrics, runs & seeds, baseline.
2. **Compute** — raw run-level data → `uv run --with numpy,scipy scripts/analyze.py …`;
   aggregated input → use as given; flag missing uncertainty ("source reports no error bars").
3. **Draft** — fill `templates/report-template.md` following the canonical structure
   (Section 6) and writing-style rules (Section 7).
4. **Verify** — run the quality checklist (below) before delivering.
5. **Render** — markdown by default; HTML on request or when interaction genuinely helps,
   via `scripts/render_html.py`. Before writing any chart code (plotly specs or matplotlib
   PNGs), invoke the **dataviz** skill for design tokens and palette.

Quality checklist (the delivery gate):
- [ ] TL;DR states outcome + magnitude + uncertainty + decision
- [ ] Every reported number has uncertainty (or a flag that the source lacks it)
- [ ] Every comparison names its baseline; deltas absolute + relative
- [ ] n (runs/seeds) visible wherever aggregates appear
- [ ] "Significant" only with named test + α; effect sizes reported
- [ ] Per-run values present (table or appendix)
- [ ] Negative/inconclusive results and excluded runs reported with reasons
- [ ] Result vs interpretation explicitly separated
- [ ] Setup complete enough to rerun (config, environment, data, compute, code pointer)

## 6. Canonical report structure (both formats)

```
# Title — verdict in one line
TL;DR: outcome + magnitude + uncertainty + decision (2-3 sentences)
1. Question & hypothesis     — why this experiment exists
2. Setup                     — config table, environment/versions, data, compute, code pointer
3. Results                   — summary table (aggregate ± uncertainty), per-run table, comparison charts
4. Statistical assessment    — tests, effect sizes, small-n flags, caveats
5. Interpretation            — what we think happened, labeled as interpretation
6. Decision & next steps     — what this changes, what runs next
Appendix                    — full per-run data, links, excluded runs
```

## 7. Writing style guidelines (`references/writing-style.md`)

Voice & stance:
1. Classic style (Pinker): prose is a window; name the actor ("we fine-tuned", "the script
   computed"). Passive only when the actor is genuinely irrelevant.
2. Calibrated certainty: "X outperformed Y on this sweep (5 seeds)", never "X is better
   than Y". "Significant" only with a named test at stated α; otherwise "suggests / is
   consistent with". "Proves" ≈ never.
3. No causal language for correlational results unless the design supports it.

Structure:
4. OCAR adapted (Schimel); BLUF — the Resolution's verdict also appears in the TL;DR.
5. Old before new (Gopen & Swan); topic sentence first; one point per paragraph; the end
   of a sentence is the stress position for the important new point.

Numbers:
6. No naked metrics: units + uncertainty + n for every number; deltas vs a named baseline,
   absolute + relative ("+2.3 pts / +4.1% vs baseline").
7. Round in prose (71.3%), exact in tables (71.28); no false precision.
8. Percentages state their base ("12.5% of 240 examples"); translate magnitudes into
   concrete terms (Heath & Heath, *Making Numbers Count*).

Honesty & completeness:
9. Negative/inconclusive results get the same care as wins.
10. Excluded runs listed with count + reason — no silent cherry-picking (Picard).
11. **Result** (measured) explicitly separated from **Interpretation** (what we think).
12. Limitations and threats to validity stated near the results, not buried.

Mechanics:
13. Curse-of-knowledge guard (Pinker): define acronyms at first use; assume a smart
    reader new to *this experiment*.
14. Cut metadiscourse ("it is interesting to note that…") and nominalizations ("we
    measured" not "measurement was performed") — Zinsser; Strunk & White.
15. Don't do what Sand-Jensen satirizes: no postponing the point, no burying the
    interesting result mid-paragraph.

## 8. `scripts/analyze.py` contract

Invocation (agent-run, never hand-computed stats):
```
uv run --with numpy,scipy scripts/analyze.py INPUT [INPUT…] \
  [--baseline NAME] [--metrics m1,m2] [--paired auto|never] \
  [--bootstrap-seed N] [--resamples N] [--holm] [--out stats.json]
```

Input: CSV or JSON run tables. Canonical (wide) format: one row per run with columns
`run_id, variant, seed, metric1, metric2, …`. Long format also accepted (one row per
run × metric, with `metric` and `value` columns). JSON = array of run objects. Missing
seeds allowed (recorded in output).

Computation per variant × metric:
- n, per-run values, mean, std, SEM, median, IQM (interquartile mean), min/max
- 95% percentile bootstrap CI over runs (default 10,000 resamples,
  deterministic default seed 3407 — homage to Picard 2021; overridable)

Pairwise vs baseline (per metric):
- Δ absolute and relative
- Test: paired-by-seed t-test when variants share ≥ 3 seeds, else Welch's t-test
  (`--paired never` forces unpaired); test name recorded in output
- Effect size: Cohen's d (paired variant when paired)
- Flags: `n < 5` → "low-power, interpret cautiously"; `n < 3` → "no statistical inference
  possible"; `--holm` applies Holm-Bonferroni adjustment across the comparison family and
  notes it in output

Output: single JSON object (stdout or `--out`):
```
{
  "meta": { "inputs": [...], "baseline": "...", "bootstrap": {"resamples": 10000, "seed": 3407}, "generated": "ISO-8601" },
  "variants": { "<variant>": { "<metric>": { "n": 5, "values": [...], "mean": …, "std": …,
      "sem": …, "median": …, "iqm": …, "min": …, "max": …,
      "ci95": [lo, hi] } } },
  "comparisons": [ { "variant": …, "baseline": …, "metric": …, "delta": …, "delta_rel": …,
      "test": "paired t-test (seed-matched, n=5)", "p": …, "cohens_d": …, "flags": [...] } ]
}
```

Non-goals: no plotting, no report text generation — numbers only, so the JSON is citable
by both renderers.

## 9. `scripts/render_html.py` contract

Invocation:
```
uv run --with markdown,pygments scripts/render_html.py --content report.md \
  --stats stats.json [--charts charts.json] [--out report.html]
```

- Renders the drafted markdown to HTML (python-markdown, tables + fenced-code extensions).
- Summary tiles row (metric, value, Δ vs baseline, n) generated from `stats.json`.
- `charts.json` = list of plotly figure specs (JSON); each rendered into its section via
  the **embedded** `assets/plotly.min.js` (inlined into the file; pinned version recorded).
- Progressive disclosure: TL;DR + summary tiles always visible; per-run tables and
  methodology sections collapsible (`<details>`); no external requests — must work from
  `file://` with zero network.
- Chart visuals follow the dataviz skill's system (the agent writes specs at draft time
  under dataviz guidance; the renderer only embeds them).

## 10. Markdown report design

Same canonical structure; tables-first (summary table with aggregate ± uncertainty, plus
per-run table). Charts optional: matplotlib PNGs into a sibling `report-assets/` folder,
relatively linked — generated only when a figure beats the table (agent decision, per
dataviz heuristics).

## 11. Validation

Fixture: 3 variants (5/5/3 seeds — method_b missing seeds 3 and 5), one metric with an
obvious gap → run the skill end-to-end → verify:
1. `stats.json` numerically correct (hand-checked once: mean/std/CI/p-value sanity)
2. `report.md` follows the canonical structure and passes the quality checklist
3. `report.html` opens offline from `file://`, charts render, tiles show Δ and n
4. Flags fire correctly (`n<5` on the 3-seed variant)
5. Final validation follows the superpowers writing-skills process before the skill is
   considered done

Success criteria: the five checks above pass on the fixture, and the skill triggers
correctly on "report these results" style requests.

## 12. Out of scope (YAGNI)

PDF/LaTeX output; full-paper manuscript mode; W&B/MLflow/TensorBoard integration; live
dashboards or servers; cross-project multi-experiment aggregation; wet-lab/CONSORT-style
reporting; automatic experiment *execution* (this skill reports, it does not run
experiments).
