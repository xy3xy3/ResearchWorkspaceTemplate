---
name: research-review
description: "独立审查假设、实验、引用和报告证据，使用原生只读审查角色及结构审计，不把模型赞同当科学确认。"
---

# Independent evidence review

Use native `evidence_reviewer` on original artifact paths, the human brief/spec, and necessary code/data locators. Do not preload the author's preferred conclusion. No separate Codex subprocess/CLI review session. A different model within the same family is still same-family review. When independent tooling is unavailable, label the parent check as self-review.

```bash
python3 .agents/skills/research-review/scripts/audit.py
python3 .agents/skills/research-review/scripts/audit.py --output research/reviews/integrity-001.json
```

The bundled audit checks receipt structure, recorded hashes, raw metrics, seed coverage, and explicit evidence violations. PASS does not prove science; NOT_APPLICABLE means no relevant records; missing raw outputs may produce WARN, not a fabricated reproduction claim.

Scientific review examines goal alignment, citation support, closest competing work, implementation/mechanism correspondence, leakage, baseline and compute fairness, alternative explanations, missing/negative runs, uncertainty, and scope. Focus on findings that could change a decision. Do not manufacture a fixed number of risks or expand a small review into unrelated redesign.

Return proceed/revise/blocked with original evidence locations, actionable issues, and one useful next step. Proceed only permits further work within stated limits; it does not establish novelty, acceptance, or objective replication. Stay read-only and return to the parent; do not spawn workers or write your own acceptance record.

Parent may save the actual review with role/model/session information when available. `research/claims.json` supported entries need path/sha256/locator evidence. Structure checks and a stored review file cannot establish semantic support or authenticate a claimed reviewer identity; read the sources and state these limits.

## Communication

User-facing output: concise, natural Chinese; give the result, decisive evidence, and material limitation. On first use, append a Chinese gloss to a specialized English term, e.g. `ablation（消融实验）`. Keep complete sentences, negation, units, exact identifiers, and uncertainty. Do not abbreviate words artificially, narrate every tool call, or repeat a long report in chat. Give brief updates for long tasks. Code, literal API fields, quotations, and English manuscripts keep their required language; do not inject Chinese glosses into them. Shorter output must not mean shallower research.
