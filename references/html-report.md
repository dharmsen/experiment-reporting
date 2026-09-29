# HTML report contract

Markdown is the default output. Produce HTML on request, or when interaction genuinely
helps (hover inspection of per-run values, collapsible depth). The renderer is
`scripts/render_html.py`; this file is the binding contract between the drafting agent and
the renderer.

## What the drafting agent must supply

- `report.md` — the drafted report, from `templates/report-template.md`, following the
  canonical structure (spec §6) and `references/writing-style.md`.
- `stats.json` — from `scripts/analyze.py`; the single source of every number shown.
- `charts.json` (optional) — a list of plotly figure specs (JSON), one per chart, placed
  in the section they belong to. **Author chart specs at draft time under the dataviz
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
- **Data inline as JSON.** `stats.json`'s content is embedded in the document, not
  referenced.
- **Markdown rendered** via python-markdown with the `tables` and `fenced-code`
  extensions — the report's tables and code blocks survive intact.
- **Summary tiles row generated from `stats.json`:** one tile per key comparison showing
  metric, value, Δ vs baseline, n, and flags.
- **Progressive disclosure via `<details>`:** TL;DR + summary tiles are always visible;
  per-run tables and methodology sections are collapsible; the Appendix (full per-run
  data, links, excluded runs) sits behind `<details>` so depth is one click away, not
  forced on every reader.
- **Zero external requests** of any kind — fonts, scripts, images, analytics included.

## Checks before delivering an HTML report

- Open the file from `file://` with networking blocked: charts render, tiles show Δ and n.
- Every number on the page traces to `stats.json` (or is flagged as source-reported).
- No chart spec was written without dataviz guidance.
