# Statistics — decision recipes

These recipes mirror `scripts/analyze.py` exactly. Never hand-compute statistics and never
invent numbers the script did not emit: run it and cite `stats.json`. All flag strings,
test names, and defaults below are the script's literal values.

## Recipe 0 — Never compare single runs

- One run per variant is noise, not a result (Henderson et al. 2018; Bouthillier et al.
  2021; Reimers & Gurevych 2017). Treat a comparison as testable only from n ≥ 3 per side
  (below that the script still emits numbers, but the report uses them descriptively), and
  as trustworthy only from n ≥ 10 per side (Colas et al. 2018: ~10+ seeds; 3 is too few).
- If only single runs exist, report the descriptive values with the flags below and no
  significance language.

## Recipe 1 — Small-n flags (exact strings from analyze.py)

Flags attach to a comparison and fire when **either** side (variant or baseline) crosses
the threshold:

- any side n < 3 → flags contain `no statistical inference possible (n<3)` — report
  descriptive values only: per-variant aggregates and per-run values, no test, no
  "significant", no p-value prose.
- 3 ≤ n < 5 on any side → flags contain `low-power: n<5, interpret cautiously` — the
  comparison may be reported, but the report must carry the caveat and hedge the
  conclusion ("suggests", not "establishes").
- n < 3 implies both flags appear together. Reproduce the flag text character-for-character
  when citing it in the report.

## Recipe 2 — Aggregates and uncertainty

Per variant × metric the script emits: `n`, `values` (per-run), `mean`, `std`, `sem`
(ddof=1; both null when n = 1), `median`, `min`, `max`, `iqm` (`scipy.stats.trim_mean(values,
0.25)`, emitted only when n ≥ 4), and `ci95`.

- Default uncertainty: mean ± 95% percentile bootstrap CI over runs — 10,000 resamples
  (`--resamples`, default 10000), deterministic seed 3407 (`--bootstrap-seed`, default
  3407 — the Picard homage), CI = 2.5th/97.5th percentiles of the resampled means.
- Prefer median/IQM over the mean for small n or heavy tails (Agarwal et al. 2021).
- Always state what the interval varies over: runs/seeds — never leave "error bars"
  ambiguous (NeurIPS Paper Checklist).
- Δ is reported both ways: absolute (`mean_v − mean_b`) and relative (`delta_rel` = Δ ÷
  baseline mean; omitted when the baseline mean is 0).

## Recipe 3 — Comparisons vs baseline

- Test selection (`--paired auto`, the default): paired-by-seed t-test
  (`scipy.stats.ttest_rel`) when the variants share ≥ 3 seeds AND the variant side has
  n ≥ 3; test name in output: `paired t-test (seed-matched, n={k})`. Otherwise Welch's
  t-test (`ttest_ind`, `equal_var=False`); test name: `Welch's t-test`.
  `--paired never` forces Welch's even when seeds align.
- Effect size: Cohen's d — paired form (mean of per-seed differences ÷ std of differences,
  ddof=1) for the paired test; pooled-SD form otherwise. Emitted as `cohens_d`; null when
  the denominator is 0. Report it with every comparison (Appelbaum et al., JARS-Quant).
- Report test name + p + Cohen's d every time, quoting `stats.json`.
- More than one comparison in the family (multiple variants and/or metrics): consider
  `--holm`, which applies Holm-Bonferroni across all comparisons and adds `p_holm` to
  each; note the adjustment in the report when used.
- The word "significant" only with a named test and a stated α — default α = 0.05. The
  script never labels significance; the report must supply test + α when it uses the word.

## Recipe 4 — Already-aggregated inputs

- When the input is already aggregated (a paper table, a dashboard mean with no per-run
  data), use the given numbers as-is. Never fabricate per-run data or run tests you lack
  the runs for.
- State what uncertainty is missing, e.g. "source reports no error bars" — that sentence
  is mandatory when the source lacks intervals.

## Recipe 5 — Bimodality check

- Before trusting a mean, eyeball the per-run `values` in `stats.json`. If the spread is
  not unimodal (two clusters, a gap, a straggler), report the distribution — the per-run
  table — and say the mean is not representative (Reimers & Gurevych 2017).

## Invocation (always via uv)

```
uv run --with numpy,scipy scripts/analyze.py INPUT [INPUT...] --baseline NAME \
  [--metrics m1,m2] [--paired auto|never] [--bootstrap-seed N] [--resamples N] \
  [--holm] [--out stats.json]
```

`stats.json` is the single citable source for Section 4 (Statistical assessment): mirror
its numbers, never recompute them.
