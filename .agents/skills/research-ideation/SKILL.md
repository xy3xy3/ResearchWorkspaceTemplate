---
name: research-ideation
description: "辅助发散生成、去重、质疑和筛选科研 idea；把文献缺口变成机制假设、反证条件和最小实验。"
---

# Evidence-led ideation

Use this skill both for a broad initial direction and to rescue a stalled hypothesis. It is a reasoning workflow, not a script that manufactures research claims. Read the brief, relevant specs, closest papers, past failed ideas, and actual compute/data limits. Reuse existing evidence instead of repeating a full survey.

## Separate generation from judgement

First build a short landscape: what is established, what is uncertain, which assumptions are shared, and which failures are repeatedly observed. A future-work sentence is a search seed, not a proven research gap. Label unsupported observations explicitly.

For a broad search, use up to three native read-only `idea_generator`/`literature_researcher` workers with different lenses. Good lenses include mechanism or assumption failure; measurement/data mismatch; transferring a verified mechanism to a genuinely different setting; and contradictory evidence. Use fewer workers for a narrow request. Workers propose candidates but do not reject other workers' candidates or write shared files.

Each candidate returns: question; proposed mechanism; closest real work and source locator; difference; predicted observation; plausible alternative explanation; falsifying observation; smallest discriminating test; resource/data needs; and a deduplication key based on mechanism plus test. Use `references/candidate-card.md`. Parent merges genuinely equivalent mechanisms while retaining distinct tests and provenance. Cosmetic names are not distinct ideas.

## Converge through evidence

1. Check the most plausible candidates against nearest work and actual source code using `research-literature`. Search for disconfirming work as well as supportive work.
2. Have a fresh `evidence_reviewer` challenge circular evaluation, hidden assumptions, infeasible data, and whether the proposed test distinguishes mechanisms. Do not preload the desired winner. Same-family criticism remains provisional.
3. Compare candidates on evidence-grounded novelty, importance, testability, and local feasibility. Avoid arbitrary composite scores and promises of acceptance. A small table with reasons is enough; unresolved fields remain unknown.
4. Select one primary hypothesis and at most one reserve unless the human asked for breadth. Use `references/hypothesis-template.md` for the chosen hypothesis. Record why alternatives were deferred, not only the winner.
5. Pass a concrete minimal control/ablation plan to `research-experiment`, within the existing approved budget. No cloud GPU, new paid API, dependency overhaul, or larger experiment without permission. A negative pilot is useful evidence, not a drafting inconvenience.
6. Update the idea card with keep/revise/abandon and links to actual observations. Do not call an idea validated merely because several model workers agreed.

A blocked experiment need not block theoretical comparison or source reading. State exactly which prediction remains untested. User-facing output is a few defensible candidates and the next discriminating test, not dozens of nearly identical ideas.

## Communication

User-facing output: concise, natural Chinese; give the result, decisive evidence, and material limitation. On first use, append a Chinese gloss to a specialized English term, e.g. `ablation（消融实验）`. Keep complete sentences, negation, units, exact identifiers, and uncertainty. Do not abbreviate words artificially, narrate every tool call, or repeat a long report in chat. Give brief updates for long tasks. Code, literal API fields, quotations, and English manuscripts keep their required language; do not inject Chinese glosses into them. Shorter output must not mean shallower research.
