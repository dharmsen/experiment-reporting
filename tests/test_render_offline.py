# tests/test_render_offline.py
import json
import re
from pathlib import Path

import render_html

REPO = Path(__file__).parents[1]

CHARTS = [{
    "div_id": "chart-1",
    "section": "Appendix",
    "figure": {"data": [{"type": "bar", "x": ["a", "b"], "y": [1, 2]}],
               "layout": {"title": "demo"}},
}]


def _page():
    body = render_html.render_markdown("# T\n\n**TL;DR:** x\n\n## Appendix\ny")
    tiles = render_html.summary_tiles({
        "meta": {"baseline": "b"},
        "variants": {"b": {"m": {"n": 3, "mean": 1.0}}},
        "comparisons": [],
    })
    js = REPO / "assets" / "plotly.min.js"
    return render_html.build_page(body, tiles, CHARTS, js.read_text(), "3.0.1")


def test_page_is_complete_html_with_charts():
    page = _page()
    assert page.startswith("<!DOCTYPE html>")
    assert "<html" in page and "</html>" in page
    assert 'id="chart-1"' in page
    assert "Plotly.newPlot" in page
    assert json.dumps(CHARTS[0]["figure"])[:60] in page.replace('\\"', '"')  # figure JSON embedded


def test_chart_spliced_into_named_section():
    page = _page()
    markup = re.sub(r"<script\b.*?</script>", "", page, flags=re.S)
    m = re.search(r"<h2>Appendix</h2>", markup)
    assert m, "Appendix heading missing"
    idx = markup.find('id="chart-1"')
    assert m.end() < idx < markup.find("</body>")  # inside the section, in the content region
    # spliced immediately after the section's h2 (top of section), not appended at the tail
    assert markup[m.end():].startswith('<div id="chart-1" class="chart"></div>')


def test_page_fully_offline():
    page = _page()
    # strip script bodies: the inlined plotly.js contains URL *string literals*
    # (map attribution, credit links) that are never fetched — only markup counts
    markup = re.sub(r"<script\b.*?</script>", "", page, flags=re.S)
    ext = re.findall(r'(?:src|href)="(https?://[^"]+)"', markup)
    assert ext == [], f"external references found: {ext}"


def test_plotly_embedded_inline():
    page = _page()
    assert "plotly.js 3.0.1" in page          # version comment marker
    assert len(page) > 1_000_000               # the library is actually inlined


def test_cli(tmp_path):
    md = tmp_path / "report.md"
    md.write_text("# T\n\n## Appendix\nper-run data\n")
    stats = tmp_path / "stats.json"
    stats.write_text(json.dumps({
        "meta": {"baseline": "b"},
        "variants": {"b": {"m": {"n": 3, "mean": 1.0, "ci95": [0.9, 1.1]}}},
        "comparisons": [],
    }))
    charts = tmp_path / "charts.json"
    charts.write_text(json.dumps(CHARTS))
    out = tmp_path / "report.html"
    rc = render_html.main(["--content", str(md), "--stats", str(stats),
                           "--charts", str(charts), "--out", str(out)])
    assert rc == 0
    page = out.read_text()
    assert "<!DOCTYPE html>" in page and "Plotly.newPlot" in page
