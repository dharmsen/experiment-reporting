# Training-recipe sweep (baseline vs method_a vs method_b) — method_a ships; method_b unresolved

**TL;DR:** method_a beats the baseline recipe by +3.1 pts mean accuracy (0.736 vs 0.705, n=5 per side; 95% bootstrap CIs [0.730, 0.742] vs [0.701, 0.709], no overlap; paired t-test, seed-matched, n=5: p=4.0e-5). It also lowers mean eval loss by 0.052 (p=6.6e-7). We are promoting method_a to the default recipe for the main sweep. method_b's +1.3 pts is not statistically significant (p=0.106) and its comparison carries the script flag `low-power: n<5, interpret cautiously` (n=3 completed runs) — it suggests, but does not establish, an improvement.

## 1. Question & hypothesis

Does either of two candidate training-recipe changes (method_a, method_b) improve held-out accuracy over the current recipe (baseline) without increasing loss, on our fixed evaluation set? If one does, we switch the default recipe used by the production sweep; if neither does, we keep the baseline and stop paying the tuning cost. Hypothesis, stated before the runs: both changes improve accuracy by at least +1 point; we would consider a variant "better" only if the improvement is statistically detectable at α=0.05 against this baseline.

## 2. Setup

Complete enough to rerun: same data, same model, same seeds; only the recipe differs.

| Variant | What differs from baseline |
|---|---|
| baseline | Current production recipe: SGD (momentum 0.9), lr 1e-2, cosine decay over 40 epochs, batch 128 |
| method_a | Baseline + label smoothing 0.1 and lr warmup (5 linear epochs) |
| method_b | Baseline + mixup (α=0.2), same schedule otherwise |

- **Task & model:** image classification; ResNet-18 (11.7M parameters), trained from scratch.
- **Data:** 45,000 train / 10,000 eval examples, fixed split, standard normalization; no filtering. The eval set is frozen and shared across all runs.
- **Metrics:** accuracy = top-1 fraction on the 10,000-example eval set; loss = mean cross-entropy on the same set. Both computed after the final epoch.
- **Runs & seeds:** seeds 1–5 per variant; the seed controls initialization, shuffling, and augmentation draw. Planned 15 runs; 13 completed (see Appendix for the 2 failures).
- **Environment:** Python 3.12.6, torch 2.5.1+cu124, CUDA 12.4, numpy 2.1.1; results analyzed with this skill's `scripts/analyze.py` (bootstrap: 10,000 resamples, seed 3407).
- **Compute:** 1x NVIDIA RTX 4090 (24 GB); ~18 min per run; ~4.1 GPU-hours for 13 completed runs.
- **Code pointer:** `sweeps/run_sweep.py` at repo commit `a1b2c3d`; raw run table at `tests/fixtures/sweep.csv` (this skill's repo). One command regenerates every number in this report from that table:

```bash
uv run --with numpy,scipy scripts/analyze.py tests/fixtures/sweep.csv \
  --baseline baseline --out examples/sweep-stats.json
```

## 3. Results

Measured values below come verbatim from `examples/sweep-stats.json`; every interval is a 95% percentile bootstrap CI over runs/seeds (10,000 resamples), which is the only variability these numbers capture — there is no data-split or cross-run protocol variance here.

Mean accuracy by variant (higher is better):

| Variant | n | Mean accuracy | 95% CI (over runs) | Median | IQM |
|---|---|---|---|---|---|
| baseline | 5 | 0.705 | [0.7006, 0.7094] | 0.705 | 0.7050 |
| method_a | 5 | 0.736 | [0.7300, 0.7420] | 0.738 | 0.7367 |
| method_b | 3 | 0.7183 | [0.7150, 0.7220] | 0.718 | — (n<4, omitted) |

Mean eval loss by variant (lower is better):

| Variant | n | Mean loss | 95% CI (over runs) | Median |
|---|---|---|---|---|
| baseline | 5 | 0.5526 | [0.5460, 0.5586] | 0.553 |
| method_a | 5 | 0.5006 | [0.4946, 0.5066] | 0.499 |
| method_b | 3 | 0.5300 | [0.5270, 0.5330] | 0.530 |

Deltas vs the named baseline (absolute and relative, from stats.json): method_a +0.0310 accuracy (+4.4% relative) and −0.0520 loss (−9.4%); method_b +0.0133 accuracy (+1.9%) and −0.0226 loss (−4.1%).

Per-run accuracy by seed (per-run loss is in the Appendix):

| Seed | baseline | method_a | method_b |
|---|---|---|---|
| 1 | 0.712 | 0.741 | 0.718 |
| 2 | 0.698 | 0.725 | 0.722 |
| 3 | 0.705 | 0.738 | — (run failed) |
| 4 | 0.701 | 0.731 | 0.715 |
| 5 | 0.709 | 0.745 | — (run failed) |

The rendered HTML version of this report includes one figure: mean accuracy per variant as a bar chart with 95% CI error bars (the intervals vary over runs/seeds, as above).

## 4. Statistical assessment

All numbers in this section are quoted from `examples/sweep-stats.json`; nothing was hand-computed. Both variants share seeds with the baseline, so the script selected the paired-by-seed t-test; effect sizes are Cohen's d (paired form); CIs are 95% percentile bootstrap over runs (10,000 resamples, seed 3407). Significance is judged at α=0.05.

| Variant | Metric | Δ absolute | Δ relative | Test | p | Cohen's d | Flags |
|---|---|---|---|---|---|---|---|
| method_a | accuracy | +0.0310 | +4.40% | paired t-test (seed-matched, n=5) | 3.991e-05 | 8.77 | — |
| method_a | loss | −0.0520 | −9.41% | paired t-test (seed-matched, n=5) | 6.632e-07 | −24.51 | — |
| method_b | accuracy | +0.0133 | +1.89% | paired t-test (seed-matched, n=3) | 0.1063 | 1.63 | `low-power: n<5, interpret cautiously` |
| method_b | loss | −0.0226 | −4.09% | paired t-test (seed-matched, n=3) | 0.0767 | −1.96 | `low-power: n<5, interpret cautiously` |

- **method_a is significant.** The +3.1-point accuracy gain is significant (paired t-test, seed-matched, n=5, p=3.991e-05, α=0.05), and so is the loss reduction (p=6.632e-07). The two variants' accuracy CIs do not overlap ([0.7300, 0.7420] vs [0.701, 0.7094]). Every method_a seed beats every baseline seed (minimum 0.725 vs maximum 0.712), so the direction is consistent across all 5 pairs.
- **method_b is not significant.** Its +1.3-point gain does not clear α (p=0.1063), and stats.json flags the comparison `low-power: n<5, interpret cautiously` because the variant side has n=3 completed runs. We report it descriptively: the gain suggests an improvement but does not establish one, and n=3 is well below the ~10 seeds recommended for a trustworthy comparison (Colas et al. 2018).
- **Multiple comparisons.** This family contains 4 tests and we did not apply the script's `--holm` correction. For transparency: method_a's accuracy p (3.991e-05) survives even a Bonferroni-style bound of 4×p = 1.6e-4, still far below α=0.05; the method_b p-values are not significant before any correction.
- **Effect-size caveat.** The Cohen's d values (8.77, −24.51) are enormous because between-seed variance is tiny relative to the paired differences; with n=5 these estimates are unstable. Read the CIs and p-values for magnitude and confidence; the d values are reported for completeness (JARS-Quant), not as trustworthy magnitudes.
- **Distribution check.** The per-run values within each variant are unimodal with no stragglers or gaps (accuracy spread ≤ 0.020 within every variant), so the means are representative of the distributions (Recipe 5; Reimers & Gurevych 2017).
- **Missing uncertainty:** none — every number above comes from run-level data with 3–5 runs per side.

## 5. Interpretation

*This section is what we think happened, separated from the measured results above.*

method_a's change (label smoothing + warmup) appears to help optimization, not just calibration: accuracy and loss improve together, on every seed, by margins far outside the run-to-run noise we measured. The mechanism we find plausible is that warmup stabilizes the early large-learning-rate phase and label smoothing reduces overconfident gradients; both would be consistent with the observed loss drop being proportionally larger (−9.4%) than the accuracy gain (+4.4%).

method_b's mixup runs trend the right direction (all 3 completed seeds land above the baseline median), but with two crashed runs we cannot distinguish a small real effect from noise at this n. The failure itself (NaN loss mid-training, see Appendix) may correlate with mixup's harder targets, which would be an additional practical strike against it if it recurs — though we have not established that.

## 6. Decision & next steps

- **Decision:** promote method_a to the default recipe for the production sweep. The evidence: +3.1 pts accuracy, significant (paired t-test, seed-matched, n=5, p=3.991e-05, α=0.05), with a simultaneous loss improvement.
- **Do not adopt method_b** on this evidence; its gain is not significant and the comparison is flagged low-power.
- **Next runs:** fix the method_b crash, then re-run method_b (and baseline alongside it) to 10 seeds before revisiting the decision; re-analyze with `--holm` since the family will then hold multiple comparisons.
- **Archive:** `examples/sweep-stats.json` (single source for every number here), this report, and the rendered HTML sit together in `examples/`.

## Appendix

Full per-run data (13 completed runs), verbatim from the input table `tests/fixtures/sweep.csv`:

| run_id | Variant | Seed | Accuracy | Loss |
|---|---|---|---|---|
| 1 | baseline | 1 | 0.712 | 0.541 |
| 2 | baseline | 2 | 0.698 | 0.562 |
| 3 | baseline | 3 | 0.705 | 0.553 |
| 4 | baseline | 4 | 0.701 | 0.558 |
| 5 | baseline | 5 | 0.709 | 0.549 |
| 6 | method_a | 1 | 0.741 | 0.492 |
| 7 | method_a | 2 | 0.725 | 0.511 |
| 8 | method_a | 3 | 0.738 | 0.499 |
| 9 | method_a | 4 | 0.731 | 0.506 |
| 10 | method_a | 5 | 0.745 | 0.495 |
| 11 | method_b | 1 | 0.718 | 0.530 |
| 12 | method_b | 2 | 0.722 | 0.527 |
| 13 | method_b | 4 | 0.715 | 0.533 |

**Incomplete runs (2, with reasons):** method_b seed 3 and method_b seed 5 crashed with NaN loss during training (epochs 31 and 44 respectively) and never reached evaluation, so they contribute no metric values. They are excluded from every aggregate above; that exclusion is why method_b has n=3 while the other variants have n=5. No run was dropped for underperforming.

**Reproduce:** the command in Section 2 regenerates `examples/sweep-stats.json` from the raw table; `scripts/render_html.py` rebuilds the HTML from this file, that stats file, and `examples/sweep-charts.json`.
