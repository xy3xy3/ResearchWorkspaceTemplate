#!/usr/bin/env python3
"""Read alphaXiv through Streamable HTTP MCP; never launches another agent."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from service_client import ServiceError, emit, endpoint, object_arg, request_bytes, token

URL = "https://api.alphaxiv.org/mcp/v1"
READ_TOOLS = {"discover_papers", "get_paper_content", "answer_pdf_queries", "read_files_from_github_repository"}


def messages(body: bytes, content_type: str) -> list[dict]:
    text = body.decode("utf-8").strip()
    if not text:
        return []
    if "text/event-stream" not in content_type and not text.startswith(("data:", ":", "event:")):
        value = json.loads(text)
        return value if isinstance(value, list) else [value]
    result, data = [], []
    for line in (text + "\n\n").splitlines():
        if line.startswith("data:"):
            data.append(line[5:].lstrip())
        elif not line and data:
            payload = "\n".join(data); data = []
            if payload != "[DONE]":
                result.append(json.loads(payload))
    return result


class McpClient:
    def __init__(self, key: str, timeout=90):
        self.key, self.timeout = key, timeout
        self.session, self.version, self.counter = None, "2025-03-26", 0
        self.ready = False

    def post(self, payload):
        headers = {"Authorization": "Bearer " + self.key, "Accept": "application/json, text/event-stream"}
        if self.ready:
            headers["MCP-Protocol-Version"] = self.version
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        body, response_headers = request_bytes(endpoint(URL, "api.alphaxiv.org", path="/mcp/v1"),
            headers=headers, payload=payload, timeout=self.timeout)
        self.session = response_headers.get("mcp-session-id", self.session)
        try:
            return messages(body, response_headers.get("content-type", ""))
        except (UnicodeError, ValueError):
            raise ServiceError("Malformed MCP response") from None

    def rpc(self, method, params=None):
        self.counter += 1
        ident = self.counter
        for message in self.post({"jsonrpc": "2.0", "id": ident, "method": method, "params": params or {}}):
            if not isinstance(message, dict) or message.get("id") != ident:
                continue
            if "error" in message:
                raise ServiceError("MCP method failed: " + method)
            value = message.get("result")
            if not isinstance(value, dict) or value.get("isError"):
                raise ServiceError("MCP tool returned an error or invalid result: " + method)
            return value
        raise ServiceError("MCP response has no matching request id")

    def initialize(self):
        if self.ready:
            return
        result = self.rpc("initialize", {"protocolVersion": self.version, "capabilities": {},
            "clientInfo": {"name": "research-workspace", "version": "2"}})
        version = result.get("protocolVersion")
        if not isinstance(version, str) or not version:
            raise ServiceError("MCP protocol negotiation failed")
        self.version, self.ready = version, True
        self.post({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def tools(self):
        self.initialize()
        found, cursor, seen = [], None, set()
        for _ in range(20):
            page = self.rpc("tools/list", {"cursor": cursor} if cursor else {})
            if not isinstance(page.get("tools"), list):
                raise ServiceError("Invalid tools/list result")
            found.extend(page["tools"])
            cursor = page.get("nextCursor")
            if not cursor:
                return {"tools": found}
            if cursor in seen:
                raise ServiceError("Repeated MCP pagination cursor")
            seen.add(cursor)
        raise ServiceError("MCP tool pagination limit reached")

    def call(self, name, arguments):
        if name not in READ_TOOLS:
            raise ServiceError("This client only permits the four documented research read tools")
        available = {t["name"]: t for t in self.tools()["tools"] if isinstance(t, dict) and "name" in t}
        if name not in available:
            raise ServiceError("Tool is unavailable; inspect the current tools/list schema")
        schema = available[name].get("inputSchema", {})
        if not isinstance(schema, dict) or not isinstance(schema.get("required", []), list) or any(not isinstance(k, str) for k in schema.get("required", [])):
            raise ServiceError("Invalid remote tool schema")
        missing = set(schema.get("required", [])) - arguments.keys()
        if missing:
            raise ServiceError("Missing tool arguments: " + ", ".join(sorted(missing)))
        return self.rpc("tools/call", {"name": name, "arguments": arguments})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--timeout", type=int, default=90)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("tools")
    call = sub.add_parser("call"); call.add_argument("tool"); call.add_argument("--args", required=True)
    discover = sub.add_parser("discover")
    discover.add_argument("--keywords", nargs="+", required=True)
    discover.add_argument("--question", required=True)
    discover.add_argument("--published-after")
    content = sub.add_parser("content"); content.add_argument("url"); content.add_argument("--full-text", action="store_true")
    args = p.parse_args()
    try:
        key = token(args.root.resolve(), Path(__file__).resolve().parents[1], "ALPHAXIV_API_TOKEN", "ALPHAXIV_API_KEY")
        client = McpClient(key, args.timeout)
        if args.command == "tools":
            result = client.tools()
        elif args.command == "call":
            result = client.call(args.tool, object_arg(args.args))
        elif args.command == "content":
            result = client.call("get_paper_content", {"url": args.url, "fullText": args.full_text})
        else:
            values = {"keywords": args.keywords, "question": args.question, "difficulty": 5}
            if args.published_after:
                values["published_after"] = args.published_after
            result = client.call("discover_papers", values)
        emit(result, (key,)); return 0
    except (ServiceError, OSError, ValueError) as exc:
        print("alphaXiv: " + str(exc), file=sys.stderr); return 2

if __name__ == "__main__":
    raise SystemExit(main())
