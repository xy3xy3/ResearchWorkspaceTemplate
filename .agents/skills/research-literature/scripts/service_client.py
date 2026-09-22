"""Small, local-only dependency for research service clients (Python 3.11+)."""
from __future__ import annotations
import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

MAX_RESPONSE = 16 * 1024 * 1024

class ServiceError(RuntimeError):
    pass


def dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values = {}
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, sep, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            raise ServiceError(f"Invalid dotenv entry at line {n}")
        if value.startswith(("\"", "'")):
            quote = value[0]
            end = value.find(quote, 1)
            if end < 0 or (value[end+1:].strip() and not value[end+1:].lstrip().startswith("#")):
                raise ServiceError(f"Invalid quoted dotenv value at line {n}")
            value = value[1:end]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].rstrip()
        values[key] = value  # No interpolation, source, eval, or shell execution.
    return values


def setting(root: Path, skill: Path, names: tuple[str, ...], default=None):
    # Precedence is by layer, THEN by alias. An explicitly empty value wins.
    for layer in (lambda: os.environ, lambda: dotenv(skill / ".env"), lambda: dotenv(root / ".env")):
        values = layer()
        for name in names:
            if name in values:
                return values[name]
    return default


def token(root: Path, skill: Path, *names: str) -> str:
    value = setting(root, skill, names)
    if not value:
        raise ServiceError("Missing or empty " + names[0])
    if "\n" in value or "\r" in value:
        raise ServiceError("Invalid token")
    return value


def endpoint(value: str, domain: str, *, path: str = "", subdomains=False) -> str:
    p = urlsplit(value)
    host = (p.hostname or "").lower()
    try:
        valid_port = p.port in (None, 443)
    except ValueError:
        valid_port = False
    valid_host = host == domain or (subdomains and host.endswith("." + domain))
    if not (p.scheme == "https" and valid_host and valid_port and not p.username
            and not p.password and not p.query and not p.fragment and p.path.rstrip("/") == path):
        raise ServiceError("Endpoint must use the official HTTPS origin and expected path")
    return "https://" + host + path


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ServiceError("Refusing redirect on authenticated request")


def request_bytes(url: str, *, method="POST", headers=None, payload=None, timeout=90):
    if timeout <= 0:
        raise ServiceError("Timeout must be positive")
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode()
    h = {"Accept": "application/json", "User-Agent": "research-workspace/2"}
    h.update(headers or {})
    if data is not None:
        h["Content-Type"] = "application/json"
    try:
        with build_opener(NoRedirect()).open(Request(url, data=data, headers=h, method=method), timeout=timeout) as response:
            body = response.read(MAX_RESPONSE + 1)
            if len(body) > MAX_RESPONSE:
                raise ServiceError("Response exceeds 16 MiB limit")
            return body, {k.lower(): v for k, v in response.headers.items()}
    except HTTPError as exc:
        # Never print provider bodies: they may reflect Authorization or queries.
        raise ServiceError(f"HTTP {exc.code}; check account, quota, endpoint and permissions") from None
    except (URLError, TimeoutError, OSError):
        raise ServiceError("Network request failed or timed out") from None


def object_arg(text: str) -> dict:
    try:
        value = json.loads(text)
    except (ValueError, TypeError):
        raise ServiceError("Arguments must be a JSON object") from None
    if not isinstance(value, dict):
        raise ServiceError("Arguments must be a JSON object")
    return value


def emit(value, secrets=()):
    text = json.dumps(value, ensure_ascii=False, indent=2)
    for secret in secrets:
        if secret:
            # Replace the JSON-escaped spelling, not just the raw spelling.
            text = text.replace(json.dumps(secret, ensure_ascii=False)[1:-1], "[REDACTED]")
    print(text)
