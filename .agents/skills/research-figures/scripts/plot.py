"""Create a reproducible single-series plot from supplied CSV, never invented values."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
from paper_repo import paper_repo, local


def read_rows(source, x, y, kind, error=None):
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        needed = {x, y} | ({error} if error else set())
        if not needed.issubset(reader.fieldnames or []):
            raise ValueError("CSV is missing requested columns")
        rows = list(reader)
    if not rows:
        raise ValueError("CSV has no observations")
    xs, ys, es = [], [], []
    for row in rows:
        xv = row[x] if kind == "bar" else float(row[x])
        yv = float(row[y]); ev = float(row[error]) if error else 0.0
        if (kind != "bar" and not math.isfinite(xv)) or not math.isfinite(yv) or not math.isfinite(ev) or ev < 0:
            raise ValueError("Coordinates must be finite; error magnitudes must be nonnegative")
        xs.append(xv); ys.append(yv); es.append(ev)
    if kind == "bar" and len(set(xs)) != len(xs):
        raise ValueError("Repeated bar categories require explicit aggregation upstream")
    return xs, ys, es


def render(source, out, *, x, y, xlabel, ylabel, kind="line", error=None, error_meaning=None):
    if kind not in {"line", "bar", "scatter"}:
        raise ValueError("Unknown plot type")
    if not xlabel.strip() or not ylabel.strip() or (error and not error_meaning):
        raise ValueError("Axis labels and the meaning of error bars are required")
    xs, ys, es = read_rows(source, x, y, kind, error)
    if out.exists():
        raise ValueError("Figure folder exists; preserve its provenance or choose a new figure ID")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent, prefix=".figure-") as d:
        stage = Path(d)
        fig, ax = plt.subplots()
        try:
            if kind == "bar": ax.bar(xs, ys, yerr=es if error else None)
            elif error: ax.errorbar(xs, ys, yerr=es, fmt="o-" if kind == "line" else "o")
            elif kind == "line": ax.plot(xs, ys, marker="o")
            else: ax.scatter(xs, ys)
            ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); fig.tight_layout()
            fig.savefig(stage / "figure.svg"); fig.savefig(stage / "figure.pdf")
        finally:
            plt.close(fig)
        shutil.copyfile(source, stage / "data.csv")
        # Standalone authoring source: no workspace helper imports needed to rerender.
        spec = {"x": x, "y": y, "xlabel": xlabel, "ylabel": ylabel, "kind": kind,
                "error": error, "error_meaning": error_meaning}
        recipe = "import csv,json\nfrom pathlib import Path\nimport matplotlib\nmatplotlib.use('Agg')\nimport matplotlib.pyplot as plt\n"
        recipe += "p=Path(__file__).resolve().parent\ns=" + repr(spec) + "\n"
        recipe += "with (p/'data.csv').open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))\n"
        recipe += "x=[r[s['x']] if s['kind']=='bar' else float(r[s['x']]) for r in rows]\ny=[float(r[s['y']]) for r in rows]\ne=[float(r[s['error']]) for r in rows] if s['error'] else None\n"
        recipe += "fig,ax=plt.subplots()\nif s['kind']=='bar': ax.bar(x,y,yerr=e)\nelif e is not None: ax.errorbar(x,y,yerr=e,fmt='o-' if s['kind']=='line' else 'o')\nelif s['kind']=='line': ax.plot(x,y,marker='o')\nelse: ax.scatter(x,y)\n"
        recipe += "ax.set_xlabel(s['xlabel']); ax.set_ylabel(s['ylabel']); fig.tight_layout()\nfig.savefig(p/'figure.svg'); fig.savefig(p/'figure.pdf'); plt.close(fig)\n"
        (stage / "figure.py").write_text(recipe, encoding="utf-8")
        spec.update({"source_sha256": hashlib.sha256((stage / "data.csv").read_bytes()).hexdigest(),
                     "authoring_sha256": hashlib.sha256(recipe.encode()).hexdigest(),
                     "matplotlib_version": matplotlib.__version__, "rows": len(ys),
                     "aggregation": "none", "scientific_verification": False, "visual_review": "required"})
        (stage / "provenance.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        stage.rename(out)
    return {"status": "rendered", "rows": len(ys), "visual_review": "required", "files": ["figure.svg", "figure.pdf", "figure.py", "data.csv", "provenance.json"]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path.cwd()); p.add_argument("--paper-repo")
    p.add_argument("--csv", type=Path, required=True); p.add_argument("--out", required=True)
    for k in ("x", "y", "xlabel", "ylabel"): p.add_argument("--"+k, required=True)
    p.add_argument("--kind", choices=["line","bar","scatter"], default="line")
    p.add_argument("--error"); p.add_argument("--error-meaning")
    a=p.parse_args()
    try:
        repo=paper_repo(a.root,a.paper_repo)
        out=local(repo,a.out)
        if out.relative_to(repo).parts[0] != "figures": raise ValueError("Place generated figures under figures/")
        result=render(a.csv.resolve(),out,x=a.x,y=a.y,xlabel=a.xlabel,ylabel=a.ylabel,kind=a.kind,error=a.error,error_meaning=a.error_meaning)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except ImportError:
        print("matplotlib is not installed; install it in your chosen local environment first",file=sys.stderr);return 2
    except (ValueError,OSError) as exc:
        print(str(exc),file=sys.stderr);return 2

if __name__ == "__main__":
    raise SystemExit(main())
