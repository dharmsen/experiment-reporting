# tests/test_loading.py
from pathlib import Path

import analyze

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_wide_csv():
    runs = analyze.load_input(FIXTURES / "sweep.csv")
    assert len(runs) == 13
    assert {r["variant"] for r in runs} == {"baseline", "method_a", "method_b"}
    by_id = {r["run_id"]: r for r in runs}
    assert by_id["1"]["seed"] == 1.0
    assert by_id["1"]["metrics"] == {"accuracy": 0.712, "loss": 0.541}
    assert by_id["13"]["metrics"]["accuracy"] == 0.715


def test_load_long_csv():
    runs = analyze.load_input(FIXTURES / "sweep_long.csv")
    assert len(runs) == 13
    by_id = {r["run_id"]: r for r in runs}
    assert by_id["10"]["metrics"] == {"accuracy": 0.745}


def test_load_long_csv_drops_non_numeric_values(tmp_path):
    p = tmp_path / "long_bad.csv"
    p.write_text("run_id,variant,seed,metric,value\n"
                 "1,v,1,accuracy,0.5\n"
                 "2,v,2,accuracy,n/a\n"
                 "3,v,3,loss,0.25\n")
    runs = analyze.load_input(p)
    by_id = {r["run_id"]: r for r in runs}
    assert by_id["1"]["metrics"] == {"accuracy": 0.5}
    assert by_id["2"]["metrics"] == {}          # bad cell dropped, no None stored
    # the pipeline downstream just omits it — no crash, no NaN
    out = analyze.build_output([p], baseline="v", metrics=["accuracy"], resamples=50)
    assert out["variants"]["v"]["accuracy"]["values"] == [0.5]


def test_load_json(tmp_path):
    p = tmp_path / "runs.json"
    p.write_text('[{"run_id": "1", "variant": "v", "seed": 1, "accuracy": 0.5}]')
    runs = analyze.load_input(p)
    assert runs == [{"run_id": "1", "variant": "v", "seed": 1, "metrics": {"accuracy": 0.5}}]
