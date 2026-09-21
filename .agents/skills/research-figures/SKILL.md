---
name: research-figures
description: "基于真实数据制作可复现论文图表与可编辑方法图，保留数据、源码和来源；支持 SVG/PDF 与 LaTeX 集成。"
---

# Scientific figures with editable sources

Read `references/figure-workflow.md`. Separate quantitative plots from conceptual method diagrams. Establish the scientific message, data/topology, final publication size, labels, uncertainty semantics, and destination before drawing. Figures belong to the independent paper repository, not the literature cache `ref/`.

## Quantitative plots

Use verified experiment analysis outputs or explicitly supplied data. Check units, metric direction, seeds, failed/missing runs, aggregation rules, and what error bars represent. Never read numerical values off an imagined plot or use synthetic examples as paper results. Do not compute significance from a formatting request.

The bundled `scripts/plot.py` renders one series from CSV with explicit column/axis labels. It does not aggregate, interpolate missing values, or infer uncertainty. Optional error bars require `--error-meaning`. More complex plots use a task-specific reproducible script rather than forcing the simple helper beyond its scope.

```bash
python3 .agents/skills/research-figures/scripts/plot.py --paper-repo paper \
  --csv research/findings/verified-results.csv --out figures/main-comparison \
  --kind bar --x method --y score --xlabel Method --ylabel 'Success rate (%)'
```

The output folder contains `figure.svg`, `figure.pdf`, the exact `data.csv`, standalone `figure.py`, and `provenance.json` with hashes and library version. It refuses existing folders. Select a new evidence version or deliberately edit the existing canonical source; do not silently replace evidence. Requires local matplotlib, with no automatic installation. The emitted source can rerender with `python figure.py` inside the paper repository.

## Method diagrams

Begin with actual modules, representations, tensor/object flow, typed connections, and the method claim. Match visual grammar to the computation; do not turn every method into identical colored stage cards. Author a meaningful SVG or TikZ source with editable text/groups/connectors. Reuse an existing source for small changes.

When a requested conceptual illustration benefits from image generation and the host actually provides it, use that capability under its permission rules. Never invent an image backend, API key, or successful render. A raster placed inside SVG is not a fully editable vector diagram. Numerical charts remain code-generated even when illustrations are generated.

Inspect whole-figure balance and final-size readability, labels, topology, clipping, contrast, and error-bar meaning. For rendered publication PDFs, inspect the actual page as well. Record what was inspected; no silent visual-approval claim from a file-existence check. Integrate with `research-latex` using `\includegraphics` and a factual caption. Preserve full scientific terminology in the figure; user explanations use Chinese glosses on first English term use.

## Communication

User-facing output: concise, natural Chinese; give the result, decisive evidence, and material limitation. On first use, append a Chinese gloss to a specialized English term, e.g. `ablation（消融实验）`. Keep complete sentences, negation, units, exact identifiers, and uncertainty. Do not abbreviate words artificially, narrate every tool call, or repeat a long report in chat. Give brief updates for long tasks. Code, literal API fields, quotations, and English manuscripts keep their required language; do not inject Chinese glosses into them. Shorter output must not mean shallower research.
