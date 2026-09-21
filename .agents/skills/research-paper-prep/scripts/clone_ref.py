#!/usr/bin/env python3
"""Rebuild an ignored reference checkout from ref/<id>/repo.txt; never run it."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from paper_io import contained, paper_id, repo_url, run


def clone(root: Path, ident: str, *, execute=False, timeout=300):
    root = root.resolve(); paper_id(ident)
    if timeout <= 0:
        raise ValueError("Timeout must be positive")
    record_dir = contained(root, "ref/" + ident)
    lines = [line.strip() for line in (record_dir / "repo.txt").read_text().splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError("repo.txt must contain exactly one repository URL")
    url = repo_url(lines[0])
    target = contained(root, "refrepo/" + ident)
    if target.exists():
        raise ValueError("Reference checkout exists; no automatic pull, reset or overwrite")
    top = subprocess.check_output(["git", "-C", str(root), "rev-parse", "--show-toplevel"], text=True, timeout=10).strip()
    if Path(top).resolve() != root:
        raise ValueError("--root must be the workspace Git root")
    check = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", "--", f"refrepo/{ident}/probe"], check=False, timeout=10)
    if check.returncode != 0:
        raise ValueError("refrepo destination is not ignored; fix .gitignore first")
    if not execute:
        return {"status": "planned", "url": url, "destination": f"refrepo/{ident}"}
    target.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_LFS_SKIP_SMUDGE="1")
    with tempfile.TemporaryDirectory(prefix=".clone-", dir=target.parent) as temp:
        temp = Path(temp)
        checkout = temp / "checkout"
        run(["git", "-c", "core.hooksPath=" + os.devnull, "-c", "protocol.file.allow=never",
             "-c", "protocol.ext.allow=never", "clone", "--depth", "1", "--", url, str(checkout)],
            root, temp / "clone.log", timeout, env)
        head = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True, timeout=10).strip()
        if target.exists():
            raise ValueError("Destination appeared during clone")
        checkout.rename(target)
    record = {"url": url, "commit": head, "destination": f"refrepo/{ident}",
              "submodules": "not-fetched", "lfs": "smudge-skipped"}
    # Checkout receipt is local. repo.txt remains the versioned source of truth.
    (target / ".git" / "research-checkout.json").write_text(json.dumps(record, indent=2) + "\n")
    return {"status": "cloned", **record}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("id")
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--execute", action="store_true")
    p.add_argument("--timeout", type=int, default=300)
    a = p.parse_args()
    try:
        print(json.dumps(clone(a.root, a.id, execute=a.execute, timeout=a.timeout), indent=2)); return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr); return 2

if __name__ == "__main__":
    raise SystemExit(main())
