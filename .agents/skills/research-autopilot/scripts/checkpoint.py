"""Native-session checkpoint storage. No model, shell, or subprocess execution."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import uuid


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def inside(root, relative):
    p = (root / relative).resolve()
    if not p.is_relative_to(root) or p == root:
        raise ValueError("Path leaves workspace")
    return p


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".checkpoint-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(value, out, ensure_ascii=False, indent=2, allow_nan=False)
            out.write("\n"); out.flush(); os.fsync(out.fileno())
        os.replace(tmp, path)
    finally:
        Path(tmp).unlink(missing_ok=True)


@contextmanager
def locked(root):
    folder = inside(root, ".runtime")
    folder.mkdir(exist_ok=True)
    with (folder / "native-checkpoint.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def contract(root):
    files = [inside(root, "research/brief.md"), *sorted(inside(root, "spec").rglob("*"))]
    result = {}
    for file in files:
        file = inside(root, file.relative_to(root))
        if file.is_file():
            result[str(file.relative_to(root))] = digest(file)
    if "research/brief.md" not in result or "spec/autonomy.json" not in result:
        raise ValueError("Initialize the workspace and its research brief first")
    return result


def evidence(root, name):
    p = inside(root, name)
    rel = p.relative_to(root)
    if rel.parts[0] not in {"research", "ref", "task"} or any(part.startswith(".") for part in rel.parts):
        raise ValueError("Evidence must be a non-secret research/ref/task file")
    if not p.is_file() or not p.stat().st_size or p.suffix.lower() not in {".md", ".json", ".csv", ".txt"}:
        raise ValueError("Evidence must be a nonempty text artifact")
    return {"path": str(rel), "sha256": digest(p)}


def start(root):
    frozen = contract(root)
    budget = load(inside(root, "spec/autonomy.json"))
    for key in ("max_rounds", "total_seconds", "round_seconds", "max_no_progress", "max_revisions"):
        if type(budget.get(key)) is not int or budget[key] <= 0:
            raise ValueError("Invalid autonomy budget: " + key)
    ident = "N-" + uuid.uuid4().hex[:12]
    state = {"schema_version": 2, "mode": "native-subagents", "id": ident,
             "created_at": time.time(), "status": "active", "budget": budget,
             "contract": frozen, "events": [], "next_action": "Read brief and select the smallest useful step."}
    save(inside(root, f"research/cycles/{ident}/state.json"), state)
    return state


def state_path(root, ident):
    if not re.fullmatch(r"N-[a-f0-9]{12}", ident):
        raise ValueError("Expected native checkpoint ID; legacy CLI state is not automatically migrated")
    return inside(root, f"research/cycles/{ident}/state.json")


def gate(root, state):
    if state.get("schema_version") != 2 or state.get("mode") != "native-subagents":
        raise ValueError("Unsupported checkpoint schema")
    if contract(root) != state["contract"]:
        return "contract-changed"
    if inside(root, ".runtime/STOP").exists():
        return "stopped"
    if state["status"] != "active":
        return state["status"]
    if time.time() < state["created_at"]:
        return "clock-changed"
    b, events = state["budget"], state["events"]
    if time.time() - state["created_at"] >= b["total_seconds"] or len(events) >= b["max_rounds"]:
        return "budget-exhausted"
    for status, limit in (("no-progress", b["max_no_progress"]), ("revise", b["max_revisions"])):
        if len(events) >= limit and all(e["status"] == status for e in events[-limit:]):
            return "stalled"
    return "active"


def record(root, ident, *, status, summary, next_action, artifacts, review=None, agents=None):
    if status not in {"continue", "complete", "blocked", "revise", "no-progress"}:
        raise ValueError("Invalid event status")
    if not summary.strip() or not next_action.strip():
        raise ValueError("A summary and next action are required")
    path = state_path(root, ident)
    state = load(path)
    if state["status"] != "active":
        raise ValueError("Terminal checkpoints cannot be overwritten; inspect before starting a linked task")
    refs = [evidence(root, p) for p in artifacts]
    if status in {"continue", "complete"} and not refs:
        raise ValueError("Progress needs existing evidence")
    receipt = evidence(root, review) if review else None
    if status == "complete" and not receipt:
        raise ValueError("Completion requires a saved review; this check does not establish its truth")
    if agents is None:
        agents = []
    if not isinstance(agents, list) or any(not isinstance(a, dict) or
        not all(isinstance(a.get(k), str) and a[k].strip() for k in ("role", "agent_id", "model")) for a in agents):
        raise ValueError("Agents need actual role, agent_id and model strings")
    before = gate(root, state)
    state["events"].append({"at": time.time(), "status": status, "summary": summary,
                            "artifacts": refs, "review": receipt, "agents": agents,
                            "identity_verification": "reported-by-parent-not-authenticated"})
    state["next_action"] = next_action
    if before != "active":
        state["status"] = before  # Keep late evidence; never reset the exhausted budget.
    elif status == "blocked":
        state["status"] = "blocked"
    elif status == "complete":
        state["status"] = "completed"
    else:
        state["status"] = gate(root, state)
    save(path, state)
    return state


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path.cwd())
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("start")
    check = sub.add_parser("check"); check.add_argument("id")
    event = sub.add_parser("record"); event.add_argument("id")
    event.add_argument("--status", choices=["continue", "complete", "blocked", "revise", "no-progress"], required=True)
    event.add_argument("--summary", required=True); event.add_argument("--next-action", required=True)
    event.add_argument("--evidence", action="append", default=[]); event.add_argument("--review")
    event.add_argument("--agents", type=json.loads, default=[])
    a = p.parse_args(); root = a.root.resolve()
    try:
        with locked(root):
            if a.command == "start":
                result = start(root)
            elif a.command == "check":
                result = load(state_path(root, a.id)); result = {"id": a.id, "status": gate(root, result), "next_action": result["next_action"]}
            else:
                result = record(root, a.id, status=a.status, summary=a.summary, next_action=a.next_action,
                                artifacts=a.evidence, review=a.review, agents=a.agents)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] in {"active", "completed"} else 2
    except (ValueError, OSError, KeyError) as exc:
        print(str(exc), file=sys.stderr); return 2

if __name__ == "__main__":
    raise SystemExit(main())
