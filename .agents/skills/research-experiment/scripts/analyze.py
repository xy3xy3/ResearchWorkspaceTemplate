#!/usr/bin/env python3
"""Paired-seed descriptive comparison; no automatic significance or novelty claim."""
import argparse
import json
import math
from pathlib import Path
import random
import statistics
import sys
from runtime import evidence, inside, now, read_json, workspace, write_json

def compare(baseline, candidate):
    for run in [baseline, candidate]:
        if run.get("status") != "succeeded" or run["plan"]["purpose"] == "smoke":
            raise ValueError("Only successful non-smoke runs may support comparisons")
        seeds = [t["seed"] for t in run["trials"]]
        if sorted(seeds) != sorted(run["plan"]["seeds"]) or len(set(seeds)) != len(seeds):
            raise ValueError("Incomplete or duplicated planned seeds")
        if run["source"]["fingerprint"] != run["source_after"]["fingerprint"]:
            raise ValueError("Experiment source changed")
        for trial in run["trials"]:
            value = trial["metrics"][run["plan"]["metric"]["name"]]
            if trial["status"] != "succeeded" or trial["returncode"] != 0:
                raise ValueError("Failed trial in a successful receipt")
            if type(value) not in {int, float} or not math.isfinite(value):
                raise ValueError("Metrics must be finite numbers")
    for key in ["dataset", "metric", "comparison_group"]:
        if baseline["plan"][key] != candidate["plan"][key]:
            raise ValueError("Comparison protocol mismatch: " + key)
    metric = baseline["plan"]["metric"]["name"]
    a = {t["seed"]: t["metrics"][metric] for t in baseline["trials"]}
    b = {t["seed"]: t["metrics"][metric] for t in candidate["trials"]}
    if not a or set(a) != set(b) or len(a) != len(baseline["trials"]) or len(b) != len(candidate["trials"]):
        raise ValueError("A paired comparison requires identical, nonduplicate seed sets")
    deltas = [b[s]-a[s] for s in sorted(a)]
    ci = None
    if len(deltas) >= 3:
        rng = random.Random(0)
        samples = sorted(statistics.mean(rng.choices(deltas, k=len(deltas))) for _ in range(2000))
        ci = [samples[49], samples[1949]]
    return {"metric": baseline["plan"]["metric"], "n": len(deltas), "seeds": sorted(a),
            "baseline_mean": statistics.mean(a.values()), "candidate_mean": statistics.mean(b.values()),
            "candidate_minus_baseline": statistics.mean(deltas),
            "paired_delta_stdev": statistics.stdev(deltas) if len(deltas) >= 2 else None,
            "paired_bootstrap_95_percent_interval": ci, "bootstrap_seed": 0, "bootstrap_replicates": 2000 if ci else 0,
            "limitations": "Descriptive paired-seed estimate; not a significance test. No CI for fewer than 3 seeds. Seed variability is not dataset-sampling uncertainty."}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".")
    p.add_argument("--baseline", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    root, _ = workspace(a.root)
    out = inside(root, a.output)
    if not out.is_relative_to(root / "research/findings") or out.exists():
        raise ValueError("Use a new output file under research/findings/")
    result = {"schema_version": 1, "type": "analysis", "at": now(),
              "evidence": [evidence(root, a.baseline), evidence(root, a.candidate)],
              **compare(read_json(inside(root, a.baseline)), read_json(inside(root, a.candidate)))}
    write_json(out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
