# Writing workflow

## Scope and sources

For a paragraph edit, preserve the manuscript's existing format and facts. For a whole paper, first create a compact outline with section purpose and claim/evidence links. The target venue is a human decision; verify current official format/anonymity/disclosure rules before submission claims. The bundled article is a drafting aid only.

## Section checks

Introduction explains a specific problem and real gap relative to closest work. Related work compares mechanisms/settings fairly, not a list of titles. Method defines the implemented mechanism, assumptions, notation, and reproducible details. Experiments describe real datasets/splits/baselines/metrics/budgets/seeds and separate pilot from confirmatory evidence. Discussion interprets supported effects, negative evidence, alternatives and meaningful limitations. Abstract and conclusion cannot be stronger than the experiments.

## Citation and number discipline

Verify existence/metadata and separately verify passage-level support. Preserve stable BibTeX keys and exact reported units. A DOI resolver does not prove the citation supports the sentence. Record missing sources outside the manuscript or use clear draft placeholders; do not manufacture entries. Tie all table/figure numbers to actual analysis artifacts. Avoid changing values during formatting.

## Figures and revisions

Use research-figures for authored source plus data/provenance. A caption states what was measured or what the diagram represents, not an unsupported causal claim. For a review response, map each real comment to the response, exact changed location, evidence, and unresolved point. Do not claim experiments were added when only prose changed.

## Build and inspection

The helper checks simple literal includes and common citation/reference forms. Macros, verbatim blocks, conditional compilation, graphicspath and bibliography packages may need actual compilation; static findings require context. It is not a full TeX parser. Compile with the user's trusted local toolchain, inspect changed PDF pages at publication scale, then fix concrete errors. No dependency installation, arbitrary latexmk rc execution, shell escape, automatic submission, or perpetual warning-chasing loop.

## Output language

English manuscript prose remains normal academic English. Concision removes empty framing, not reasoning or necessary uncertainty. Chinese user-facing summaries explain the change and first-use specialized English terms; do not put chat glosses into publication equations, identifiers, or exact quotations.
