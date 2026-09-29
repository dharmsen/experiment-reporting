# tests/test_e2e.py
import json
import re
from pathlib import Path

REPO = Path(__file__).parents[1]
EXAMPLES = REPO / "examples"


def test_stats_json_numerically_correct():
    stats = json.loads((EXAMPLES / "sweep-stats.json").read_text())
    acc = stats["variants"]["baseline"]["accuracy"]
    assert acc["n"] == 5
    assert abs(acc["mean"] - 0.705) < 1e-12
    assert abs(acc["std"] - 0.0057009) < 1e-6
    comp = next(c for c in stats["comparisons"]
                if c["variant"] == "method_a" and c["metric"] == "accuracy")
    assert comp["delta"] > 0.03 and comp["p"] < 1e-4
    comp_b = next(c for c in stats["comparisons"]
                  if c["variant"] == "method_b" and c["metric"] == "accuracy")
    assert "low-power: n<5, interpret cautiously" in comp_b["flags"]


def test_report_md_structure_and_checklist():
    md = (EXAMPLES / "sweep-report.md").read_text()
    for section in ["TL;DR:", "## 1. Question", "## 2. Setup", "## 3. Results",
                    "## 4. Statistical assessment", "## 5. Interpretation",
                    "## 6. Decision", "## Appendix"]:
        assert section in md, f"missing {section}"
    assert "baseline" in md and re.search(r"n\s*=\s*\d", md)
    assert "0.705" in md  # cites stats.json numbers


def test_html_offline_and_complete():
    page = (EXAMPLES / "sweep-report.html").read_text()
    markup = re.sub(r"<script\b.*?</script>", "", page, flags=re.S)
    assert page.startswith("<!DOCTYPE html>")
    assert "Plotly.newPlot" in page
    assert not re.findall(r'(?:src|href)="(https?://[^"]+)"', markup)
    assert len(page) > 1_000_000
