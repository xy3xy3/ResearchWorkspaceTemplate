#!/usr/bin/env python3
"""Read Sciverse search, content and evidence APIs; no SDK or agent subprocess."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import quote, urlencode
from service_client import ServiceError, emit, endpoint, object_arg, request_bytes, setting, token

DEFAULT_BASE = "https://api.sciverse.space"


def search_payload(values):
    keys = ("query", "page", "page_size", "fields", "collection", "freshness_boost", "impact_boost", "language_affinity")
    body = {k: values[k] for k in keys if k in values}
    filters = list(values.get("filters", []))
    for key, field, op in [("year_from", "publication_published_year", "GTE"),
        ("year_to", "publication_published_year", "LTE"), ("title_contains", "title", "CONTAINS"),
        ("abstract_contains", "abstract", "CONTAINS"), ("authors", "author", "IN"),
        ("journals", "publication_venue_name_unified", "IN"), ("subjects", "subjects", "IN")]:
        if key in values:
            filters.append({"field": field, "operator": "FILTER_OP_" + op, "value": values[key]})
    if filters:
        body["filters"] = filters
    if "sort" in values:
        body["sort"] = values["sort"]
    return body


def route(command, values):
    if command == "catalog":
        return "GET", "/meta-catalog", values, None
    if command == "search":
        return "POST", "/meta-search", None, search_payload(values)
    if command == "semantic":
        if not values.get("query"):
            raise ServiceError("semantic requires query")
        values = dict(values)
        mode = values.pop("mode", "balanced")
        modes = {"fast": {"retrieval": "es"}, "balanced": {"retrieval": "hybrid"},
                 "quality": {"retrieval": "hybrid", "sub_queries": 3}}
        if mode not in modes:
            raise ServiceError("mode must be fast, balanced or quality")
        return "POST", "/agentic-search", None, {**modes[mode], **values}
    if command == "content":
        if not values.get("doc_id"):
            raise ServiceError("content requires doc_id from a search result")
        return "GET", "/content", values, None
    if command == "relations":
        return "POST", "/meta-paper-relations", None, values
    if command == "schema-capabilities":
        return "GET", "/paper-schema", None, None
    if command == "schema-search":
        return "POST", "/paper-schema/search", None, values
    if command == "evidence-search":
        return "POST", "/paper-schema/evidence/search", None, values
    if command == "evidence-get":
        if not values.get("schema_id") or not values.get("evidence_id"):
            raise ServiceError("evidence-get requires schema_id and evidence_id")
        parts = [quote(str(values[k]), safe="") for k in ("schema_id", "evidence_id")]
        return "GET", f"/paper-schema/schemas/{parts[0]}/evidence/{parts[1]}", None, None
    if command == "provenance":
        return "POST", "/paper-schema/resolve-provenance", None, values
    raise ServiceError("Unsupported operation")


def retrieve(command, values, key, base=DEFAULT_BASE, timeout=90):
    base = endpoint(base, "sciverse.space", subdomains=True)
    method, path, query, body = route(command, values)
    if query:
        path += "?" + urlencode({k: str(v).lower() if isinstance(v, bool) else v for k, v in query.items()}, doseq=True)
    raw, _ = request_bytes(base + path, method=method,
        headers={"Authorization": "Bearer " + key, "X-Sciverse-Source": "research-workspace"},
        payload=body, timeout=timeout)
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeError):
        raise ServiceError("Sciverse returned invalid JSON") from None
    if not isinstance(result, dict):
        raise ServiceError("Sciverse returned a non-object response")
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--timeout", type=int, default=90)
    p.add_argument("command", choices=["catalog", "search", "semantic", "content", "relations",
        "schema-capabilities", "schema-search", "evidence-search", "evidence-get", "provenance"])
    p.add_argument("--args", default="{}")
    args = p.parse_args()
    try:
        root, skill = args.root.resolve(), Path(__file__).resolve().parents[1]
        key = token(root, skill, "SCIVERSE_API_TOKEN")
        base = setting(root, skill, ("SCIVERSE_BASE_URL",), DEFAULT_BASE)
        result = retrieve(args.command, object_arg(args.args), key, base, args.timeout)
        emit(result, (key,)); return 0
    except (ServiceError, OSError, ValueError) as exc:
        print("Sciverse: " + str(exc), file=sys.stderr); return 2

if __name__ == "__main__":
    raise SystemExit(main())
