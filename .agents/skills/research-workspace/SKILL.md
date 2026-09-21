---
name: research-workspace
description: "管理科研工作区初始化、机器路径注册、任务进行中/归档、决策和验证记录；不替代科学判断。"
---

# 工作区与留痕

脚本入口为本 skill 的 `scripts/workspace.py`；运行时只依赖同目录 `runtime.py` 和 Python 标准库。
在工作区根目录启动 Codex，不要在嵌套代码仓库启动后假设父仓库 skills 会自动加载。
机器注册放 `workspace.local.json`，不提交；任务、约束和研究报告提交到工作区仓库。

## 操作

```bash
python3 .agents/skills/research-workspace/scripts/workspace.py init --direction "研究方向" --code-repo repos/implementation
python3 .agents/skills/research-workspace/scripts/workspace.py doctor
python3 .agents/skills/research-workspace/scripts/workspace.py task-new --title "核验最近邻方法" --question Q-...
python3 .agents/skills/research-workspace/scripts/workspace.py task-event T-... --kind decision --text "先查官方实现" --state running
python3 .agents/skills/research-workspace/scripts/workspace.py task-close T-... --outcome completed --summary "证据已整理" --evidence research/literature/report.md
python3 .agents/skills/research-workspace/scripts/workspace.py status --write
```

不在根目录运行时，把 `--root /absolute/workspace` 放在子命令前。
已存在的 brief 不会被 init 覆盖；修改方向需要显式编辑。init 不 clone、不安装依赖、不修改已有代码仓库。

## 记录规则

非平凡执行创建一个 task，不为每次工具调用创建任务。`meta.json` 是状态与事件权威记录；
`task.md` 记录范围、计划、验证和交接，不手工维护第二套状态。
进行中任务可为 planned/running/blocked；completed/abandoned 移入 archive。
归档任务不可修改；需要续做时创建关联旧 ID 的新任务。引用稳定 task ID，不依赖可移动目录路径。
完成必须附已存在的持久证据。任务完成不代表假设成立，失败实验也可完成一个验证任务。

通过 `note --kind question|idea|finding|decision --title ... --body ... [--task T-...] [--evidence ...]`
新增长期研究记录；finding 必须有证据。正文说明证据强度，不把“有文件”当作科学验证。
简单问答、单行修订不强制走留痕流程。STATUS.md 只是可重建视图，不是额外权威状态。
