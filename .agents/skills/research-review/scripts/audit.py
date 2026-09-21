#!/usr/bin/env python3
"""Check receipt structure, finite results and evidence hashes; not scientific truth."""
import argparse
import json
import math
from pathlib import Path
import sys
from runtime import digest, evidence, inside, now, read_json, workspace, write_json

def references(value):
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            yield value
        for child in value.values():
            yield from references(child)
    elif isinstance(value, list):
        for child in value:
            yield from references(child)

def audit(root):
    errors, warnings, checked = [], [], 0
    for file in sorted((root / "research").rglob("*.json")):
        try:
            value = read_json(file)
            if not isinstance(value, dict) or value.get("type") not in {"experiment", "analysis", "research-cycle"}:
                continue
            checked += 1
            for ref in references(value):
                actual = evidence(root, ref["path"])
                if actual["sha256"] != ref["sha256"]:
                    errors.append({"file": file.relative_to(root).as_posix(), "reason": "evidence_changed", "path": ref["path"]})
            if value.get("type") == "experiment" and value.get("status") == "succeeded":
                trials, plan = value["trials"], value["plan"]
                seeds = [t["seed"] for t in trials]
                if sorted(seeds) != sorted(plan["seeds"]) or len(set(seeds)) != len(seeds):
                    raise ValueError("seed coverage mismatch")
                if value["source"]["fingerprint"] != value["source_after"]["fingerprint"]:
                    raise ValueError("source changed during experiment")
                for trial in trials:
                    if trial["status"] != "succeeded" or trial["returncode"] != 0:
                        raise ValueError("successful receipt contains a failed trial")
                    metrics = trial["metrics"]
                    if plan["metric"]["name"] not in metrics or any(type(v) not in {int, float} or not math.isfinite(v) for v in metrics.values()):
                        raise ValueError("invalid metrics")
                    raw = inside(root, ".runtime/experiments/" + value["id"] + "/seed-" + str(trial["seed"]) + "/" + plan.get("metrics_file", "metrics.json"))
                    if not raw.is_file():
                        warnings.append({"file": file.relative_to(root).as_posix(), "reason": "raw_metrics_unavailable"})
                    elif digest(raw) != trial["metrics_sha256"] or read_json(raw) != metrics:
                        raise ValueError("raw metrics disagree with receipt")
                if value["source"]["dirty"]:
                    warnings.append({"file": file.relative_to(root).as_posix(), "reason": "dirty_code_requires_local_patch_and_untracked_files"})
        except (ValueError, OSError, KeyError, TypeError) as exc:
            errors.append({"file": file.relative_to(root).as_posix(), "reason": str(exc)})
    claims = root / "research/claims.json"
    if claims.exists():
        try:
            data = read_json(claims)
            if not isinstance(data, list):
                raise ValueError("claims.json must be an array")
            for claim in data:
                checked += 1
                if claim.get("status") == "supported":
                    if not claim.get("evidence"):
                        raise ValueError("supported claim has no evidence")
                    for ref in claim["evidence"]:
                        if not ref.get("locator") or evidence(root, ref["path"])["sha256"] != ref.get("sha256"):
                            raise ValueError("claim locator or hash invalid")
                        path = inside(root, ref["path"])
                        if path.suffix == ".json":
                            source = read_json(path)
                            if isinstance(source, dict) and source.get("type") == "experiment":
                                if source.get("status") != "succeeded" or source["plan"]["purpose"] == "smoke":
                                    raise ValueError("claim cites failed/smoke experiment as support")
        except (ValueError, OSError, KeyError, TypeError) as exc:
            errors.append({"file": "research/claims.json", "reason": str(exc)})
    return {"schema_version": 1, "type": "evidence-audit", "at": now(), "checked_records": checked,
            "status": "FAIL" if errors else "WARN" if warnings else "PASS" if checked else "NOT_APPLICABLE",
            "errors": errors, "warnings": warnings,
            "scope": "Structural checks only. No independent reproduction, semantic citation verification, novelty proof, or scientific acceptance."}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".")
    p.add_argument("--output")
    a = p.parse_args()
    root, _ = workspace(a.root)
    result = audit(root)
    if a.output:
        out = inside(root, a.output)
        if not out.is_relative_to(root / "research/reviews") or out.exists():
            raise ValueError("Use a new output under research/reviews/")
        write_json(out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] in {"FAIL", "WARN"} else 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
