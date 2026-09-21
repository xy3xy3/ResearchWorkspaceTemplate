"""Small vendored runtime. Standard library only; no external workspace hooks."""
from __future__ import annotations
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time

SECRET = re.compile(r"TOKEN|SECRET|PASSWORD|API_KEY|CREDENTIAL", re.I)
KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
RESERVED = {"PATH", "PYTHONPATH", "PYTHONHOME", "LD_PRELOAD", "LD_LIBRARY_PATH", "HOME", "CODEX_HOME"}

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def workspace(value):
    root = Path(value).expanduser().resolve()
    cfg = read_json(root / "workspace.local.json")
    if cfg.get("schema_version") != 1:
        raise ValueError("Unsupported workspace schema")
    return root, cfg

def inside(root, relative):
    root = Path(root).resolve()
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Expected a workspace-relative path without '..'")
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Path escapes workspace (including symlink)")
    return path

def evidence(root, relative):
    p = inside(root, relative)
    rel = p.relative_to(root)
    if not rel.parts or rel.parts[0] not in {"research", "ref", "task", "spec"}:
        raise ValueError("Evidence must be in research/, ref/, task/, or spec/")
    if any(part.startswith(".") for part in rel.parts):
        raise ValueError("Hidden files are not evidence")
    if not p.is_file() or not 0 < p.stat().st_size <= 8 * 1024 * 1024:
        raise ValueError("Evidence missing, empty, or larger than 8 MiB")
    return {"path": rel.as_posix(), "sha256": digest(p), "bytes": p.stat().st_size}

def dotenv(path):
    """Literal KEY=value subset; no shell execution or variable expansion."""
    result = {}
    if not Path(path).is_file():
        return result
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        key, sep, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or not KEY.fullmatch(key):
            raise ValueError(f"Invalid dotenv assignment at {Path(path).name}:{line_no}")
        if value.startswith('"'):
            try:
                value, end = json.JSONDecoder().raw_decode(value)
                tail = line.partition("=")[2].strip()[end:].strip()
                if not isinstance(value, str) or (tail and not tail.startswith("#")):
                    raise ValueError()
            except (ValueError, json.JSONDecodeError):
                raise ValueError(f"Invalid double-quoted dotenv value at line {line_no}") from None
        elif value.startswith("'"):
            end = value.find("'", 1)
            if end < 0 or (value[end+1:].strip() and not value[end+1:].strip().startswith("#")):
                raise ValueError(f"Invalid single-quoted dotenv value at line {line_no}")
            value = value[1:end]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].rstrip()
        result[key] = value
    return result

def environment(root, skill, allowed=()):
    """Process > skill .env > workspace .env, only for declared variables."""
    allowed = list(allowed)
    if any(not KEY.fullmatch(k) or k in RESERVED for k in allowed):
        raise ValueError("Invalid or reserved environment variable in allowlist")
    merged = dotenv(Path(root) / ".env")
    merged.update(dotenv(Path(skill) / ".env"))
    merged.update(os.environ)
    env = {k: v for k, v in os.environ.items() if not SECRET.search(k)}
    for key in allowed:
        if key in merged:
            env[key] = merged[key]  # An explicitly empty process value still wins.
    secrets = [v for k, v in merged.items() if SECRET.search(k) and len(v) >= 6]
    return env, secrets

def redact(text, secrets):
    for value in sorted(set(secrets), key=len, reverse=True):
        text = text.replace(value, "<redacted>")
    return text

@contextlib.contextmanager
def lock(root, name):
    if os.name != "posix":
        raise RuntimeError("Use Linux, macOS, or WSL for lock/process-group support")
    import fcntl
    path = Path(root) / ".runtime" / (name + ".lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as f:
        os.chmod(path, 0o600)
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(f"Another {name} process is active") from None
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=20)
    if result.returncode:
        raise ValueError("Git check failed; verify the registered repository and HEAD")
    return result.stdout.strip()

def code_repo(root, cfg, required=True):
    value = cfg.get("code_repo")
    if not value:
        if required:
            raise ValueError("Register code_repo with research-workspace init first")
        return None
    path = Path(value).expanduser()
    path = (root / path).resolve() if not path.is_absolute() else path.resolve()
    if path == root or root.is_relative_to(path):
        raise ValueError("Code repository must not contain or equal the workspace")
    if path.is_relative_to(root) and path.relative_to(root).parts[0] != "repos":
        raise ValueError("Nested code repositories belong under repos/; siblings are also supported")
    if not path.exists() and not required:
        return None
    if Path(git(path, "rev-parse", "--show-toplevel")).resolve() != path:
        raise ValueError("code_repo must be an independent Git repository root")
    git(path, "rev-parse", "HEAD")
    return path

def run_logged(argv, cwd, env, timeout, log, secrets=(), stop=None, max_bytes=8*1024*1024):
    """Foreground process; bounded logs/time; reap the POSIX process group."""
    if os.name != "posix" or timeout <= 0:
        raise ValueError("Execution needs POSIX and a positive timeout")
    if not argv or not all(isinstance(x, str) and x and "\0" not in x for x in argv):
        raise ValueError("argv must be a nonempty array of nonempty strings")
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    status, proc = "error", None
    with tempfile.TemporaryFile() as raw:
        try:
            if stop and Path(stop).exists():
                return {"status": "stopped", "returncode": None, "seconds": 0.0}
            proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                    stdout=raw, stderr=subprocess.STDOUT, start_new_session=True)
            status = "succeeded"
            while proc.poll() is None:
                if stop and Path(stop).exists():
                    status = "stopped"
                    break
                if time.monotonic() - start >= timeout:
                    status = "timeout"
                    break
                if os.fstat(raw.fileno()).st_size > max_bytes:
                    status = "log_limit"
                    break
                time.sleep(0.05)
        except KeyboardInterrupt:
            status = "interrupted"
        finally:
            if proc:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                    if proc.poll() is None:
                        proc.wait(timeout=2)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    pass
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
            raw.seek(0)
            content = raw.read(max_bytes).decode("utf-8", errors="replace")
            if os.fstat(raw.fileno()).st_size > max_bytes:
                content += "\n[LOG TRUNCATED]\n"
                if status == "succeeded":
                    status = "log_limit"
            log.write_text(redact(content, secrets), encoding="utf-8")
            os.chmod(log, 0o600)
    rc = proc.returncode if proc else None
    if status == "succeeded" and rc != 0:
        status = "failed"
    return {"status": status, "returncode": rc, "seconds": round(time.monotonic()-start, 3)}
