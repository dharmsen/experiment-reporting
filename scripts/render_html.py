#!/usr/bin/env python3
"""Build a self-contained offline HTML report from drafted markdown + stats.json.

Usage:
  uv run --with markdown,pygments scripts/render_html.py --content report.md \
      --stats stats.json [--charts charts.json] [--out report.html]
"""
import json
import re
import sys
from pathlib import Path

PAGE_CSS = """
:root { --ink:#1a1a1a; --muted:#5f6672; --bg:#ffffff; --accent:#2563eb;
        --good:#0f7b46; --warn:#9a6700; --line:#e4e7eb; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif; color: var(--ink);
       background: var(--bg); max-width: 60rem; margin: 0 auto; padding: 2rem 1.25rem;
       line-height: 1.55; }
h1 { font-size: 1.7rem; line-height: 1.25; }
h2 { font-size: 1.25rem; border-bottom: 1px solid var(--line); padding-bottom: .3rem; }
table { border-collapse: collapse; margin: 1rem 0; }
th, td { border: 1px solid var(--line); padding: .35rem .6rem; text-align: left; }
td:nth-child(n+2) { text-align: right; font-variant-numeric: tabular-nums; }
.tiles { display: flex; flex-wrap: wrap; gap: .75rem; margin: 1.25rem 0; }
.tile { border: 1px solid var(--line); border-radius: 8px; padding: .6rem .9rem;
        min-width: 11rem; }
.tile .k { color: var(--muted); font-size: .8rem; }
.tile .v { font-size: 1.35rem; font-weight: 600; }
.tile .d { font-size: .85rem; }
.d.up { color: var(--good); } .d.down { color: var(--warn); }
details { border: 1px solid var(--line); border-radius: 8px; padding: .5rem .9rem;
          margin: .75rem 0; }
summary { cursor: pointer; font-weight: 600; }
code, pre { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: .9em; }
pre { background: #f6f8fa; padding: .75rem; border-radius: 6px; overflow-x: auto; }
"""


def render_markdown(md_text):
    import markdown
    return markdown.markdown(md_text, extensions=["tables", "fenced_code"])


def _fmt(x, digits=3):
    return f"{x:.{digits}f}" if isinstance(x, (int, float)) else "—"


def summary_tiles(stats):
    baseline = stats["meta"]["baseline"]
    tiles = []
    for c in stats.get("comparisons", []):
        agg = stats["variants"].get(c["variant"], {}).get(c["metric"], {})
        mean, ci = agg.get("mean"), agg.get("ci95")
        mean_s = _fmt(mean)
        if ci:
            mean_s += f" <span class='k'>[{_fmt(ci[0])}, {_fmt(ci[1])}]</span>"
        delta_s = f"{c['delta']:+.3f} / {c['delta_rel'] * 100:+.1f}% vs {c['baseline']}" \
            if c.get("delta_rel") is not None else f"{c['delta']:+.3f} vs {c['baseline']}"
        cls = "up" if c.get("delta", 0) > 0 else "down"
        flags = f"<div class='k'>{' · '.join(c['flags'])}</div>" if c.get("flags") else ""
        tiles.append(
            f"<div class='tile'><div class='k'>{c['variant']} · {c['metric']} · "
            f"n={c['n_variant']}</div><div class='v'>{mean_s}</div>"
            f"<div class='d {cls}'>{delta_s}</div>{flags}</div>")
    if not tiles:
        for variant, metrics in stats.get("variants", {}).items():
            for metric, agg in metrics.items():
                tiles.append(
                    f"<div class='tile'><div class='k'>{variant} · {metric} · "
                    f"n={agg['n']}</div><div class='v'>{_fmt(agg['mean'])}</div></div>")
    return f"<div class='tiles'>{''.join(tiles)}</div>"


def collapsify(body_html):
    """Wrap h2 sections whose name is in COLLAPSIBLE in <details>."""
    collapsible = {"Appendix"}
    parts = re.split(r"(<h2>.*?</h2>)", body_html)
    out, in_details = [], False
    for part in parts:
        m = re.match(r"<h2>(.*?)</h2>$", part)
        if m:
            name = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            if in_details:
                out.append("</details>")
                in_details = False
            if name in collapsible:
                out.append(f"<details><summary>{name}</summary>")
                in_details = True
            else:
                out.append(part)
        else:
            out.append(part)
    if in_details:
        out.append("</details>")
    return "".join(out)
