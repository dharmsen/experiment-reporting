# tests/test_compare.py
from pathlib import Path

import pytest

import analyze

FIXTURES = Path(__file__).parent / "fixtures"


def _runs():
    return analyze.load_input(FIXTURES / "sweep.csv")


def test_compare_method_a_significant():
    c = analyze.compare(_runs(), "method_a", "baseline", "accuracy")
    assert c["n_variant"] == 5 and c["n_baseline"] == 5
    assert c["delta"] == pytest.approx(0.031, abs=1e-12)
    assert c["delta_rel"] == pytest.approx(0.031 / 0.705, abs=1e-6)
    assert c["test"] == "paired t-test (seed-matched, n=5)"
    assert c["p"] < 1e-4
    assert c["cohens_d"] == pytest.approx(8.768, abs=1e-2)
    assert c["flags"] == []


def test_compare_method_b_low_power_not_significant():
    c = analyze.compare(_runs(), "method_b", "baseline", "accuracy")
    assert c["n_variant"] == 3
    assert c["test"] == "paired t-test (seed-matched, n=3)"
    assert c["p"] == pytest.approx(0.1072, abs=5e-3)
    assert c["delta"] == pytest.approx(0.0133333, abs=1e-6)
    assert "low-power: n<5, interpret cautiously" in c["flags"]


def test_compare_forced_welch():
    c = analyze.compare(_runs(), "method_a", "baseline", "accuracy", paired_mode="never")
    assert c["test"] == "Welch's t-test"
    assert c["p"] == pytest.approx(1.73e-4, abs=2e-5)


def test_compare_no_inference_when_n_lt_3(tmp_path):
    p = tmp_path / "tiny.csv"
    p.write_text("run_id,variant,seed,accuracy\n1,v1,1,0.5\n2,v1,2,0.6\n"
                 "3,baseline,1,0.5\n4,baseline,2,0.6\n")
    c = analyze.compare(analyze.load_input(p), "v1", "baseline", "accuracy")
    assert "no statistical inference possible (n<3)" in c["flags"]  # n=2 runs each
    assert c["test"] == "Welch's t-test"  # only 2 shared seeds → no pairing


def test_holm_adjust():
    adj = analyze.holm_adjust([0.04, 0.01, 0.03])
    assert adj == pytest.approx([0.06, 0.03, 0.06])


def test_build_output_schema():
    out = analyze.build_output([FIXTURES / "sweep.csv"], baseline="baseline",
                               metrics=["accuracy"], paired_mode="auto",
                               resamples=500, seed=3407, use_holm=False)
    assert set(out) == {"meta", "variants", "comparisons"}
    assert out["meta"]["baseline"] == "baseline"
    assert out["meta"]["bootstrap"] == {"resamples": 500, "seed": 3407}
    assert set(out["variants"]) == {"baseline", "method_a", "method_b"}
    assert len(out["comparisons"]) == 2
    comp = {c["variant"]: c for c in out["comparisons"]}
    assert comp["method_a"]["metric"] == "accuracy"


def test_cli_writes_json(tmp_path, capsys):
    out_path = tmp_path / "stats.json"
    rc = analyze.main(["--baseline", "baseline", "--metrics", "accuracy",
                       "--resamples", "500", "--out", str(out_path),
                       str(FIXTURES / "sweep.csv")])
    assert rc == 0
    data = __import__("json").loads(out_path.read_text())
    assert data["variants"]["method_a"]["accuracy"]["n"] == 5
