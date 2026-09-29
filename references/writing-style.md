# Writing style — 15 rules

Apply to every section of the report, TL;DR included. Rule text is the design spec §7
verbatim; the tag names the source demanding it. When two things fight, the stricter rule
wins.

## Voice & stance

1. **Write in classic style — name the actor.** (Pinker) Prose is a window; name the actor
   ("we fine-tuned", "the script computed"). Passive only when the actor is genuinely
   irrelevant.
   *Why:* hidden agency reads as evasion; the reader must know who did what.
2. **Calibrate certainty to the evidence.** (Agarwal et al. 2021; Dror et al. 2018) "X
   outperformed Y on this sweep (5 seeds)", never "X is better than Y". "Significant" only
   with a named test at stated α; otherwise "suggests / is consistent with". "Proves" ≈
   never.
   *Why:* an unqualified claim outlives the data that supported it and gets quoted
   without its conditions.
3. **No causal language for correlational results unless the design supports it.** (Schimel)
   *Why:* "caused" claims a controlled experiment; if there wasn't one, the verb is lying.

## Structure

4. **Structure OCAR — and lead with the verdict.** (Schimel) OCAR adapted; BLUF — the
   Resolution's verdict also appears in the TL;DR.
   *Why:* the reader decides in the first three sentences whether to keep reading; make
   those sentences carry the decision.
5. **Old before new; end on the stress.** (Gopen & Swan) Topic sentence first; one point
   per paragraph; the end of a sentence is the stress position for the important new
   point.
   *Why:* readers parse sentence ends with the most attention — wasting the stress
   position on a qualifier buries the point.

## Numbers

6. **No naked metrics.** (NeurIPS Paper Checklist; Agarwal et al. 2021) Units + uncertainty
   + n for every number; deltas vs a named baseline, absolute + relative ("+2.3 pts /
   +4.1% vs baseline").
   *Why:* a number without its interval and its n cannot be re-checked or compared — it is
   decoration.
7. **Round in prose, exact in tables.** (Tufte) Round in prose (71.3%), exact in tables
   (71.28); no false precision.
   *Why:* prose rounds for reading, tables keep the lookup value; extra decimals imply
   resolution the data does not have.
8. **Percentages state their base; translate magnitudes into concrete terms.** (Heath &
   Heath, *Making Numbers Count*) "12.5% of 240 examples" — say the base, then make the
   magnitude imaginable.
   *Why:* a percentage without its denominator can be resized by anyone who quotes it
   later.

## Honesty & completeness

9. **Negative/inconclusive results get the same care as wins.** (Henderson et al. 2018)
   *Why:* the null result is data; burying it guarantees someone re-runs it at full cost.
10. **Excluded runs listed with count + reason — no silent cherry-picking.** (Picard)
    *Why:* an unexplained exclusion is indistinguishable from rigging; the count lets the
    reader audit the n.
11. **Result (measured) explicitly separated from Interpretation (what we think).**
    (Pinker) **Result** (measured) explicitly separated from **Interpretation** (what we
    think).
    *Why:* classic style shows the reader the world before telling them what to conclude;
    blending the two launders opinion as measurement.
12. **Limitations and threats to validity stated near the results, not buried.** (Schimel)
    *Why:* a caveat three pages later is a caveat the reader never weighed.

## Mechanics

13. **Curse-of-knowledge guard.** (Pinker) Define acronyms at first use; assume a smart
    reader new to *this experiment*.
    *Why:* the report's audience is future-self plus colleagues outside the work — both
    lack this week's context.
14. **Cut metadiscourse and nominalizations.** (Zinsser; Strunk & White) Cut "it is
    interesting to note that…" and prefer "we measured" not "measurement was performed".
    *Why:* words about the writing are words not about the result; nominalizations hide
    the actor rule 1 just made you name.
15. **Don't do what Sand-Jensen satirizes: no postponing the point, no burying the
    interesting result mid-paragraph.** (Sand-Jensen)
    *Why:* his boring-literature rules are this skill's failure modes read backwards.
