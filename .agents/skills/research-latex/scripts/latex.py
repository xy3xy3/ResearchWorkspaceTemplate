"""Scaffold/check/build a separate manuscript repository. Never starts a model."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
from paper_repo import paper_repo, local

ASSETS = Path(__file__).resolve().parents[1] / "assets"


def initialize(repo):
    sources = [p for p in (ASSETS / "article").rglob("*") if p.is_file()]
    if not sources:
        raise ValueError("Missing bundled article template")
    targets = [(p, local(repo, p.relative_to(ASSETS / "article"))) for p in sources]
    if any(target.exists() for _, target in targets):
        raise ValueError("Template files already exist; edit the existing manuscript, do not overwrite it")
    for source, target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return {"status": "created", "files": [str(p.relative_to(repo)) for _, p in targets], "venue": "generic-article-not-submission-template"}


def uncomment(text):
    return re.sub(r"(?<!\\)%[^\n]*", "", text)


def check(repo, main="main.tex"):
    # Bounded static assistance, not a TeX interpreter or a citation-faithfulness audit.
    errors, warnings, visited, labels, cites, refs = [], [], set(), [], set(), set()
    def walk(relative):
        file = local(repo, relative)
        if file in visited:
            return
        visited.add(file)
        if not file.is_file():
            errors.append("Missing TeX source: " + str(relative)); return
        text = uncomment(file.read_text(encoding="utf-8"))
        if re.search(r"\b(TBD|TODO|DATA_NEEDED)\b", text):
            warnings.append("Unresolved placeholders: " + str(relative))
        labels.extend(re.findall(r"\\label\{([^}]+)\}", text))
        refs.update(re.findall(r"\\(?:ref|eqref|autoref|pageref)\{([^}]+)\}", text))
        for group in re.findall(r"\\(?:cite[a-zA-Z]*|nocite)\*?(?:\[[^\]]*\])*\{([^}]+)\}", text):
            cites.update(k.strip() for k in group.split(",") if k.strip() != "*")
        for target in re.findall(r"\\(?:input|include)\{([^}]+)\}", text):
            if "\\" in target or "#" in target:
                warnings.append("Dynamic include needs real TeX compilation"); continue
            path = Path(target)
            walk(str(path if path.suffix else path.with_suffix(".tex")))
    walk(main)
    bibkeys = []
    for file in repo.rglob("*.bib"):
        if ".git" in file.relative_to(repo).parts or ".build" in file.relative_to(repo).parts:
            continue
        file = local(repo, file.relative_to(repo))
        bibkeys.extend(re.findall(r"@(?!(?:comment|string|preamble)\b)\w+\s*\{\s*([^,\s]+)\s*,", file.read_text(encoding="utf-8"), re.I))
    errors.extend("Undefined reference: " + k for k in sorted(refs - set(labels)))
    errors.extend("Missing bibliography key: " + k for k in sorted(cites - set(bibkeys)))
    errors.extend("Duplicate label: " + k for k in sorted(set(labels)) if labels.count(k) > 1)
    errors.extend("Duplicate bibliography key: " + k for k in sorted(set(bibkeys)) if bibkeys.count(k) > 1)
    return {"status": "FAIL" if errors else "WARN" if warnings else "PASS", "errors": errors,
            "warnings": warnings, "coverage": "literal includes, common citations and references only; macros/graphicspath/conditional TeX require compilation"}


def build(repo, main="main.tex", timeout=180, execute=False):
    source = local(repo, main)
    if not source.is_file() or source.suffix != ".tex" or timeout <= 0:
        raise ValueError("A TeX entry file and positive timeout are required")
    output = local(repo, ".build")
    command = ["latexmk", "-norc", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
               "-pdflatex=pdflatex -no-shell-escape %O %S", "-outdir=" + str(output), str(source)]
    if not execute:
        return {"status": "planned", "argv": command}
    if not shutil.which("latexmk"):
        raise ValueError("latexmk is not installed; no dependencies were installed automatically")
    ignored = subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", ".build/probe"], capture_output=True, timeout=10)
    if ignored.returncode:
        raise ValueError("Ignore .build/ in the paper repository before compiling")
    output.mkdir(exist_ok=True)
    log = output / "build-driver.log"
    with log.open("wb") as handle:
        proc = subprocess.Popen(command, cwd=repo, stdout=handle, stderr=subprocess.STDOUT,
                                start_new_session=(os.name == "posix"))
        try:
            rc = proc.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            try:
                if os.name == "posix": os.killpg(proc.pid, signal.SIGKILL)
                else: proc.kill()
            except ProcessLookupError:
                pass
            proc.wait(); raise ValueError("Build interrupted or timed out; inspect .build/build-driver.log") from None
    pdf = output / (source.stem + ".pdf")
    if rc or not pdf.is_file():
        raise ValueError("Build failed; inspect .build/build-driver.log")
    return {"status": "built", "pdf": str(pdf.relative_to(repo)), "log": str(log.relative_to(repo)),
            "visual_review": "not-performed-by-this-script", "scientific_verification": False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path.cwd()); p.add_argument("--paper-repo")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    c = sub.add_parser("check"); c.add_argument("--main", default="main.tex")
    b = sub.add_parser("build"); b.add_argument("--main", default="main.tex")
    b.add_argument("--timeout", type=int, default=180); b.add_argument("--execute", action="store_true")
    a = p.parse_args()
    try:
        repo = paper_repo(a.root, a.paper_repo)
        result = initialize(repo) if a.command == "init" else check(repo, a.main) if a.command == "check" else build(repo, a.main, a.timeout, a.execute)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 2 if result["status"] == "FAIL" else 0
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr); return 2

if __name__ == "__main__":
    raise SystemExit(main())
