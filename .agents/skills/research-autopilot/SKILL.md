---
name: research-autopilot
description: "用 Codex 原生子智能体持续推进调研、idea、实验与论文；从检查点恢复，不运行脚本式 Codex 驱动器。"
---

# Native research orchestration

Read `research/brief.md`, `spec/`, the local repository registry, active tasks, and the latest relevant evidence. Enter at the actual research stage. Use the smallest next action that can change a decision; do not restart the whole pipeline. Load specialist skills only when needed.

## Native execution contract

The current Codex parent owns orchestration. Use the host's actual native subagent tools (commonly `spawn_agent`, `send_input`, and waiting/closing tools); inspect their exposed schema rather than copying an invented call signature. Select a registered role from `.codex/agents/`. Do not launch `codex exec`, another Codex CLI, SDK session, MCP-to-Codex bridge, or a Python model driver. `scripts/loop.py` is a migration notice, not a fallback.

Delegate only independent deliverables, normally 1–3 at a time. Each brief contains the question, exact input paths, known facts, allowed files, constraints, output format, and stopping condition. Workers do not spawn workers. Do not dispatch the same search twice; reuse a worker for related follow-up. Close completed workers. While waiting, do independent integration work rather than repeated polling.

Fast extraction uses `quick_scan`; synthesis uses `literature_researcher`; cross-file reasoning uses `code_explorer`; difficult ideation uses `idea_generator`; implementation uses `experiment_implementer`; scoped tests use `verifier`; manuscript edits use `manuscript_writer`. `evidence_reviewer` reads original artifacts without the author's preferred interpretation. Model choices and escalation rules: `references/native-agents.md`.

Use native tools only when actually available. Otherwise continue suitable work in the parent sequentially, label independent review unavailable, and never invent an agent identity or create another model process to hide the limitation.

## One research cycle

1. Restore the question, prior decisions, abandoned candidates, budget, and unresolved evidence. Reconcile local files before repeating work.
2. Retrieve primary sources through `research-literature`; use `research-paper-prep` only when local full text or reference code is needed.
3. Generate or revise falsifiable alternatives with `research-ideation`. Deduplicate mechanisms, not just titles. Choose a discriminating test, not merely the idea most likely to score well in a model review.
4. Plan and run bounded local experiments through `research-experiment`. A worker may edit only allocated files in the registered independent code repository. Preserve unsuccessful runs.
5. Analyze results, then obtain a fresh evidence review. Same-family review remains same-family review, regardless of model names or reasoning strength.
6. Parent records keep/revise/abandon, evidence paths, and the next action. Use `research-writing` for a stage report and `research-latex` / `research-figures` only when manuscript work is in scope.

Routine reversible choices inside approved constraints do not need a new human confirmation. Stop on exhausted budget, changed research scope, new costs/dependencies/data permissions, missing essential resources, repeated non-progress, or `.runtime/STOP`. Silence is not authorization. Do not redefine a failed hypothesis to claim success.

## Durable checkpoints, not a model runtime

```bash
python3 .agents/skills/research-autopilot/scripts/checkpoint.py start
python3 .agents/skills/research-autopilot/scripts/checkpoint.py check N-<actual-id>
python3 .agents/skills/research-autopilot/scripts/checkpoint.py record N-<actual-id> \
  --status continue --summary '已核对最接近的方法，发现一个可测试差异' \
  --evidence research/literature/nearest-work.md --next-action '设计该差异的最小对照'
```

Run `check` before dispatch and before an expensive step. Only the parent writes this state. `record --status complete` also requires `--review <existing-review.md>`. Optional `--agents` is a JSON array with actual `role`, `agent_id`, and `model`; omit it when unavailable. The helper validates file existence/hashes, not scientific truth or identity authenticity.

The new `N-` state stores the frozen brief/spec and original budget. It never reads legacy `C-` state as native state. Read old evidence and create a linked new task deliberately. Elapsed wall time includes idle time across resumes; restart does not reset an existing checkpoint. A changed contract or expired budget requires human reconciliation, not automatic re-initialization.

Native-session time limits are cooperative checks, not preemptive process cancellation. The parent also respects `round_seconds`; the existing experiment runner enforces its own subprocess deadline. Checkpoints cannot restart a closed Codex session or promise unattended background work.

## Communication

User-facing output: concise, natural Chinese; give the result, decisive evidence, and material limitation. On first use, append a Chinese gloss to a specialized English term, e.g. `ablation（消融实验）`. Keep complete sentences, negation, units, exact identifiers, and uncertainty. Do not abbreviate words artificially, narrate every tool call, or repeat a long report in chat. Give brief updates for long tasks. Code, literal API fields, quotations, and English manuscripts keep their required language; do not inject Chinese glosses into them. Shorter output must not mean shallower research.
