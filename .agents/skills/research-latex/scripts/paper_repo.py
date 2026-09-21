"""Resolve a separately versioned manuscript repository without creating it."""
from pathlib import Path
import json
import subprocess


def paper_repo(root: Path, explicit=None) -> Path:
    root = root.resolve()
    value = explicit
    if value is None:
        config = root / "workspace.local.json"
        if not config.is_file():
            raise ValueError("Register paper_repo or pass --paper-repo explicitly")
        value = json.loads(config.read_text(encoding="utf-8")).get("paper_repo")
    if not isinstance(value, (str, Path)) or not str(value):
        raise ValueError("A separate paper repository is required")
    repo = (root / value).resolve()
    if repo == root or not repo.is_dir():
        raise ValueError("Paper repository must exist and differ from the workspace")
    result = subprocess.run(["git", "-C", str(repo), "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=10)
    if result.returncode or Path(result.stdout.strip()).resolve() != repo:
        raise ValueError("Expected an independent Git repository root")
    if repo.is_relative_to(root):
        ignored = subprocess.run(["git", "-C", str(root), "check-ignore", "-q", str(repo.relative_to(root) / "probe")], capture_output=True, timeout=10)
        if ignored.returncode:
            raise ValueError("Nested paper repository must be ignored by the outer workspace")
    return repo


def local(repo, relative):
    p = (repo / relative).resolve()
    if not p.is_relative_to(repo) or p == repo or ".git" in p.relative_to(repo).parts:
        raise ValueError("Path escapes the manuscript area")
    return p
