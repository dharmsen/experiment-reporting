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
