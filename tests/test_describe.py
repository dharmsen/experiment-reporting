# tests/test_describe.py
from pathlib import Path

import pytest

import analyze

FIXTURES = Path(__file__).parent / "fixtures"


def _accuracy(variant):
    runs = analyze.load_input(FIXTURES / "sweep.csv")
    return sorted(r["metrics"]["accuracy"] for r in runs if r["variant"] == variant)


def test_describe_baseline_accuracy():
    d = analyze.describe(_accuracy("baseline"), resamples=1000, seed=3407)
    assert d["n"] == 5
    assert d["mean"] == pytest.approx(0.705, abs=1e-12)
    assert d["std"] == pytest.approx(0.0057009, abs=1e-6)
    assert d["sem"] == pytest.approx(0.0025501, abs=1e-6)
    assert d["median"] == pytest.approx(0.705)
    assert d["iqm"] == pytest.approx(0.705)  # trim_mean(0.25) of middle 3
    assert d["min"] == 0.698 and d["max"] == 0.712
    lo, hi = d["ci95"]
    assert lo < d["mean"] < hi
    assert 0.698 <= lo and hi <= 0.712


def test_describe_small_n_and_even_iqm():
    d = analyze.describe(_accuracy("method_b"), resamples=1000, seed=3407)
    assert d["n"] == 3
    assert d["iqm"] is None  # trim_mean needs n >= 4
    even = analyze.describe([0.715, 0.718, 0.722, 0.725], resamples=100, seed=3407)
    assert even["iqm"] == pytest.approx(0.72)  # (0.718 + 0.722) / 2


def test_describe_deterministic():
    a = analyze.describe(_accuracy("baseline"), resamples=500, seed=3407)
    b = analyze.describe(_accuracy("baseline"), resamples=500, seed=3407)
    assert a["ci95"] == b["ci95"]
