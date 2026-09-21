#!/usr/bin/env python3
"""Bounded metadata retrieval and identifier-based deduplication; not claim verification."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from runtime import environment, lock, now, read_json, workspace, write_json

SKILL = Path(__file__).resolve().parent.parent

def get(url, headers=None):
    request = urllib.request.Request(url, headers={"User-Agent": "ResearchWorkspaceTemplate/0.1", **(headers or {})})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                body = response.read(5 * 1024 * 1024 + 1)
                if len(body) > 5 * 1024 * 1024:
                    raise ValueError("Provider response exceeds 5 MiB")
                return body
        except urllib.error.HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise RuntimeError(f"Provider HTTP {exc.code}") from None
            time.sleep(1 + attempt)
        except urllib.error.URLError:
            if attempt == 2:
                raise RuntimeError("Provider network/TLS/DNS error") from None
            time.sleep(1 + attempt)

def normalize(item):
    title = str(item.get("title", "")).strip()
    if not title:
        raise ValueError("Metadata record has no title")
    doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", str(item.get("doi") or ""), flags=re.I).strip().lower()
    arxiv = re.sub(r"v\d+$", "", str(item.get("arxiv_id") or "").strip())
    ids = (["doi:" + doi] if doi else []) + (["arxiv:" + arxiv] if arxiv else [])
    if item.get("semantic_id"):
        ids.append("s2:" + str(item["semantic_id"]))
    if not ids:
        key = re.sub(r"\W+", "", title.casefold())
        ids = ["title:" + hashlib.sha256(key.encode()).hexdigest()[:20]]
    return {**item, "title": title, "doi": doi or None, "arxiv_id": arxiv or None,
            "id": ids[0], "identifiers": ids, "sources": list(item.get("sources", []))}

def deduplicate(items):
    groups = []
    for original in items:
        item = normalize(original)
        ids = set(item["identifiers"])
        matches = [g for g in groups if ids.intersection(g["identifiers"])]
        for other in matches:
            groups.remove(other)
            ids.update(other["identifiers"])
            item = {**other, **{k: v for k, v in item.items() if v is not None and v != ""}}
            item["sources"] = sorted(set(other["sources"] + item["sources"]))
        item["identifiers"] = sorted(ids)
        item["id"] = next((s for s in sorted(ids) if s.startswith("doi:")), sorted(ids)[0])
        groups.append(item)
    return sorted(groups, key=lambda x: x["id"])

def retrieve(provider, query, limit, env):
    params = urllib.parse.urlencode
    records = []
    if provider == "arxiv":
        body = get("https://export.arxiv.org/api/query?" + params({"search_query": "all:" + query, "start": 0, "max_results": limit}))
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for entry in ET.fromstring(body).findall("a:entry", ns):
            url = entry.findtext("a:id", "", ns)
            records.append({"title": " ".join(entry.findtext("a:title", "", ns).split()),
                            "arxiv_id": url.split("/abs/")[-1], "url": url,
                            "year": entry.findtext("a:published", "", ns)[:4],
                            "authors": [a.findtext("a:name", "", ns) for a in entry.findall("a:author", ns)]})
    elif provider == "crossref":
        body = json.loads(get("https://api.crossref.org/works?" + params({"query": query, "rows": limit})))
        for item in body["message"]["items"]:
            records.append({"title": (item.get("title") or [""])[0], "doi": item.get("DOI"),
                            "url": item.get("URL"), "year": (item.get("issued", {}).get("date-parts") or [[None]])[0][0],
                            "authors": [" ".join(filter(None, [a.get("given"), a.get("family")])) for a in item.get("author", [])]})
    else:
        headers = {"x-api-key": env["SEMANTIC_SCHOLAR_API_KEY"]} if env.get("SEMANTIC_SCHOLAR_API_KEY") else {}
        body = json.loads(get("https://api.semanticscholar.org/graph/v1/paper/search?" + params({
            "query": query, "limit": limit, "fields": "title,year,authors,url,externalIds"}), headers))
        for item in body.get("data", []):
            ids = item.get("externalIds") or {}
            records.append({"title": item.get("title"), "doi": ids.get("DOI"), "arxiv_id": ids.get("ArXiv"),
                            "semantic_id": item.get("paperId"), "url": item.get("url"), "year": item.get("year"),
                            "authors": [a.get("name") for a in item.get("authors", [])]})
    return [{**r, "sources": [provider], "retrieved_at": now(), "verification": "metadata-only"}
            for r in records if r.get("title")]

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default=".")
    p.add_argument("--query", default="")
    p.add_argument("--provider", action="append", choices=["arxiv", "crossref", "semanticscholar"])
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--import-file", type=Path)
    a = p.parse_args()
    if not 1 <= a.limit <= 50 or (not a.query and not a.import_file):
        p.error("Use --query or --import-file; limit must be 1..50")
    root, _ = workspace(a.root)
    env, _ = environment(root, SKILL, ["SEMANTIC_SCHOLAR_API_KEY"])
    records, errors = [], []
    if a.import_file:
        values = read_json(a.import_file)
        if not isinstance(values, list):
            raise ValueError("Import must be a JSON array")
        records = [{**v, "sources": ["manual-import"], "verification": "unverified-import", "retrieved_at": now()} for v in values]
    else:
        for provider in dict.fromkeys(a.provider or ["arxiv", "crossref"]):
            try:
                records.extend(retrieve(provider, a.query, a.limit, env))
            except (ValueError, KeyError, RuntimeError, OSError, ET.ParseError) as exc:
                errors.append({"provider": provider, "error_type": type(exc).__name__, "message": "Request or response validation failed"})
    normalized = deduplicate(records)
    run_id = "L-" + uuid.uuid4().hex[:12]
    with lock(root, "literature"):
        catalog = root / "ref/catalog.json"
        previous = read_json(catalog) if catalog.exists() else []
        write_json(catalog, deduplicate(previous + normalized))
        report = {"schema_version": 1, "type": "literature-search", "id": run_id, "at": now(),
                  "query": a.query, "status": "partial" if errors and records else "failed" if errors else "completed",
                  "records": normalized, "errors": errors,
                  "limitations": "Bounded metadata search, not exhaustive. Metadata existence does not verify claims or novelty."}
        write_json(root / "research/literature" / (run_id + ".json"), report)
    print(json.dumps({"id": run_id, "records": len(normalized), "status": report["status"], "errors": errors}, ensure_ascii=False))
    return 2 if report["status"] == "failed" else 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"ERROR: {type(exc).__name__}: literature operation failed", file=sys.stderr)
        raise SystemExit(2)
