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
