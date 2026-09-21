#!/usr/bin/env python3
"""Publish text-only paper records from existing Markdown or a local PDF parser."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import urlsplit, parse_qsl
from paper_io import contained, digest, paper_id, repo_url, run


def text_only(markdown: str) -> tuple[str, int]:
    """Remove visual embeds, not captions/equations; omissions stay explicit."""
    count = 0
    def omitted(match):
        nonlocal count
        count += 1
        alt = match.groupdict().get("alt", "") or "visual content"
        return "[Visual omitted: " + alt.replace("\n", " ") + "]"

    # Parser output is data. Never execute embedded HTML or scripts.
    markdown = re.sub(r"<(?:svg|picture|script)\b[^>]*>.*?</(?:svg|picture|script)\s*>", omitted, markdown, flags=re.I | re.S)
    markdown = re.sub(r"<img\b[^>]*>", omitted, markdown, flags=re.I | re.S)
    # Balanced destinations permit filenames containing parentheses.
    start = re.compile(r"!\[(?P<alt>[^\]]*)\]\(")
    result, cursor = [], 0
    while (m := start.search(markdown, cursor)) is not None:
        depth, i = 1, m.end()
        while i < len(markdown) and depth:
            if markdown[i] == "\\":
                i += 2; continue
            if markdown[i] == "(": depth += 1
            if markdown[i] == ")": depth -= 1
            i += 1
        if depth:
            raise ValueError("Unbalanced Markdown image; fix the parsed source before importing")
        result.extend([markdown[cursor:m.start()], omitted(m)])
        cursor = i
    result.append(markdown[cursor:]); markdown = "".join(result)
    markdown = re.sub(r"!\[(?P<alt>[^\]]*)\](?:\[[^\]]*\])?", omitted, markdown)
    markdown = re.sub(r"\\includegraphics(?:\[[^\]]*\])?\{[^}]*\}", omitted, markdown)
    markdown = re.sub(r"(?im)^\s*\[[^\]]+\]:\s*(?:<?data:image/\S+|\S+\.(?:png|jpe?g|gif|svg|webp|bmp)(?:[?#]\S*)?>?)(?:\s+.*)?$", "", markdown)
    markdown = re.sub(r"\[(?P<alt>[^\]]+)\]\([^\n)]*\.(?:png|jpe?g|gif|svg|webp|bmp)(?:\?[^)]*)?\)", omitted, markdown, flags=re.I)
    if re.search(r"data:image/", markdown, re.I):
        raise ValueError("Unrecognized inline image data remains; no paper record was published")
    if not markdown.strip():
        raise ValueError("Parsed Markdown is empty")
    return markdown.rstrip() + "\n", count


def parser_command(parser, executable, pdf, output):
    if parser == "mineru":
        return [executable or "mineru", "-p", str(pdf), "-o", str(output), "-b", "pipeline"]
    if parser == "paddleocr":
        return [executable or "paddleocr", "pp_structurev3", "-i", str(pdf), "--save_path", str(output)]
    raise ValueError("Unknown local parser")


def natural_key(path):
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", path.as_posix())]


def prepare(root: Path, ident: str, source: Path, *, parser: str, source_url: str,
            repository=None, execute=False, executable=None, timeout=1800, join_pages=False):
    root, source = root.resolve(), source.resolve()
    paper_id(ident)
    if timeout <= 0:
        raise ValueError("Timeout must be positive")
    if parser not in ("mineru", "paddleocr"):
        raise ValueError("Declare mineru or paddleocr as the parser")
    u = urlsplit(source_url)
    if u.scheme != "https" or not u.hostname or u.username or u.password:
        raise ValueError("Source URL must be credential-free HTTPS")
    if any(k.lower() in {"token", "access_token", "api_key", "key", "signature", "x-amz-signature"} for k, _ in parse_qsl(u.query)):
        raise ValueError("Use a canonical source URL, not a signed or credential-bearing download URL")
    if repository:
        repository = repo_url(repository)
    if not source.is_file() or source.stat().st_size > 200 * 1024 * 1024:
        raise ValueError("Source missing or larger than this wrapper's 200 MiB limit")
    if source.suffix.lower() not in (".md", ".pdf"):
        raise ValueError("Source must be .md or .pdf")
    target = contained(root, "ref/" + ident)
    if target.exists():
        raise ValueError("Paper record exists; use a new version id or review a manual update")
    scratch = contained(root, ".runtime/paper-prep")
    scratch.mkdir(parents=True, exist_ok=True)
    source_hash = digest(source)
    command, fragments = None, []
    with tempfile.TemporaryDirectory(prefix=ident + "-", dir=scratch) as temp:
        temp = Path(temp)
        if source.suffix.lower() == ".pdf":
            if not execute:
                raise ValueError("PDF parsing requires --execute; importing existing .md needs no parser process")
            with source.open("rb") as f:
                if f.read(5) != b"%PDF-":
                    raise ValueError("Input is not a PDF")
            pdf, output = temp / "input.pdf", temp / "output"
            shutil.copyfile(source, pdf); output.mkdir()
            command = parser_command(parser, executable, pdf, output)
            run(command, temp, temp / "parser.log", timeout)
            paths = sorted(output.rglob("*.md"), key=natural_key)
            if not paths or (len(paths) > 1 and not join_pages):
                raise ValueError("Expected one Markdown output; review multi-page files then use --join-pages")
            for path in paths:
                if not path.resolve().is_relative_to(output.resolve()):
                    raise ValueError("Parser output symlink leaves the temporary directory")
                fragments.append((path.relative_to(output).as_posix(), path.read_text(encoding="utf-8-sig")))
        else:
            fragments.append(("provided.md", source.read_text(encoding="utf-8-sig")))
        text = "\n\n".join((f"<!-- parser-fragment: {name} -->\n" if len(fragments) > 1 else "") + value for name, value in fragments)
        text, removed = text_only(text)
        if digest(source) != source_hash:
            raise ValueError("Source changed during preparation")
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".staging-", dir=target.parent) as stage:
            stage = Path(stage)
            (stage / "paper.md").write_text(text, encoding="utf-8")
            record = {"id": ident, "source_url": source_url, "parser": parser,
                "mode": "local-parser" if command else "imported-parser-markdown",
                "parser_execution_verified": bool(command), "parser_version": "not-probed",
                "source_sha256": source_hash, "markdown_sha256": digest(stage / "paper.md"),
                "fragments": [x[0] for x in fragments], "visual_embeds_removed": removed,
                "visual_evidence_retained": False, "verification": "parsed-text-not-scientifically-verified",
                "prepared_at": datetime.now(timezone.utc).isoformat()}
            (stage / "source.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if repository:
                (stage / "repo.txt").write_text(repository + "\n", encoding="utf-8")
            if target.exists():
                raise ValueError("Paper record appeared during preparation")
            stage.rename(target)
    # Only our temporary copies are removed. The caller's input is never deleted.
    return record


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--id", required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--source-url", required=True)
    p.add_argument("--repo-url")
    p.add_argument("--parser", choices=["mineru", "paddleocr"], required=True)
    p.add_argument("--parser-exe")
    p.add_argument("--timeout", type=int, default=1800)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--join-pages", action="store_true")
    a = p.parse_args()
    try:
        result = prepare(a.root, a.id, a.source, parser=a.parser, source_url=a.source_url,
            repository=a.repo_url, execute=a.execute, executable=a.parser_exe,
            timeout=a.timeout, join_pages=a.join_pages)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr); return 2

if __name__ == "__main__":
    raise SystemExit(main())
