---
name: experiment-reporting
description: "Use when reporting results of experiments the agent ran or was given — benchmarks, ablations, hyperparameter sweeps, model or LLM evals — with results in context or in markdown/CSV/JSON files. Produces a rigorous lab-notebook report: clean markdown by default, self-contained interactive HTML on request."
---

# Experiment Reporting

Turn experimental results into a report a future reader can trust and act on.
Statistics are computed by script, never in your head. Every number carries its
uncertainty and its baseline.

## Workflow

1. **Ingest** — Locate the results (conversation context, `.md` table, `.csv`,
   `.json`). Identify: the question, variants/configs, metrics, runs & seeds,
   and the baseline. Ask the user for the baseline if ambiguous.
2. **Compute** — If you have raw run-level data (one row per run), run:

   ```bash
   uv run --with numpy,scipy scripts/analyze.py INPUT [INPUT...] \
     --baseline NAME [--metrics m1,m2] [--holm] --out stats.json
   ```

   (script path = this skill's `scripts/analyze.py`). Cite stats.json numbers
   verbatim in the report. If input is already aggregated, use the given numbers
   and flag what is missing (e.g. "source reports no error bars").

3. **Draft** — Fill `templates/report-template.md` (in this skill). Follow the
   canonical structure; obey `references/writing-style.md`. Load
   `references/statistics.md` before writing section 4, and
   `references/reporting-standards.md` when unsure what a section needs.
4. **Verify** — Pass the quality checklist below before delivering. Fix and
   re-check; do not deliver a failing checklist.
5. **Render** — Deliver the markdown file next to the results (default). HTML
   when requested or when interaction genuinely helps:

   ```bash
   uv run --with markdown,pygments scripts/render_html.py \
     --content report.md --stats stats.json [--charts charts.json] --out report.html
   ```

   (renderer contract and delivery checks: `references/html-report.md`).
   Charts: BEFORE writing any chart code (plotly specs or matplotlib PNGs),
   invoke the `dataviz` skill and follow its design system. charts.json =
   `[{"div_id": "chart-1", "figure": {"data": [...], "layout": {...}}}]`.
   For markdown, charts are optional PNGs in a sibling `report-assets/` folder,
   relatively linked — only when a figure beats the table.

## Quality checklist (delivery gate)

- [ ] TL;DR: outcome + magnitude + uncertainty + decision
- [ ] Every number has uncertainty (or a flag that the source lacks it)
- [ ] Every comparison names its baseline; deltas absolute + relative
- [ ] n (runs/seeds) visible wherever aggregates appear
- [ ] "Significant" only with named test + α; effect sizes reported
- [ ] Per-run values present (table or appendix)
- [ ] Negative/inconclusive results and excluded runs reported with reasons
- [ ] Result vs interpretation explicitly separated
- [ ] Setup complete enough to rerun (config, environment, data, compute, code)
