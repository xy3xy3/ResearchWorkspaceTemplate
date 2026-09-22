---
name: research-latex
description: "在独立论文仓库中进行 LaTeX 论证规划、正文写作、修订、引用核对和本地编译；不虚构结果或投稿状态。"
---

# Evidence-bound LaTeX authoring

Read `references/writing-workflow.md`. Use the registered independent `paper_repo`, or an explicitly selected independent Git repository; never mix the manuscript into the workspace's research memory. Respect that repository's own instructions. Load only the relevant mode: outline, section draft, full draft, revision/rebuttal, compression, citation check, or build.

## Argument before prose

Establish the audience/venue and actual evidence. For each contribution, map claim, source locator or experiment receipt, uncertainty, and the section/figure that communicates it. Preserve research scope, numerical values, citation keys, definitions, mathematical symbols, and negative evidence. A draft may contain `TBD`/`DATA_NEEDED`; missing results are never filled with plausible numbers.

Plan the narrative around problem, closest prior work, insight, actual mechanism, distinguishing evidence, and bounded conclusion. Paragraphs have a scientific purpose, not a repeated defensive disclaimer. Explain real limitations where they affect interpretation. Learn organization from exemplars without copying sentences, results, or novel claims.

For a small edit, edit the existing source and inspect the affected claim/TeX context only. For a full paper, verify the requested venue's current official template, anonymity, page limits, and disclosure rules before claiming compliance. The bundled article is only a neutral drafting scaffold, not an accepted conference template. Do not silently select a venue.

## Native collaboration and delivery

Delegate scoped sections to `manuscript_writer` only with non-overlapping file ownership and a shared definitions/evidence map. Parent owns cross-section coherence and bibliography reconciliation. Use `research-figures` for data-backed plots and editable method diagrams. Have `evidence_reviewer` inspect changed claims independently; do not use a model's score as evidence of scientific correctness.

Write publication text in the requested manuscript language, normally academic English. Chinese summaries and first-use Chinese terminology glosses belong in user-facing reports, not automatically inside English manuscript prose, labels, equations, or BibTeX.

```bash
python3 .agents/skills/research-latex/scripts/latex.py --paper-repo paper init
python3 .agents/skills/research-latex/scripts/latex.py --paper-repo paper check
python3 .agents/skills/research-latex/scripts/latex.py --paper-repo paper build
python3 .agents/skills/research-latex/scripts/latex.py --paper-repo paper build --execute
```

The paper directory must already be its own Git repository and be ignored by the outer workspace. `init` refuses existing template files; it does not initialize Git or overwrite a paper. `check` is a limited static citation/reference check, not a TeX interpreter or source-faithfulness verifier. `build` plans by default; explicit execution uses installed `latexmk` with no rc files and no shell escape, a timeout, and ignored `.build/` outputs. This is not an OS sandbox for hostile TeX.

After a real build, inspect the PDF at final size: references, table/figure placement, clipped content, equations, and changed pages. Report unavailable engines or inspection tools honestly. A compiled PDF is not a scientifically verified or submission-ready paper. Save a short change/evidence summary in the workspace and keep paper source/history in the paper repository. No automatic push or submission.

## Communication

User-facing output: concise, natural Chinese; give the result, decisive evidence, and material limitation. On first use, append a Chinese gloss to a specialized English term, e.g. `ablation（消融实验）`. Keep complete sentences, negation, units, exact identifiers, and uncertainty. Do not abbreviate words artificially, narrate every tool call, or repeat a long report in chat. Give brief updates for long tasks. Code, literal API fields, quotations, and English manuscripts keep their required language; do not inject Chinese glosses into them. Shorter output must not mean shallower research.
