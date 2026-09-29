# tests/test_render_core.py
import json

import render_html

STATS = {
    "meta": {"baseline": "baseline"},
    "variants": {
        "baseline": {"accuracy": {"n": 5, "mean": 0.705, "ci95": [0.699, 0.711]}},
        "method_a": {"accuracy": {"n": 5, "mean": 0.736, "ci95": [0.729, 0.743]}},
    },
    "comparisons": [{
        "variant": "method_a", "baseline": "baseline", "metric": "accuracy",
        "delta": 0.031, "delta_rel": 0.044, "test": "paired t-test (seed-matched, n=5)",
        "p": 1e-5, "cohens_d": 8.77, "flags": [], "n_variant": 5, "n_baseline": 5,
    }],
}


def test_render_markdown_tables():
    body = render_html.render_markdown("| a | b |\n|---|---|\n| 1 | 2 |")
    assert "<table" in body and "<td>1</td>" in body


def test_summary_tiles_content():
    tiles = render_html.summary_tiles(STATS)
    assert "method_a" in tiles
    assert "accuracy" in tiles
    assert "0.736" in tiles          # variant mean
    assert "+0.031" in tiles          # delta absolute
    assert "+4.4%" in tiles           # delta relative (percent, 1 decimal)
    assert "n=5" in tiles
    assert "baseline" in tiles


def test_collapsify_wraps_appendix_only():
    body = "<h2>3. Results</h2><p>x</p><h2>Appendix</h2><p>per-run</p>"
    out = render_html.collapsify(body)
    assert out.count("<details") == 1
    assert "<summary>Appendix</summary>" in out
    # no collapsible wrapper inside the Results section (between its heading and the details opener)
    assert "<h2>3. Results</h2>" in out and "<details" not in out.split("<h2>3. Results</h2>")[1].split("<details")[0]


def test_summary_tiles_escape_variant_and_flags():
    tiles = render_html.summary_tiles({
        "meta": {"baseline": "b"},
        "variants": {},
        "comparisons": [{
            "variant": "acc<x", "baseline": "b", "metric": "accuracy",
            "delta": 0.01, "delta_rel": None, "test": "Welch's t-test",
            "p": None, "cohens_d": None,
            "flags": ["no statistical inference possible (n<3)"],
            "n_variant": 1, "n_baseline": 5,
        }],
    })
    assert "acc&lt;x" in tiles       # variant name is html-escaped
    assert "acc<x" not in tiles      # ...never raw
    assert "n&lt;3" in tiles         # flag text is escaped too (analyze.py's literal strings contain <)
