# HTML report contract

Markdown is the default output. Produce HTML on request, or when interaction genuinely
helps (hover inspection of per-run values, collapsible depth). The renderer is
`scripts/render_html.py`; this file is the binding contract between the drafting agent and
the renderer.

## What the drafting agent must supply

- `report.md` — the drafted report, from `templates/report-template.md`, following the
  canonical structure (spec §6) and `references/writing-style.md`.
- `stats.json` — from `scripts/analyze.py`; the single source of every number shown.
- `charts.json` (optional) — a list of plotly figure specs (JSON), one per chart; give an
  entry a `"section"` key set to its target section's `<h2>` heading text and the renderer
  will place it there. **Author chart specs at draft time under the dataviz
  skill's system** (invoke dataviz before writing any chart spec — design tokens, palette,
  chart-type choice). The renderer does not design, restyle, or validate charts; it only
  embeds the specs you hand it.

## Command (always via uv)

```
uv run --with markdown,pygments scripts/render_html.py --content report.md \
  --stats stats.json [--charts charts.json] [--out report.html]
```

## What the renderer guarantees

- **Single self-contained file.** One `.html` — no sibling assets, no CDN, no fetched
  data. Must open from `file://` and render fully with zero network.
- **plotly.min.js embedded inline** from `assets/plotly.min.js` (vendored, pinned version
  recorded in the file and in `assets/PLOTLY_VERSION`; currently 3.0.1).
- **No stats blob — numbers via tiles and text.** `stats.json`'s content is not embedded
  as a JSON blob; its numbers reach the page through the summary tiles and the drafted
  report text (which quotes them).
- **Markdown rendered** via python-markdown with the `tables` and `fenced-code`
  extensions — the report's tables and code blocks survive intact.
- **Charts placed by `"section"`.** A charts.json entry whose `"section"` value matches
  an h2 heading's text renders at the top of that section, immediately after the
  heading; entries with no `"section"` key (or whose section matches no heading) render
  after the tiles and content.
- **Summary tiles row generated from `stats.json`:** one tile per key comparison showing
  metric, value, Δ vs baseline, n, and flags; the row renders above the report body, so
  the decision leads the page.
- **Progressive disclosure via `<details>`:** the Appendix is the only collapsible
  section — it renders behind `<details>` so depth is one click away — while the TL;DR,
  tiles, and every other section render expanded.
- **Zero external requests** of any kind — fonts, scripts, images, analytics included.

## Checks before delivering an HTML report

- Open the file from `file://` with networking blocked: charts render, tiles show Δ and n.
- Every number on the page traces to `stats.json` (or is flagged as source-reported).
- No chart spec was written without dataviz guidance.
