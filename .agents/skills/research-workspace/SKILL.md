---
name: research-workspace
description: "管理工作区初始化、机器路径、任务进行中和归档、决策与验证留痕，不替代科研判断。"
---

# Workspace memory

Start Codex at the workspace root. The independent implementation repository, paper repository, and reference clones are not the workspace. `workspace.local.json` stores local paths and stays ignored; `task/`, `research/`, and `spec/` are tracked. This skill uses its bundled `scripts/workspace.py` and `runtime.py`.

```bash
python3 .agents/skills/research-workspace/scripts/workspace.py init --direction '研究方向' --code-repo repos/implementation
python3 .agents/skills/research-workspace/scripts/workspace.py doctor
python3 .agents/skills/research-workspace/scripts/workspace.py task-new --title '核对最近邻方法' --question Q-example
python3 .agents/skills/research-workspace/scripts/workspace.py task-event T-actual --kind decision --text '先读官方实现' --state running
python3 .agents/skills/research-workspace/scripts/workspace.py task-close T-actual --outcome completed --summary '证据已整理' --evidence research/literature/report.md
python3 .agents/skills/research-workspace/scripts/workspace.py status --write
```

Use actual IDs and existing evidence. Outside the root, pass `--root /workspace` before the subcommand. Initialization does not clone code, install dependencies, or overwrite an existing brief.

Create one task for a meaningful deliverable, not each tool call. `meta.json` is the sole task state/event source; `task.md` contains scope, plan, validation, and handoff. Active states are planned/running/blocked; completed/abandoned tasks move to archive. Do not rewrite archives; create a new linked task. Reference stable IDs, not paths that change on archival.

Use `note --kind question|idea|finding|decision --title ... --body ... [--task ...] [--evidence ...]` for long-lived research memory. Findings require evidence, but file existence is not scientific confirmation. A completed verification task may legitimately refute its hypothesis. `research/STATUS.md` is a regenerated view, not a second source of truth. Simple questions and tiny edits need no task ceremony.

Native orchestration state belongs to the parent using `research-autopilot` checkpoints. This helper does not dispatch models. All scripts resolve declared secrets through process environment, then skill `.env`, then project `.env`; never print credentials or put them into journal text.

## Communication

User-facing output: concise, natural Chinese; give the result, decisive evidence, and material limitation. On first use, append a Chinese gloss to a specialized English term, e.g. `ablation（消融实验）`. Keep complete sentences, negation, units, exact identifiers, and uncertainty. Do not abbreviate words artificially, narrate every tool call, or repeat a long report in chat. Give brief updates for long tasks. Code, literal API fields, quotations, and English manuscripts keep their required language; do not inject Chinese glosses into them. Shorter output must not mean shallower research.
