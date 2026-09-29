# Experiment Reporting Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `experiment-reporting` Claude Code skill that turns ML experiment results (in-context / markdown / CSV / JSON) into rigorous lab-notebook reports — markdown by default, self-contained interactive HTML on demand.

**Architecture:** Lean `SKILL.md` workflow + progressive-disclosure `references/` + deterministic Python scripts (`analyze.py` for stats via `uv run --with`, `render_html.py` for offline single-file HTML with embedded plotly.js) + markdown template + vendored plotly asset. Statistics are computed by script, never by the agent's mental arithmetic.

**Tech Stack:** Python ≥3.10 via `uv run --with numpy,scipy` (analysis) and `uv run --with markdown,pygments` (rendering); pytest for tests; plotly.js 3.0.1 vendored from cdn.plot.ly.

**Spec:** `docs/superpowers/specs/2026-09-29-experiment-reporting-skill-design.md` — the plan argues from the spec; executors read both.

## Global Constraints

- Repository root: `/home/dalton/skills/experiment-reporting` (not yet a git repo — Task 1 initializes it).
- ALL Python/pytest invocations go through `uv run --with <deps>` (user's global rule: ALWAYS use uv). No venvs, no lockfiles, no `pip`.
- Analysis deps: `numpy,scipy`. Rendering deps: `markdown,pygments`. Test deps: `pytest`.
- Skill name (frontmatter `name:`): `experiment-reporting`. Install via symlink `~/.claude/skills/experiment-reporting` → repo root.
- HTML output must be fully offline: zero `http(s)` references, plotly.js embedded inline.
- Bootstrap default seed `3407`, default resamples `10000`, CI `95%` percentile method.
- Flags: `n < 5` → `"low-power: n<5, interpret cautiously"`; `n < 3` → `"no statistical inference possible (n<3)"`.
- IQM = `scipy.stats.trim_mean(values, 0.25)`; return `null` when `n < 4`.
- Commit messages carry NO co-author/attribution trailers of any kind (user request, 2026-09-29).
- Scripts produce numbers/HTML only — never report prose. Prose is drafted by the agent following `references/writing-style.md`.

---

### Task 1: Repository scaffolding + shared fixtures + vendored plotly

**Files:**
- Create: `.gitignore`, `conftest.py`, `tests/fixtures/sweep.csv`, `tests/fixtures/sweep_long.csv`, `assets/plotly.min.js`, `assets/PLOTLY_VERSION`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: `tests/fixtures/sweep.csv` — 3 variants (5/5/3 seeds; method_b has only 3 runs: seeds 1,2,4 — missing seeds 3 and 5), wide format `run_id,variant,seed,accuracy,loss`. Used by Tasks 2–4 tests and Task 9 end-to-end. `assets/plotly.min.js` consumed by Task 7. `conftest.py` puts `scripts/` on `sys.path` so tests can `import analyze`.

- [ ] **Step 1: Initialize git and directory structure**

```bash
cd /home/dalton/skills/experiment-reporting
git init
mkdir -p scripts references templates assets tests/fixtures
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
.pytest_cache/
*.pyc
.superpowers/
```

- [ ] **Step 3: Create `conftest.py`** (repo root — makes `scripts/` importable in tests)

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
```

- [ ] **Step 4: Create `tests/fixtures/sweep.csv`** (exact content — hand-verified numbers below depend on it)

```csv
run_id,variant,seed,accuracy,loss
1,baseline,1,0.712,0.541
2,baseline,2,0.698,0.562
3,baseline,3,0.705,0.553
4,baseline,4,0.701,0.558
5,baseline,5,0.709,0.549
6,method_a,1,0.741,0.492
7,method_a,2,0.725,0.511
8,method_a,3,0.738,0.499
9,method_a,4,0.731,0.506
10,method_a,5,0.745,0.495
11,method_b,1,0.718,0.530
12,method_b,2,0.722,0.527
13,method_b,4,0.715,0.533
```

- [ ] **Step 5: Create `tests/fixtures/sweep_long.csv`** (long format of the same data, accuracy only)

```csv
run_id,variant,seed,metric,value
1,baseline,1,accuracy,0.712
2,baseline,2,accuracy,0.698
3,baseline,3,accuracy,0.705
4,baseline,4,accuracy,0.701
5,baseline,5,accuracy,0.709
6,method_a,1,accuracy,0.741
7,method_a,2,accuracy,0.725
8,method_a,3,accuracy,0.738
9,method_a,4,accuracy,0.731
10,method_a,5,accuracy,0.745
11,method_b,1,accuracy,0.718
12,method_b,2,accuracy,0.722
13,method_b,4,accuracy,0.715
```

- [ ] **Step 6: Vendor plotly.js (pinned)**

```bash
curl -fsSL -o assets/plotly.min.js https://cdn.plot.ly/plotly-3.0.1.min.js
printf '3.0.1\n' > assets/PLOTLY_VERSION
```

- [ ] **Step 7: Verify assets and fixtures**

Run: `wc -c assets/plotly.min.js && wc -l tests/fixtures/sweep.csv tests/fixtures/sweep_long.csv`
Expected: plotly.min.js is > 1,000,000 bytes; sweep.csv is 14 lines; sweep_long.csv is 14 lines.

- [ ] **Step 8: Commit**

```bash
git add .gitignore conftest.py tests/fixtures assets docs
git commit -m "chore: scaffold experiment-reporting skill repo, fixtures, vendored plotly"
```

---

### Task 2: `analyze.py` — input loading (wide CSV, long CSV, JSON)

**Files:**
- Create: `scripts/analyze.py`
- Test: `tests/test_loading.py`

**Interfaces:**
- Consumes: fixtures from Task 1.
- Produces: `load_input(path) -> list[Run]` where `Run = {"run_id": str|None, "variant": str, "seed": float|None, "metrics": dict[str, float]}`. Used by Tasks 3–4.

- [ ] **Step 1: Write the failing tests**

```python
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


def test_load_json(tmp_path):
    p = tmp_path / "runs.json"
    p.write_text('[{"run_id": "1", "variant": "v", "seed": 1, "accuracy": 0.5}]')
    runs = analyze.load_input(p)
    assert runs == [{"run_id": "1", "variant": "v", "seed": 1, "metrics": {"accuracy": 0.5}}]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest,numpy,scipy pytest tests/test_loading.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'analyze'`

- [ ] **Step 3: Write the loading implementation** (`scripts/analyze.py`)

```python
#!/usr/bin/env python3
"""Compute statistics for experiment reports. Numbers only — no prose.

Usage:
  uv run --with numpy,scipy scripts/analyze.py INPUT [INPUT...] [--baseline NAME]
      [--metrics m1,m2] [--paired auto|never] [--bootstrap-seed N]
      [--resamples N] [--holm] [--out stats.json]
"""
import csv
import json
import sys
from pathlib import Path

ID_COLS = {"run_id", "variant", "seed"}


def _to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load_wide_csv(path):
    runs = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            metrics = {}
            for k, v in row.items():
                if k is None or k in ID_COLS:
                    continue
                fv = _to_float(v)
                if fv is not None:
                    metrics[k] = fv
            runs.append({
                "run_id": row.get("run_id"),
                "variant": row["variant"],
                "seed": _to_float(row.get("seed")),
                "metrics": metrics,
            })
    return runs


def load_long_csv(path):
    runs = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            key = (row.get("variant"), _to_float(row.get("seed")), row.get("run_id"))
            run = runs.setdefault(key, {
                "run_id": row.get("run_id"),
                "variant": row["variant"],
                "seed": _to_float(row.get("seed")),
                "metrics": {},
            })
            run["metrics"][row["metric"]] = _to_float(row["value"])
    return list(runs.values())


def load_json(path):
    data = json.loads(Path(path).read_text())
    runs = []
    for obj in data:
        metrics = {k: float(v) for k, v in obj.items()
                   if k not in ID_COLS and isinstance(v, (int, float))}
        runs.append({
            "run_id": obj.get("run_id"),
            "variant": obj["variant"],
            "seed": obj.get("seed"),
            "metrics": metrics,
        })
    return runs


def load_input(path):
    p = str(path).lower()
    if p.endswith(".json"):
        return load_json(path)
    with open(path, newline="") as f:
        header = csv.DictReader(f).fieldnames or []
    if "metric" in header and "value" in header:
        return load_long_csv(path)
    return load_wide_csv(path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest,numpy,scipy pytest tests/test_loading.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/analyze.py tests/test_loading.py
git commit -m "feat(analyze): load wide/long CSV and JSON run tables"
```

---

### Task 3: `analyze.py` — descriptive statistics + bootstrap CI

**Files:**
- Modify: `scripts/analyze.py` (append)
- Test: `tests/test_describe.py`

**Interfaces:**
- Consumes: `load_input` from Task 2.
- Produces: `describe(values: list[float], resamples: int = 10000, seed: int = 3407) -> dict` with keys `n, values, mean, std, sem, median, iqm, min, max, ci95` — exactly the variant×metric object of the spec §8 output schema. Constants `DEFAULT_SEED = 3407`, `DEFAULT_RESAMPLES = 10000`.

- [ ] **Step 1: Write the failing tests** (hand-verified expectations: baseline accuracy mean = 0.705, sample std ≈ 0.0057009, sem ≈ 0.0025501; method_b accuracy n=4 → IQM = mean of middle two = 0.72)

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest,numpy,scipy pytest tests/test_describe.py -v`
Expected: FAIL — `AttributeError: module 'analyze' has no attribute 'describe'`

- [ ] **Step 3: Append implementation to `scripts/analyze.py`** (also add imports `numpy as np` and `from scipy import stats as sps` at the top)

```python
DEFAULT_SEED = 3407          # Picard (2021), arXiv:2109.08203
DEFAULT_RESAMPLES = 10_000


def describe(values, resamples=DEFAULT_RESAMPLES, seed=DEFAULT_SEED):
    """Descriptive stats + 95% percentile bootstrap CI over runs."""
    import numpy as np
    from scipy import stats as sps

    a = np.asarray(values, dtype=float)
    n = int(a.size)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(resamples, n))
    boot_means = a[idx].mean(axis=1)
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    out = {
        "n": n,
        "values": [float(v) for v in values],
        "mean": float(a.mean()),
        "median": float(np.median(a)),
        "min": float(a.min()),
        "max": float(a.max()),
        "ci95": [float(lo), float(hi)],
        "std": None, "sem": None, "iqm": None,
    }
    if n > 1:
        out["std"] = float(a.std(ddof=1))
        out["sem"] = float(a.std(ddof=1) / np.sqrt(n))
    if n >= 4:
        out["iqm"] = float(sps.trim_mean(a, 0.25))
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest,numpy,scipy pytest tests/test_describe.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/analyze.py tests/test_describe.py
git commit -m "feat(analyze): descriptive stats with deterministic bootstrap CI"
```

---

### Task 4: `analyze.py` — comparisons, flags, Holm, CLI + JSON output

**Files:**
- Modify: `scripts/analyze.py` (append)
- Test: `tests/test_compare.py`

**Interfaces:**
- Consumes: `load_input`, `describe` from Tasks 2–3.
- Produces: `compare(runs, variant, baseline, metric, paired_mode="auto") -> dict` (the comparison object of spec §8: `variant, baseline, metric, delta, delta_rel, test, p, cohens_d, flags, n_variant, n_baseline`); `holm_adjust(pvals) -> list[float]`; `build_output(paths, baseline, metrics, paired_mode, resamples, seed, use_holm) -> dict` (full spec §8 schema); `main(argv)`. Exit code 0; JSON to stdout or `--out`.
- Hand-verified expectations: method_a vs baseline accuracy — paired (5 shared seeds), mean diff = 0.031, paired sd ≈ 0.0035355, t ≈ 19.604, p < 1e-4, Cohen's d ≈ 8.768. method_b vs baseline — 3 shared seeds ≥ 3 → paired on matched pairs (n=3): mean diff of matched pairs ≈ 0.0146667 while `delta` over all runs = 0.0133333 (baseline keeps its 5 runs), t ≈ 2.816, df=2, p ≈ 0.107 (NOT significant), flag `low-power`.

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest,numpy,scipy pytest tests/test_compare.py -v`
Expected: FAIL — `AttributeError: module 'analyze' has no attribute 'compare'`

- [ ] **Step 3: Append implementation to `scripts/analyze.py`**

```python
LOW_POWER_N = 5
NO_INFERENCE_N = 3
PAIRED_MIN_SHARED = 3


def _values(runs, variant, metric):
    return [r["metrics"][metric] for r in runs
            if r["variant"] == variant and metric in r["metrics"]]


def _seed_aligned(runs, variant, baseline, metric):
    """Return (variant_vals, baseline_vals) paired by equal seed, or None."""
    def by_seed(v):
        return {r["seed"]: r["metrics"][metric] for r in runs
                if r["variant"] == v and metric in r["metrics"]
                and r["seed"] is not None}
    a, b = by_seed(variant), by_seed(baseline)
    shared = sorted(set(a) & set(b))
    if len(shared) < PAIRED_MIN_SHARED:
        return None
    return [a[s] for s in shared], [b[s] for s in shared]


def compare(runs, variant, baseline, metric, paired_mode="auto"):
    import numpy as np
    from scipy import stats as sps

    v_vals, b_vals = _values(runs, variant, metric), _values(runs, baseline, metric)
    delta = float(np.mean(v_vals) - np.mean(b_vals))
    delta_rel = float(delta / np.mean(b_vals)) if np.mean(b_vals) != 0 else None
    flags = []
    if len(v_vals) < NO_INFERENCE_N or len(b_vals) < NO_INFERENCE_N:
        flags.append("no statistical inference possible (n<3)")
    if len(v_vals) < LOW_POWER_N or len(b_vals) < LOW_POWER_N:
        flags.append("low-power: n<5, interpret cautiously")

    paired = None
    if paired_mode == "auto":
        paired = _seed_aligned(runs, variant, baseline, metric)
    if paired_mode == "never":
        paired = None

    if paired is not None and len(v_vals) >= NO_INFERENCE_N:
        a, b = paired
        res = sps.ttest_rel(a, b)
        d = np.asarray(a) - np.asarray(b)
        cohens_d = float(d.mean() / d.std(ddof=1)) if d.std(ddof=1) > 0 else None
        test = f"paired t-test (seed-matched, n={len(a)})"
    else:
        res = sps.ttest_ind(v_vals, b_vals, equal_var=False)
        sv, sb = np.var(v_vals, ddof=1), np.var(b_vals, ddof=1)
        nv, nb = len(v_vals), len(b_vals)
        pooled = np.sqrt(((nv - 1) * sv + (nb - 1) * sb) / (nv + nb - 2))
        cohens_d = float(delta / pooled) if pooled > 0 else None
        test = "Welch's t-test"

    return {
        "variant": variant, "baseline": baseline, "metric": metric,
        "delta": delta, "delta_rel": delta_rel,
        "test": test, "p": float(res.pvalue), "cohens_d": cohens_d,
        "flags": flags, "n_variant": len(v_vals), "n_baseline": len(b_vals),
    }


def holm_adjust(pvals):
    """Holm-Bonferroni: returns adjusted p-values in the original order."""
    import numpy as np
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


def _all_metrics(runs):
    names = []
    for r in runs:
        for k in r["metrics"]:
            if k not in names:
                names.append(k)
    return names


def build_output(paths, baseline, metrics=None, paired_mode="auto",
                 resamples=DEFAULT_RESAMPLES, seed=DEFAULT_SEED, use_holm=False):
    from datetime import datetime, timezone

    runs = []
    for p in paths:
        runs.extend(load_input(p))
    metrics = metrics or _all_metrics(runs)
    variants = sorted({r["variant"] for r in runs})

    out = {
        "meta": {
            "inputs": [str(p) for p in paths],
            "baseline": baseline,
            "bootstrap": {"resamples": resamples, "seed": seed},
            "holm": use_holm,
            "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "variants": {},
        "comparisons": [],
    }
    for v in variants:
        out["variants"][v] = {}
        for m in metrics:
            vals = _values(runs, v, m)
            if vals:
                out["variants"][v][m] = describe(vals, resamples=resamples, seed=seed)

    for v in variants:
        if v == baseline:
            continue
        for m in metrics:
            if _values(runs, v, m) and _values(runs, baseline, m):
                out["comparisons"].append(
                    compare(runs, v, baseline, m, paired_mode=paired_mode))

    if use_holm and out["comparisons"]:
        adjusted = holm_adjust([c["p"] for c in out["comparisons"]])
        for c, p in zip(out["comparisons"], adjusted):
            c["p_holm"] = p
    return out


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("inputs", nargs="+", help="CSV/JSON run tables")
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--metrics", default=None, help="comma-separated; default: all")
    ap.add_argument("--paired", choices=["auto", "never"], default="auto")
    ap.add_argument("--bootstrap-seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--resamples", type=int, default=DEFAULT_RESAMPLES)
    ap.add_argument("--holm", action="store_true")
    ap.add_argument("--out", default=None, help="write JSON here instead of stdout")
    args = ap.parse_args(argv)

    out = build_output([Path(p) for p in args.inputs], baseline=args.baseline,
                       metrics=args.metrics.split(",") if args.metrics else None,
                       paired_mode=args.paired, resamples=args.resamples,
                       seed=args.bootstrap_seed, use_holm=args.holm)
    text = json.dumps(out, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest,numpy,scipy pytest tests/ -v`
Expected: all tests PASS (loading, describe, compare).

- [ ] **Step 5: Manual smoke check of the CLI**

Run: `uv run --with numpy,scipy scripts/analyze.py tests/fixtures/sweep.csv --baseline baseline --resamples 1000 | head -40`
Expected: JSON with `meta`, `variants` (3 variants), `comparisons` (2); method_b comparison carries the low-power flag.

- [ ] **Step 6: Commit**

```bash
git add scripts/analyze.py tests/test_compare.py
git commit -m "feat(analyze): comparisons, flags, Holm, CLI JSON output"
```

---

### Task 5: Reference docs + markdown template (content authoring)

**Files:**
- Create: `references/reporting-standards.md`, `references/statistics.md`, `references/writing-style.md`, `references/html-report.md`, `templates/report-template.md`

**Interfaces:**
- Consumes: spec §3 (citations), §6 (structure), §7 (writing rules), §8 (stats rules), §9 (HTML contract).
- Produces: the reference set `SKILL.md` (Task 8) points to; the template the agent fills in step 3 of the workflow.

- [ ] **Step 1: Write `references/reporting-standards.md`** — the spec §3 evidence base: all sources with URLs, grouped (standards/checklists, statistical rigor, structure/writing, tooling), each with 2–4 bullets of its reporting-relevant requirements, ending with the one-line distillation from spec §3. Copy the source list verbatim from the spec.

- [ ] **Step 2: Write `references/statistics.md`** — the decision recipes the script encodes:
  - Never compare single runs (Henderson, Bouthillier, Reimers & Gurevych).
  - n ≥ 10 preferred; 3 ≤ n < 5 → flag "no inference" / "low-power" exactly as analyze.py emits them; when n < 3 report descriptive values only.
  - Aggregates: prefer median/IQM for small n; mean ± 95% percentile bootstrap CI (10k resamples, seed 3407) as default uncertainty; always say what the interval varies over (runs/seeds).
  - Comparisons: paired-by-seed t-test when ≥ 3 shared seeds, else Welch's; report test name, p, Cohen's d; with >1 comparison consider `--holm`; "significant" only with test + α stated (α = 0.05 default).
  - Already-aggregated inputs: use given numbers, state what uncertainty is missing.
  - Bimodality check: eyeball per-run values; if spread is not unimodal, report the distribution, not the mean (Reimers & Gurevych).

- [ ] **Step 3: Write `references/writing-style.md`** — spec §7's 15 rules verbatim, each tagged with its source (Pinker; Schimel; Gopen & Swan; Heath & Heath; Picard; Zinsser; Strunk & White; Sand-Jensen).

- [ ] **Step 4: Write `references/html-report.md`** — the HTML contract: single file; plotly.min.js embedded from `assets/`; data inline JSON; summary tiles row (metric, value, Δ vs baseline, n, flags) generated from stats.json; `<details>` progressive disclosure for Appendix; zero external requests (must open from `file://`); chart specs authored under the dataviz skill's system at draft time, renderer only embeds.

- [ ] **Step 5: Write `templates/report-template.md`** with HTML-comment guidance per section:

```markdown
# {{Experiment title}} — {{one-line verdict}}

<!-- TL;DR: outcome + magnitude + uncertainty + decision. 2-3 sentences. Example:
"method_a beats baseline by +3.1 pts accuracy (95% CI [2.4, 3.8], paired t-test n=5,
p<1e-4). Ship it to the main sweep; method_b's +1.5 pts is not significant (p=0.11,
low-power n=4)." -->

**TL;DR:** …

## 1. Question & hypothesis
<!-- Why this experiment exists; what result would change what we do. -->

## 2. Setup
<!-- Config table (variant → what differs), environment/versions, data, compute, code pointer. Complete enough to rerun. -->

## 3. Results
<!-- Summary table: variant | metric | n | aggregate ± uncertainty. Per-run table (or pointer to Appendix). Charts only if they beat the table. -->

## 4. Statistical assessment
<!-- Tests, effect sizes, small-n flags, caveats — mirror stats.json, cite its numbers. -->

## 5. Interpretation
<!-- Labeled as interpretation: what we think happened. Separate from measured results above. -->

## 6. Decision & next steps
<!-- What this changes; what runs next. -->

## Appendix
<!-- Full per-run data, links, excluded runs with count + reason. -->
```

- [ ] **Step 6: Verify content completeness**

Run: `grep -c "arxiv\|jmlr\|aclanthology\|neurips.cc\|plos" references/reporting-standards.md && grep -c "^#" templates/report-template.md`
Expected: reporting-standards.md contains ≥ 8 source URLs; template contains ≥ 7 headings (title + 6 numbered + Appendix = 8 `#`-lines).

- [ ] **Step 7: Commit**

```bash
git add references templates
git commit -m "docs: reference standards, statistics recipes, writing style, report template"
```

---

### Task 6: `render_html.py` — markdown → HTML core with summary tiles

**Files:**
- Create: `scripts/render_html.py`
- Test: `tests/test_render_core.py`

**Interfaces:**
- Consumes: stats.json shaped per spec §8 (Task 4 output).
- Produces: `render_markdown(md_text) -> str` (HTML body); `summary_tiles(stats) -> str` (tiles row HTML); `collapsify(body_html) -> str` (wraps `<h2>Appendix</h2>` section in `<details>`); `PAGE_CSS -> str` (shared styling constant, used again by Task 7).

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest,markdown,pygments pytest tests/test_render_core.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'render_html'`

- [ ] **Step 3: Write `scripts/render_html.py`**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest,markdown,pygments pytest tests/test_render_core.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/render_html.py tests/test_render_core.py
git commit -m "feat(render): markdown body, summary tiles, collapsible appendix"
```

---

### Task 7: `render_html.py` — chart embedding + offline single-file assembly + CLI

**Files:**
- Modify: `scripts/render_html.py` (append)
- Test: `tests/test_render_offline.py`

**Interfaces:**
- Consumes: `render_markdown`, `summary_tiles`, `collapsify`, `PAGE_CSS` from Task 6; `assets/plotly.min.js` from Task 1.
- Produces: `build_page(content_html, tiles_html, charts, plotly_js, plotly_version) -> str` (complete HTML document string); `main(argv)` with `--content/--stats/--charts/--out`. `charts.json` format: `[{"div_id": "chart-1", "figure": {"data": [...], "layout": {...}}}]`.
- Task 9 consumes the CLI end-to-end.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_render_offline.py
import json
import re
from pathlib import Path

import render_html

REPO = Path(__file__).parents[1]

CHARTS = [{
    "div_id": "chart-1",
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
    assert json.dumps(CHARTS[0]["figure"])[:60] in page.replace('\\"', '"') or \
           '"data"' in page  # figure JSON embedded


def test_page_fully_offline():
    page = _page()
    ext = re.findall(r'(?:src|href)="(https?://[^"]+)"', page)
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest,markdown,pygments pytest tests/test_render_offline.py -v`
Expected: FAIL — `AttributeError: module 'render_html' has no attribute 'build_page'`

- [ ] **Step 3: Append implementation to `scripts/render_html.py`**

```python
COLLAPSIBLE_NOTE = "<!-- sections whose h2 name is in collapsify()'s set render collapsed -->"


def build_page(content_html, tiles_html, charts, plotly_js, plotly_version):
    import html as html_mod

    charts_json = json.dumps([{"div_id": c["div_id"], "figure": c["figure"]}
                              for c in (charts or [])])
    charts_divs = "".join(f'<div id="{html_mod.escape(c["div_id"])}" class="chart"></div>'
                          for c in (charts or []))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Experiment report</title>
<style>{PAGE_CSS}
.chart {{ width: 100%; min-height: 22rem; margin: 1rem 0; }}
</style>
</head>
<body>
{content_html}
{tiles_html}
{charts_divs}
<script>/* plotly.js {plotly_version} */
{plotly_js}
</script>
<script>
const REPORT_CHARTS = {charts_json};
for (const c of REPORT_CHARTS) {{
  Plotly.newPlot(c.div_id, c.figure.data, c.figure.layout || {{}}, {{responsive: true}});
}}
</script>
</body>
</html>
"""


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--content", required=True, help="drafted report markdown")
    ap.add_argument("--stats", required=True, help="stats.json from analyze.py")
    ap.add_argument("--charts", default=None, help="charts.json (plotly figure specs)")
    ap.add_argument("--out", default=None, help="output .html path")
    args = ap.parse_args(argv)

    stats = json.loads(Path(args.stats).read_text())
    charts = json.loads(Path(args.charts).read_text()) if args.charts else []
    body = collapsify(render_markdown(Path(args.content).read_text()))
    tiles = summary_tiles(stats)
    repo = Path(__file__).resolve().parents[1]
    plotly_js = (repo / "assets" / "plotly.min.js").read_text()
    version = (repo / "assets" / "PLOTLY_VERSION").read_text().strip()
    page = build_page(body, tiles, charts, plotly_js, version)

    out = Path(args.out) if args.out else Path(args.content).with_suffix(".html")
    out.write_text(page)
    print(f"wrote {out} ({len(page) / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --with pytest,markdown,pygments pytest tests/test_render_offline.py -v`
Expected: 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/render_html.py tests/test_render_offline.py
git commit -m "feat(render): offline single-file HTML with inline plotly and charts"
```

---

### Task 8: `SKILL.md` + install symlink

**Files:**
- Create: `SKILL.md`
- Create (outside repo): `~/.claude/skills/experiment-reporting` symlink → repo root

**Interfaces:**
- Consumes: everything from Tasks 1–7.
- Produces: the installed, invocable skill.

Note for the executor: before writing SKILL.md, invoke the `superpowers:writing-skills` skill via the Skill tool and follow its authoring guidance (description/trigger wording, length discipline).

- [ ] **Step 1: Write `SKILL.md`**

```markdown
---
name: experiment-reporting
description: Use when reporting results of experiments the agent ran or was given — benchmarks, ablations, hyperparameter sweeps, model or LLM evals — with results in context or in markdown/CSV/JSON files. Produces a rigorous lab-notebook report: clean markdown by default, self-contained interactive HTML on request.
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
```

- [ ] **Step 2: Verify SKILL.md structure**

Run: `grep -c "^" SKILL.md && grep -c "^-" SKILL.md`
Expected: file exists, has frontmatter with `name:` and `description:`, 9 checklist items.

- [ ] **Step 3: Install the symlink**

```bash
mkdir -p ~/.claude/skills
ln -sfn /home/dalton/skills/experiment-reporting ~/.claude/skills/experiment-reporting
test -L ~/.claude/skills/experiment-reporting && echo OK
```

Expected: `OK`.

- [ ] **Step 4: Commit**

```bash
git add SKILL.md
git commit -m "feat: SKILL.md workflow, checklist, install symlink"
```

---

### Task 9: End-to-end validation (spec §11 success criteria)

**Files:**
- Create: `tests/test_e2e.py`, `examples/sweep-report.md`, `examples/sweep-stats.json`, `examples/sweep-charts.json`, `examples/sweep-report.html` (generated artifacts)

**Interfaces:**
- Consumes: full skill from Tasks 1–8.
- Produces: proof the five spec §11 success criteria pass; example artifacts future users can skim.

- [ ] **Step 1: Generate stats for the fixture**

```bash
uv run --with numpy,scipy scripts/analyze.py tests/fixtures/sweep.csv \
  --baseline baseline --out examples/sweep-stats.json
```

Expected: exit 0; `examples/sweep-stats.json` exists; method_b comparison has the low-power flag.

- [ ] **Step 2: Draft `examples/sweep-report.md`** by actually following the skill (template + writing-style rules + checklist). Content: the three-variant accuracy/loss sweep as if it were a real experiment — TL;DR with verdict (+3.1 pts method_a, CI, p; method_b not significant), question, setup, results tables (summary + per-run from stats.json values), statistical assessment mirroring stats.json, interpretation, decision, appendix with per-run rows.

- [ ] **Step 3: Author `examples/sweep-charts.json`** — one bar chart of mean accuracy with CI error bars per variant (figure spec only; visuals per the dataviz skill's mark rules if available in the executing session; otherwise a clean default layout with axis titles and legend off).

- [ ] **Step 4: Render the HTML**

```bash
uv run --with markdown,pygments scripts/render_html.py \
  --content examples/sweep-report.md --stats examples/sweep-stats.json \
  --charts examples/sweep-charts.json --out examples/sweep-report.html
```

Expected: exit 0, prints `wrote …`, file > 1 MB.

- [ ] **Step 5: Write `tests/test_e2e.py`**

```python
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
    comp = {c["variant"]: c for c in stats["comparisons"]}["method_a"]
    assert comp["delta"] > 0.03 and comp["p"] < 1e-4
    comp_b = {c["variant"]: c for c in stats["comparisons"]}["method_b"]
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
    assert page.startswith("<!DOCTYPE html>")
    assert "Plotly.newPlot" in page
    assert not re.findall(r'(?:src|href)="(https?://[^"]+)"', page)
    assert len(page) > 1_000_000
```

- [ ] **Step 6: Run the full suite**

Run: `uv run --with pytest,numpy,scipy,markdown,pygments pytest tests/ -v`
Expected: ALL tests pass (Tasks 2–7 suites + e2e).

- [ ] **Step 7: Browser-optional visual check** — open `examples/sweep-report.html` if a browser is available (`explorer.exe` on WSL or `wslview`); confirm tiles, collapsible Appendix, and rendering bar chart appear. If no browser, rely on Step 5's structural assertions.

- [ ] **Step 8: Run the superpowers writing-skills validation** on the finished skill (invoke the `superpowers:writing-skills` skill via the Skill tool; follow its verification steps, e.g. reading SKILL.md fresh and checking the trigger description, lengths, and that referenced files exist: `references/*.md`, `scripts/*.py`, `templates/report-template.md`, `assets/plotly.min.js`).

Run: `ls -la ~/.claude/skills/experiment-reporting/ && grep -l "" references/*.md scripts/*.py templates/*.md`
Expected: symlink resolves; every referenced file exists and is non-empty.

- [ ] **Step 9: Commit**

```bash
git add examples tests/test_e2e.py
git commit -m "test: end-to-end validation artifacts and e2e suite"
```

---

## Plan self-review notes

- Spec coverage: §2 decisions → Tasks 4 (stats flags), 6–7 (HTML), 8 (markdown default/symlink); §3 → Task 5 Step 1; §4 layout → Tasks 1–8; §5 → Task 8; §6 → Task 5 Step 5; §7 → Task 5 Step 3; §8 → Tasks 2–4; §9 → Tasks 6–7; §10 → Task 8 (workflow text); §11 → Task 9. No gaps.
- No placeholders: every code step contains real code; authoring steps name exact files and required content sources.
- Type consistency: `Run` dict shape and stats.json schema are identical across Tasks 2, 4, 6, 7, 9; `describe()` keys match spec §8; `build_page(content_html, tiles_html, charts, plotly_js, plotly_version)` consistent between Tasks 7 tests and implementation.
