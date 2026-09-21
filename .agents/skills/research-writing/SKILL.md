---
name: research-writing
description: "把调研、idea、实验、反证和决策整理为阶段报告；将论文正文与作图交给独立写作技能。"
---

# Research reports and manuscript handoff

Use `references/report-template.md`. Write to `research/` from actual materials: question, method, evidence, interpretation, limitations, and next step. Link implementation detail through stable task IDs rather than duplicating a task journal. Distinguish observed facts, inference, and hypothesis.

Check each substantive claim against the source passage or experiment record. Citations need more than a matching title; numbers come from analysis outputs, not manual embellishment. Keep negative results and the uncertainty that changes interpretation. Review-triggered edits must not silently strengthen claims.

A small prose edit needs no full multiagent pipeline. For a substantial report, use an independent native `evidence_reviewer` on raw artifacts and changed claims. Integrate actionable findings, then check affected text rather than repeatedly rewriting everything.

LaTeX source belongs to `research-latex`; quantitative plots and method diagrams belong to `research-figures`. Pass a compact claim/evidence map, verified bibliographic fields, figure data, and relevant versions. Without a registered paper repository, produce only a workspace writing plan/report. Do not create a mixed repository, submit a paper, or push code as a side effect.

## Communication

User-facing output: concise, natural Chinese; give the result, decisive evidence, and material limitation. On first use, append a Chinese gloss to a specialized English term, e.g. `ablation（消融实验）`. Keep complete sentences, negation, units, exact identifiers, and uncertainty. Do not abbreviate words artificially, narrate every tool call, or repeat a long report in chat. Give brief updates for long tasks. Code, literal API fields, quotations, and English manuscripts keep their required language; do not inject Chinese glosses into them. Shorter output must not mean shallower research.
