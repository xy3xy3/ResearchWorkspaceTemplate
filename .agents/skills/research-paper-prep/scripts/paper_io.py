"""Filesystem and process helpers shipped with the paper preparation skill."""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import re
import signal
import subprocess
from urllib.parse import urlsplit


def contained(root: Path, relative: str) -> Path:
    root = root.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError("Path leaves the workspace")
    return path


def paper_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,100}", value) or ".." in value:
        raise ValueError("Use a short paper id containing letters, numbers, dots, underscores or hyphens")
    return value


def repo_url(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"git@[A-Za-z0-9.-]+:[A-Za-z0-9_./-]+", value):
        path = value.split(":", 1)[1]
    else:
        p = urlsplit(value)
        if (p.scheme != "https" or not p.hostname or p.username or p.password
                or p.query or p.fragment or p.port not in (None, 443)):
            raise ValueError("Repository URL must be credential-free HTTPS or git@host:path")
        path = p.path.lstrip("/")
        if not re.fullmatch(r"[A-Za-z0-9_./-]+", path):
            raise ValueError("Invalid repository path")
    if len(path.split("/")) < 2 or any(x in ("", ".", "..") for x in path.split("/")):
        raise ValueError("Invalid repository path")
    return value


def digest(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def run(argv: list[str], cwd: Path, log: Path, timeout: int, env=None):
    if timeout <= 0:
        raise ValueError("Timeout must be positive")
    with log.open("wb") as output:
        proc = subprocess.Popen(argv, cwd=cwd, stdout=output, stderr=subprocess.STDOUT,
            env=env, start_new_session=os.name == "posix")
        try:
            code = proc.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            try:
                if os.name == "posix":
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
            except ProcessLookupError:
                pass
            proc.wait()
            raise RuntimeError("Local command interrupted or timed out") from None
    if code:
        with log.open("rb") as f:
            f.seek(max(0, log.stat().st_size - 1200))
            detail = f.read().decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Local command failed ({code}): {detail}")
