#!/usr/bin/env python3
"""Initialize a workspace and maintain small, evidence-linked research records."""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import shutil
import sys
import uuid
from runtime import code_repo, evidence, lock, now, read_json, workspace, write_json

KINDS = {"question": "questions", "idea": "ideas", "finding": "findings", "decision": "decisions"}

def identifier(prefix):
    return prefix + "-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]

def locate(root, ident):
    if not re.fullmatch(r"T-[A-Za-z0-9-]+", ident):
        raise ValueError("Invalid task ID")
    matches = [root / "task" / state / ident for state in ("active", "archive")
               if (root / "task" / state / ident / "meta.json").is_file()]
    if len(matches) != 1:
        raise ValueError("Task is missing or duplicated")
    return matches[0]

def initialize(root, args):
    root.mkdir(parents=True, exist_ok=True)
    config_path = root / "workspace.local.json"
    cfg = read_json(config_path) if config_path.exists() else {
        "schema_version": 1, "code_repo": None, "paper_repo": None,
        "codex_env_keys": ["CODEX_API_KEY", "OPENAI_API_KEY"]}
    if args.code_repo:
        cfg["code_repo"] = args.code_repo
        code_repo(root, cfg, required=False)
    if args.paper_repo:
        p = Path(args.paper_repo).expanduser()
        p = (root / p).resolve() if not p.is_absolute() else p.resolve()
        if p == root or root.is_relative_to(p):
            raise ValueError("paper_repo must be independent of the workspace")
        if p.is_relative_to(root) and p.relative_to(root).parts[0] != "paper":
            raise ValueError("Nested paper repository belongs under paper/")
        cfg["paper_repo"] = args.paper_repo
    brief = root / "research/brief.md"
    if args.direction and brief.exists():
        raise ValueError("brief.md already exists; edit it explicitly rather than overwriting")
    for part in ["task/active", "task/archive", "repos", "paper", "ref", "refrepo", ".runtime",
                 "spec", *["research/" + k for k in ["questions", "ideas", "literature", "experiments",
                                                        "findings", "decisions", "reviews", "cycles"]]]:
        (root / part).mkdir(parents=True, exist_ok=True)
    write_json(config_path, cfg)
    if args.direction:
        brief.write_text("# Research brief\n\n" + args.direction +
                         "\n\n## Constraints\nSee spec/autonomy.json and spec/research-policy.md.\n", encoding="utf-8")
    policy = root / "spec/autonomy.json"
    if not policy.exists():
        write_json(policy, {"schema_version": 1, "max_rounds": 6, "total_seconds": 7200,
                            "round_seconds": 1200, "experiment_seconds": 600,
                            "max_no_progress": 2, "max_revisions": 2})
    return {"root": str(root), "configured": True, "brief_exists": brief.exists(),
            "next": "Clone/register an independent code repository, review spec/, then launch Codex here."}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".")
    subs = p.add_subparsers(dest="command", required=True)
    q = subs.add_parser("init")
    q.add_argument("--direction")
    q.add_argument("--code-repo")
    q.add_argument("--paper-repo")
    q = subs.add_parser("task-new")
    q.add_argument("--title", required=True)
    q.add_argument("--question", default="")
    q = subs.add_parser("task-event")
    q.add_argument("id")
    q.add_argument("--kind", choices=["decision", "progress", "verification"], required=True)
    q.add_argument("--text", required=True)
    q.add_argument("--state", choices=["planned", "running", "blocked"])
    q.add_argument("--evidence", action="append", default=[])
    q = subs.add_parser("task-close")
    q.add_argument("id")
    q.add_argument("--outcome", choices=["completed", "abandoned"], required=True)
    q.add_argument("--summary", required=True)
    q.add_argument("--evidence", action="append", default=[])
    q = subs.add_parser("note")
    q.add_argument("--kind", choices=list(KINDS), required=True)
    q.add_argument("--title", required=True)
    q.add_argument("--body", required=True)
    q.add_argument("--task", default="")
    q.add_argument("--evidence", action="append", default=[])
    q = subs.add_parser("status")
    q.add_argument("--write", action="store_true")
    subs.add_parser("doctor")
    args = p.parse_args()
    root = Path(args.root).expanduser().resolve()
    with lock(root, "ledger"):
        if args.command == "init":
            result = initialize(root, args)
        else:
            root, cfg = workspace(root)
            result = {}
            if args.command == "task-new":
                ident = identifier("T")
                folder = root / "task/active" / ident
                folder.mkdir()
                meta = {"schema_version": 1, "id": ident, "title": args.title,
                        "question_id": args.question, "status": "planned", "created_at": now(), "events": []}
                write_json(folder / "meta.json", meta)
                (folder / "task.md").write_text("# " + args.title + "\n\n## 目标与边界\n\n## 实现计划\n\n"
                    "## 验证记录\n\n## 结论与交接\n\n状态、决策事件和证据哈希以 meta.json 为准。\n", encoding="utf-8")
                result = meta
            elif args.command in {"task-event", "task-close"}:
                folder = locate(root, args.id)
                if folder.parent.name != "active":
                    raise ValueError("Archived tasks are immutable; create a linked follow-up task")
                meta = read_json(folder / "meta.json")
                refs = [evidence(root, e) for e in args.evidence]
                if args.command == "task-close":
                    if args.outcome == "completed" and not refs:
                        raise ValueError("Completion requires a report or other durable verification evidence")
                    destination = root / "task/archive" / args.id
                    if destination.exists():
                        raise ValueError("Archive destination already exists")
                    meta.update(status=args.outcome, closed_at=now(), summary=args.summary)
                    meta["events"].append({"at": now(), "kind": "close", "text": args.summary, "evidence": refs})
                    write_json(folder / "meta.json", meta)
                    folder.rename(destination)
                else:
                    meta["events"].append({"at": now(), "kind": args.kind, "text": args.text, "evidence": refs})
                    if args.state:
                        meta["status"] = args.state
                    write_json(folder / "meta.json", meta)
                result = meta
            elif args.command == "note":
                refs = [evidence(root, e) for e in args.evidence]
                if args.kind == "finding" and not refs:
                    raise ValueError("Findings need evidence; use an idea for untested hypotheses")
                if args.task:
                    locate(root, args.task)
                ident = identifier({"question": "Q", "idea": "H", "finding": "F", "decision": "D"}[args.kind])
                dest = root / "research" / KINDS[args.kind] / (ident + ".md")
                text = (f"---\nid: {ident}\nkind: {args.kind}\ntask_id: {json.dumps(args.task)}\n"
                        f"created_at: {now()}\n---\n\n# {args.title}\n\n{args.body}\n\n## Evidence\n")
                text += "\n".join(f"- `{r['path']}` SHA256 `{r['sha256']}`" for r in refs) or "Not yet established."
                dest.write_text(text + "\n", encoding="utf-8")
                result = {"id": ident, "path": dest.relative_to(root).as_posix()}
            elif args.command == "status":
                tasks = [read_json(f) for f in sorted((root / "task/active").glob("*/meta.json"))]
                archived = len(list((root / "task/archive").glob("*/meta.json")))
                result = {"active": tasks, "archived_count": archived}
                if args.write:
                    text = "# Workspace status\n\nGenerated view; task/*/meta.json is authoritative.\n\n"
                    text += "\n".join(f"- {t['id']} [{t['status']}] {t['title']}" for t in tasks) or "No active tasks."
                    text += f"\n\nArchived: {archived}\n"
                    (root / "research/STATUS.md").write_text(text, encoding="utf-8")
            elif args.command == "doctor":
                result = {"python": sys.version.split()[0], "git": shutil.which("git"),
                          "codex": shutil.which("codex"), "network": "not tested",
                          "code_repo": str(code_repo(root, cfg, required=False)),
                          "brief": (root / "research/brief.md").is_file()}
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
