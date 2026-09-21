#!/usr/bin/env python3
"""Foreground, budgeted Codex research rounds with a fresh read-only reviewer."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import time
import uuid
from runtime import code_repo, environment, evidence, inside, lock, now, read_json, redact, run_logged, workspace, write_json

SKILL = Path(__file__).resolve().parent.parent

def contract_hash(root):
    paths = [root / "research/brief.md", root / "workspace.local.json", *sorted((root / "spec").rglob("*.md")), *sorted((root / "spec").rglob("*.json"))]
    paths += sorted(p for p in (root / ".agents").rglob("*") if p.is_file() and p.suffix in {".py", ".md", ".json"} and "__pycache__" not in p.parts)
    paths += sorted((root / ".codex").rglob("*.toml"))
    h = hashlib.sha256()
    for path in paths:
        h.update(path.relative_to(root).as_posix().encode())
        h.update(path.read_bytes())
    return h.hexdigest()

def validate_reply(reply, review=False):
    status = {"proceed", "revise", "blocked"} if review else {"continue", "complete", "blocked"}
    if not isinstance(reply, dict) or reply.get("status") not in status:
        raise ValueError("Invalid structured response status")
    if not isinstance(reply.get("summary"), str) or not reply["summary"].strip():
        raise ValueError("Response summary is required")
    if not isinstance(reply.get("next_action"), str):
        raise ValueError("Response next_action is required")
    if not review and (type(reply.get("progress")) is not bool or not isinstance(reply.get("artifacts"), list)
                       or not all(isinstance(x, str) for x in reply["artifacts"])):
        raise ValueError("Executor must return a progress boolean and artifact paths")
    return reply

def call_codex(root, cfg, binary, model, folder, phase, prompt, timeout, code):
    folder.mkdir(parents=True, exist_ok=True)
    final = folder / (phase + ".json")
    if final.exists():
        raise ValueError("Refusing to reuse a stale Codex response path")
    argv = [binary, "exec", "--sandbox", "read-only" if phase == "review" else "workspace-write",
            "--json", "-C", str(root), "--output-schema", str(SKILL / "references" / (phase + ".schema.json")),
            "-o", str(final)]
    if phase != "review" and code:
        argv.extend(["--add-dir", str(code)])
    if model:
        argv.extend(["--model", model])
    argv.append(prompt)
    env, secrets = environment(root, SKILL, cfg.get("codex_env_keys", ["CODEX_API_KEY", "OPENAI_API_KEY"]))
    result = run_logged(argv, root, env, timeout, folder / (phase + ".log"), secrets, root / ".runtime/STOP")
    if result["status"] != "succeeded":
        raise RuntimeError("Codex " + phase + " ended with " + result["status"])
    if not final.is_file() or final.stat().st_size > 1024*1024:
        raise ValueError("Missing or oversized Codex final response")
    reply = json.loads(redact(json.dumps(read_json(final), ensure_ascii=False), secrets))
    write_json(final, reply)
    return validate_reply(reply, phase == "review"), result

def drive(root, cfg, args):
    policy = read_json(root / "spec/autonomy.json")
    keys = ["max_rounds", "total_seconds", "round_seconds", "max_no_progress", "max_revisions"]
    if any(type(policy.get(k)) is not int or policy[k] <= 0 for k in keys):
        raise ValueError("Autonomy limits must be positive integers")
    brief = root / "research/brief.md"
    if not brief.is_file() or len(brief.read_text(encoding="utf-8").strip()) < 10:
        raise ValueError("Initialize research/brief.md with a human research direction first")
    code = code_repo(root, cfg, required=False)
    fingerprint = contract_hash(root)
    limits = {k: policy[k] for k in keys}
    if args.max_rounds is not None:
        if not 1 <= args.max_rounds <= limits["max_rounds"]:
            raise ValueError("--max-rounds may reduce, never exceed, spec/autonomy.json")
        limits["max_rounds"] = args.max_rounds
    binary = shutil.which(args.codex_bin)
    if not args.execute:
        return {"status": "dry-run", "limits": limits, "codex_found": bool(binary),
                "code_repo_available": code is not None, "next": "Review spec/ and pass --execute to run locally."}
    if not binary:
        raise ValueError("Codex CLI is not installed or --codex-bin is invalid")
    if args.resume:
        if not re.fullmatch(r"C-[a-f0-9]{12}", args.resume):
            raise ValueError("Invalid cycle ID")
        state_path = root / "research/cycles" / args.resume / "state.json"
        state = read_json(state_path)
        if state["contract_hash"] != fingerprint:
            raise ValueError("Brief, policy, or machine registry changed; start a newly authorized cycle")
        if args.max_rounds is not None and args.max_rounds != state["limits"]["max_rounds"]:
            raise ValueError("Resume cannot change the original run budget")
        limits = state["limits"]
        if state["status"] == "completed":
            return state
        for attempt in state["attempts"]:
            if attempt["status"] == "running":
                attempt["status"] = "interrupted-unknown-effects"
        # A crashed round keeps its full reservation: resume cannot reset consumed budget.
    else:
        ident = "C-" + uuid.uuid4().hex[:12]
        state_path = root / "research/cycles" / ident / "state.json"
        state = {"schema_version": 1, "type": "research-cycle", "id": ident, "created_at": now(),
                 "contract_hash": fingerprint, "limits": limits, "status": "ready", "spent_seconds": 0.0,
                 "no_progress": 0, "revisions": 0, "attempts": [],
                 "review_independence": "fresh Codex session; model-family independence not established"}
    while len(state["attempts"]) < limits["max_rounds"] and state["spent_seconds"] < limits["total_seconds"]:
        if (root / ".runtime/STOP").exists():
            state["status"] = "stopped"
            break
        reserved = min(limits["round_seconds"], limits["total_seconds"]-state["spent_seconds"])
        if reserved < 1:
            state["status"] = "budget-exhausted"
            break
        number = len(state["attempts"]) + 1
        folder = root / ".runtime/cycles" / state["id"] / f"round-{number:03d}"
        attempt = {"round": number, "status": "running", "started_at": now()}
        state["attempts"].append(attempt)
        state["status"] = "running"
        state["spent_seconds"] += reserved
        write_json(state_path, state)
        started = time.monotonic()
        try:
            prompt = ("Use $research-autopilot for ONE evidence-producing research step, not the whole project. "
                "Read AGENTS.md, spec/, research/brief.md, workspace.local.json, and the cycle state at "
                + str(state_path.relative_to(root)) + ". Resume from durable evidence and prior review.next_action. "
                "Choose survey, hypothesis refinement, local experiment planning/execution, analysis, or report writing "
                "according to the missing evidence. Use the installed specialist skills. Register and update task/ records. "
                "Only the registered local code repository may contain implementation code. No SSH/cloud execution, "
                "no external hooks, no pushes, no installs/purchases without prior authorization. Never read or print .env. "
                "Do not change spec/, the brief, workspace.local.json, agent configuration, skill code, or cycle state. "
                "Never relaunch this driver recursively. Preserve negative results. Use new artifact paths for new evidence. "
                "A smoke run is not scientific evidence. Do not claim completed research solely from created files. "
                "Return structured status, summary, next_action, progress, and workspace-relative artifact paths. "
                "If blocked, explain the blocker; never fabricate an artifact. Round execution budget in seconds: " + str(round(reserved * 0.65, 2)))
            reply, execution = call_codex(root, cfg, binary, args.model, folder, "execute", prompt, reserved * 0.65, code)
            attempt.update(executor=reply, execution=execution)
            if contract_hash(root) != fingerprint:
                raise ValueError("Executor modified a frozen brief/policy/registry")
            if reply["status"] == "blocked":
                attempt["status"], state["status"] = "blocked", "blocked"
                break
            refs = [evidence(root, path) for path in reply["artifacts"]]
            if not refs or not any(r["path"].startswith("research/") and "/cycles/" not in r["path"] for r in refs):
                raise ValueError("A research round must produce a durable research artifact, not only task/state files")
            remaining = reserved-(time.monotonic()-started)
            if remaining <= 0:
                raise RuntimeError("No remaining review budget")
            review_prompt = ("Read $research-review and act as an independent read-only reviewer. "
                "Read the human brief and spec directly. Review these artifact paths from scratch: "
                + json.dumps([r["path"] for r in refs]) + ". No author summary or self-assessment is supplied. "
                "Follow original source locators, experiment receipts, code revisions and protocol where needed. "
                "Assess scientific relevance, counterevidence, missing tests, novelty uncertainty and claim strength. "
                "File existence is not scientific validation. Reject fabricated results and smoke-as-science. "
                "Do not edit files. Return proceed, revise, or blocked with summary and one next_action. "
                "Proceed means the workflow can advance, not independent scientific proof or publication acceptance.")
            review, verification = call_codex(root, cfg, binary, args.model, folder, "review", review_prompt, remaining, code)
            if contract_hash(root) != fingerprint or refs != [evidence(root, r["path"]) for r in refs]:
                raise ValueError("Frozen input or evidence changed during review")
            previous = {e["sha256"] for a in state["attempts"][:-1] for e in a.get("evidence", [])}
            progress = reply["progress"] and any(r["sha256"] not in previous for r in refs)
            attempt.update(status="reviewed", review=review, verification=verification, evidence=refs)
            state["no_progress"] = 0 if progress and review["status"] == "proceed" else state["no_progress"]+1
            state["revisions"] = state["revisions"]+1 if review["status"] == "revise" else 0
            if review["status"] == "blocked":
                state["status"] = "blocked"
            elif state["no_progress"] >= limits["max_no_progress"] or state["revisions"] >= limits["max_revisions"]:
                state["status"] = "stalled"
            elif reply["status"] == "complete" and review["status"] == "proceed":
                state["status"] = "completed"
            else:
                state["status"] = "ready"
        except (Exception, KeyboardInterrupt) as exc:
            attempt.update(status="error", error_type=type(exc).__name__)
            state["status"] = "stopped" if (root / ".runtime/STOP").exists() else "error"
        finally:
            elapsed = time.monotonic()-started
            state["spent_seconds"] = round(state["spent_seconds"]-reserved+elapsed, 3)
            attempt.update(ended_at=now(), seconds=round(elapsed, 3))
            write_json(state_path, state)
        if state["status"] != "ready":
            break
    if state["status"] in {"ready", "running"}:
        state["status"] = "budget-exhausted"
    state["updated_at"] = now()
    write_json(state_path, state)
    return state

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--resume")
    p.add_argument("--max-rounds", type=int)
    p.add_argument("--codex-bin", default="codex")
    p.add_argument("--model")
    a = p.parse_args()
    root, cfg = workspace(a.root)
    with lock(root, "autopilot"):
        state = drive(root, cfg, a)
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0 if state["status"] in {"completed", "dry-run"} else 2

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
