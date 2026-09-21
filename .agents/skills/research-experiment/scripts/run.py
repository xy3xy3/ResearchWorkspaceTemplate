#!/usr/bin/env python3
"""Run one local, sequential seed plan with fresh outputs and provenance receipts."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from runtime import code_repo, digest, environment, git, inside, lock, now, read_json, redact, run_logged, workspace, write_json

SKILL = Path(__file__).resolve().parent.parent

def snapshot(repo, save=None):
    head = git(repo, "rev-parse", "HEAD")
    dirty = bool(git(repo, "status", "--porcelain", "--untracked-files=normal"))
    patch = subprocess.run(["git", "-C", str(repo), "diff", "HEAD", "--binary"],
                           check=True, capture_output=True, timeout=20).stdout
    untracked = git(repo, "ls-files", "--others", "--exclude-standard", "-z").strip("\0").split("\0")
    files = {}
    for name in filter(None, untracked):
        p = repo / name
        files[name] = digest(p) if not p.is_symlink() and p.is_file() and p.stat().st_size <= 8*1024*1024 else "not-snapshotted"
    value = {"commit": head, "dirty": dirty, "diff_sha256": hashlib.sha256(patch).hexdigest(), "untracked": files}
    value["fingerprint"] = hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    if save is not None:
        save.write_bytes(patch)
        os.chmod(save, 0o600)
    return value

def validate(plan):
    if not isinstance(plan, dict):
        raise ValueError("Plan must be an object")
    for key in ["question_id", "hypothesis", "baseline", "comparison_group", "code_commit"]:
        if not isinstance(plan.get(key), str) or not plan[key].strip():
            raise ValueError("Plan requires nonempty " + key)
    if plan.get("purpose") not in {"smoke", "pilot", "confirmatory"}:
        raise ValueError("purpose must be smoke, pilot, or confirmatory")
    seeds = plan.get("seeds")
    if not isinstance(seeds, list) or not 1 <= len(seeds) <= 32 or any(type(s) is not int for s in seeds) or len(set(seeds)) != len(seeds):
        raise ValueError("Use 1..32 distinct integer seeds")
    if not isinstance(plan.get("argv"), list) or not plan["argv"] or any(not isinstance(s, str) or not s for s in plan["argv"]):
        raise ValueError("argv must be a nonempty string array, not a shell command")
    if type(plan.get("timeout_seconds")) is not int or plan["timeout_seconds"] <= 0:
        raise ValueError("timeout_seconds must be a positive integer")
    metric = plan.get("metric", {})
    if not isinstance(metric, dict) or not metric.get("name") or metric.get("direction") not in {"higher", "lower"} or not metric.get("unit"):
        raise ValueError("metric requires name, direction, and unit")
    if not isinstance(plan.get("dataset"), dict) or any(not plan.get("dataset", {}).get(k) for k in ["name", "version", "split"]):
        raise ValueError("dataset requires name, version, and split")
    keys = plan.get("env_keys", [])
    if not isinstance(keys, list) or not all(isinstance(k, str) for k in keys):
        raise ValueError("env_keys must be a string array")
    return plan

def execute(root, cfg, plan, allow_dirty=False):
    validate(plan)
    repo = code_repo(root, cfg)
    policy = read_json(root / "spec/autonomy.json")
    limit = policy.get("experiment_seconds")
    if type(limit) is not int or limit <= 0:
        raise ValueError("experiment_seconds must be a positive integer")
    if plan["timeout_seconds"] * len(plan["seeds"]) > limit:
        raise ValueError("Seed plan exceeds the project experiment wall-time budget")
    env, secrets = environment(root, SKILL, plan.get("env_keys", []))
    run_id = "E-" + uuid.uuid4().hex[:12]
    local = root / ".runtime/experiments" / run_id
    local.mkdir(parents=True)
    before = snapshot(repo, local / "code.diff")
    if before["commit"] != plan["code_commit"]:
        raise ValueError("Plan code_commit does not match the registered code repository HEAD")
    if before["dirty"] and (not allow_dirty or plan["purpose"] == "confirmatory"):
        raise ValueError("Commit code first; --allow-dirty is available only for smoke/pilot")
    manifest = {"schema_version": 1, "type": "experiment", "id": run_id, "started_at": now(),
                "status": "running", "plan": json.loads(redact(json.dumps(plan), secrets)), "source": before,
                "python": sys.version.split()[0], "platform": sys.platform, "trials": [],
                "reproducibility": "git-clean" if not before["dirty"] else "dirty-local-patch; untracked contents not archived"}
    output = root / "research/experiments" / (run_id + ".json")
    write_json(output, manifest)
    started = time.monotonic()
    try:
        for seed in plan["seeds"]:
            folder = local / ("seed-" + str(seed))
            folder.mkdir()
            argv = [s.replace("{seed}", str(seed)).replace("{run_dir}", str(folder)) for s in plan["argv"]]
            trial_env = {**env, "RW_RUN_DIR": str(folder), "RW_SEED": str(seed)}
            result = run_logged(argv, repo, trial_env, min(plan["timeout_seconds"], max(0.001, limit-(time.monotonic()-started))),
                                folder / "process.log", secrets, root / ".runtime/STOP")
            trial = {"seed": seed, **result, "log": (folder / "process.log").relative_to(root).as_posix()}
            if result["status"] == "succeeded":
                try:
                    metrics_path = inside(folder, plan.get("metrics_file", "metrics.json"))
                    if metrics_path.stat().st_size > 1024*1024:
                        raise ValueError("Metrics file too large")
                    metrics = read_json(metrics_path)
                    if not isinstance(metrics, dict) or plan["metric"]["name"] not in metrics:
                        raise ValueError("Expected metric missing")
                    if any(type(v) not in {int, float} or not math.isfinite(v) for v in metrics.values()):
                        raise ValueError("Metrics must be finite numbers, never NaN, booleans, or strings")
                    trial.update(metrics=metrics, metrics_sha256=digest(metrics_path))
                except (OSError, ValueError, TypeError):
                    trial.update(status="invalid_metrics", error="Missing, invalid, or stale-location metrics")
            manifest["trials"].append(trial)
            write_json(output, manifest)
            if trial["status"] != "succeeded":
                break
        manifest["source_after"] = snapshot(repo)
        good = len(manifest["trials"]) == len(plan["seeds"]) and all(t["status"] == "succeeded" for t in manifest["trials"])
        manifest["status"] = "succeeded" if good else "failed"
        if before["fingerprint"] != manifest["source_after"]["fingerprint"]:
            manifest["status"] = "tainted_source_changed"
    except (Exception, KeyboardInterrupt) as exc:
        manifest.update(status="interrupted" if isinstance(exc, KeyboardInterrupt) else "error", error=type(exc).__name__)
    finally:
        manifest.update(ended_at=now(), seconds=round(time.monotonic()-started, 3))
        write_json(output, manifest)
    return manifest, output

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".")
    p.add_argument("--plan", required=True)
    p.add_argument("--allow-dirty", action="store_true")
    a = p.parse_args()
    root, cfg = workspace(a.root)
    with lock(root, "experiment"):
        manifest, path = execute(root, cfg, read_json(inside(root, a.plan)), a.allow_dirty)
    print(json.dumps({"id": manifest["id"], "status": manifest["status"], "manifest": path.relative_to(root).as_posix()}))
    return 0 if manifest["status"] == "succeeded" else 2

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
