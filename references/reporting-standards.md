# Reporting standards — evidence base

Every rule this skill enforces is traceable to a source below. When a report deviates from
a bullet here, the report is wrong, not the bullet. Grouped as in the design spec §3.

## Standards & checklists

### Pineau et al. 2021, "Improving Reproducibility in ML Research (NeurIPS 2019 Reproducibility Program)"
https://www.jmlr.org/papers/v22/20-303.html

- The Setup section must be complete enough to rerun the experiment: every hyperparameter, dataset detail, and evaluation protocol, not a summary of them.
- State the number of runs/seeds explicitly wherever an aggregate appears.
- Include a code pointer (script path, commit, or repo) so results can be re-derived, not just re-read.

### NeurIPS Paper Checklist
https://neurips.cc/public/guides/PaperChecklist

- Error bars must state what variability they capture (runs? seeds? data splits?) and how they were computed — std vs SEM vs CI is not interchangeable.
- Report experimental details that move numbers: compute resources, number of runs, intermediate results.
- Any claim of improvement must name its baseline and the conditions of comparison.

### ML Reproducibility Checklist v2.0
https://www.cs.mcgill.ca/~jpineau/ReproducibilityChecklist.pdf

- For every reported number, describe how it was produced: evaluation metric definition, baseline source (re-run or cited), and parameter counts.
- Describe datasets: sizes, splits, preprocessing, and any filtering.
- Mark clearly which baselines were re-run under identical conditions and which numbers were taken from elsewhere.

### Sandve et al. 2013, "Ten Simple Rules for Reproducible Computational Research" (PLOS Comp Bio)
https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003285

- Every result must be linked to the exact script and environment version that produced it.
- Record all inputs (including random states/seeds) with the result — no undocumented manual steps between data and reported number.
- A single command should regenerate the reported numbers from the recorded inputs.

## Statistical rigor

### Henderson et al. 2018, "Deep RL That Matters"
https://arxiv.org/abs/1709.06560

- Report all results, including failed, negative, and inconclusive ones — selective reporting is the core failure mode.
- Many trials; never compare single runs. Means without across-run variance are not results.
- Document the sources of discrepancy (seeds, hyperparameters, implementation details) when numbers disagree with prior work.

### Reimers & Gurevych 2017, "Reporting Score Distributions Makes a Difference"
https://arxiv.org/abs/1707.09861

- Compare distributions, not single scores; report per-run values, not only aggregates.
- Watch for bimodality: if the per-run distribution is not unimodal, the mean misleads — report the distribution.
- Prefer paired tests when runs share structure (same seeds / same evaluation data).

### Bouthillier et al. 2021, "Accounting for Variance in ML Benchmarks"
https://arxiv.org/abs/2103.03098

- Identify which variance source dominates — data sampling, initialization, hyperparameters, ordering — and say which one your error bars capture.
- Generalize conclusions over the dominant variance source, not over the one that was cheapest to measure.
- If variance is unquantified, more runs beat clever aggregation; say so rather than hiding it.

### Agarwal et al. 2021, "Deep RL at the Edge of the Statistical Precipice"
https://arxiv.org/abs/2108.13264

- Report point estimates with interval estimates — every performance claim carries its uncertainty.
- Prefer IQM/median over mean/max, especially with few runs.
- Use (stratified) bootstrap CIs for aggregate performance; a single ranking number is not a conclusion.

### Colas et al. 2018, "How Many Random Seeds Should I Use?"
https://arxiv.org/abs/1806.08295

- ~10+ seeds for reliable comparisons; 3 is too few — treat 3–4 run comparisons as provisional and flag them low-power.
- Report the confidence level actually attained by the conclusion given the number of runs, not the one wished for.
- Check that the conclusion does not flip when re-run with different seeds.

### Dror et al. 2018, "The Hitchhiker's Guide to Testing Statistical Significance in NLP"
https://aclanthology.org/D18-1242/

- Select the statistical test with a protocol (data type, assumptions, pairing) decided before looking at p-values.
- Report which test was used and why it fits the data.
- Correct for multiple comparisons when running more than one test (this skill's `--holm`).

### Picard 2021, "torch.manual_seed(3407) is all you need"
https://arxiv.org/abs/2109.08203

- Seed choice flips rankings: report exactly which seeds ran, and never implicitly cherry-pick them.
- List excluded runs with count and reason — no silent dropping.
- (The skill's deterministic default bootstrap seed, 3407, is the homage.)

### Appelbaum et al. 2018, JARS-Quant (APA)

- Effect sizes and confidence intervals for every claim, not just significance.
- Report the analysis plan with the results: tests used, α, and handling of missing/excluded data.
- A p-value alone is never the result; pair it with magnitude and interval.

## Structure & writing style

### Gopen & Swan 1990, "The Science of Scientific Writing"
https://cseweb.ucsd.edu/~swanson/papers/science-of-writing.pdf

- Old before new: start each sentence/paragraph from what the reader already holds.
- Topic position and stress position carry the logic — put the important new point at the end of the sentence, where stress falls.
- One point per paragraph; the topic sentence states it.

### Schimel 2012, *Writing Science* (OCAR: Opening, Challenge, Action, Resolution)

- Structure reports OCAR — and BLUF: the Resolution's verdict also appears in the TL;DR at the top.
- The Opening states why the experiment exists; the Resolution states what it changes.

### Pinker 2014, "Why Academics Stink at Writing" / *The Sense of Style*

- Classic style: prose is a window — name the actor ("we fine-tuned", "the script computed"); passive only when the actor is genuinely irrelevant.
- Fight the curse of knowledge: define acronyms at first use; assume a smart reader new to *this experiment*.

### Sand-Jensen 2007, "How to write consistently boring scientific literature" (Oikos; inverse guide)

- Read as an inverse guide: do not postpone the point, do not bury the interesting result mid-paragraph, do not omit the implications.
- Anything the satire recommends doing to make writing boring is a bug in a report.

### Tufte, *The Visual Display of Quantitative Information*

- Tables for lookup (exact values), figures for comparison (shape of the difference).
- A chart earns its place only if it beats the table; sparklines and small multiples for many-series data.

## Tooling conventions

### HELM (Liang et al. 2022)
https://arxiv.org/abs/2211.09110

- Per-instance/per-run data behind every aggregate stays accessible (this skill's Appendix).
- Uncertainty is shown on aggregate numbers by default, not on request.

### Biderman et al. 2024, "Lessons from the Trenches on Reproducible Evaluation of LLMs"
https://arxiv.org/abs/2404.01543

- Bootstrapped stderr (here: bootstrap CI) on reported metrics by default.
- Pin and report versions — models, datasets, code — and document implementation decisions that move numbers.

### W&B Reports (panels + markdown notes structure)

- Interleave panels (tables/charts) with short markdown notes that interpret them — the model this skill's HTML report follows: tiles, charts, and prose in one scrollable document.
- Keep the split clean: panels are generated from logged data, notes are authored prose. Numbers come from tooling (here: `stats.json`), interpretation comes from the writer.

## One-line distillation

**lead with the decision; every number carries its uncertainty and its baseline; per-run values stay visible; the claim states its test; negatives are reported; the setup is complete enough to rerun.**
