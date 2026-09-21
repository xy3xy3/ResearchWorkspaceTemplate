---
name: research-autopilot
description: "从人类初步科研方向持续推进调研、假设、实验、分析与修正；支持交互式 Codex 和有预算的本地循环，不用于单次简单问答。"
---

# 自主研究编排

首先读取人类方向、`research/brief.md`、`spec/`、`workspace.local.json` 和现有研究记录。
本 skill 编排本包的 research-workspace / literature / ideation / experiment / review / writing；
只在需要时加载相关 skill，不要求每次先加载全部家族文档。不依赖外部 hooks、MCP 桥或全局 ARIS 安装。

## 一轮研究

恢复当前问题和未决证据，选择能改变判断的最小下一步：检索原始来源 → 形成/修正可证伪假设 →
设计判别实验 → 在独立代码仓库实现并运行本地实验 → 分析证据 → 独立审查 → 决策。
允许从任意已有阶段切入；证据不足时回到对应环节，不机械从头重跑。
维护 task 的执行状态；长期事实、idea、反证、判断写入 research。
默认在已授权范围内自动选择下一步并继续，不把每个阶段变成人类确认关卡。
权限、预算、研究方向或不可逆外部动作超出约束时才停止；不要把“没有回复”当作授权。

## 两种运行方式

交互式：用户在 Codex 中输入 `$research-autopilot 初步方向...`。在当前会话推进，按需要派发
原生自定义 subagent。主 agent 执行预算规则；提示词本身不是硬超时保障。

脚本式：用户从本机终端运行以下驱动。它使用新的 `codex exec` 执行会话与单独只读审查会话，
每次都从文件恢复，不靠同一无限增长的上下文。默认仅 dry-run，`--execute` 才真正调用模型。

```bash
python3 .agents/skills/research-autopilot/scripts/loop.py
python3 .agents/skills/research-autopilot/scripts/loop.py --execute --max-rounds 3
python3 .agents/skills/research-autopilot/scripts/loop.py --execute --resume C-...
```

脚本从当前 skill 的 references/ 读取输出 schema，从 scripts/ 读取全部程序。
驱动调用中的 agent **不得再次启动 loop.py**；只完成一轮所需工作。
缺 Codex CLI、登录、数据或所需能力时标记 blocked/error；不假装调用成功。
脚本执行在前台。`touch .runtime/STOP` 可停止当前及后续子进程；显式删除 STOP 后才可恢复。

## 预算、恢复和审查

`spec/autonomy.json` 限制轮数、累计墙钟时间、单轮时间、无进展和修改次数。
恢复沿用原预算；异常中断的轮次按完整预留时间计费，避免重启重置额度。
这不是 GPU 利用率/费用计量，也不能阻止不受信任程序自行脱离进程组。
修改 brief/spec/机器注册后，旧循环不可直接恢复；需要新的明确授权循环。

独立审查只收到目标文件路径与原始约束，不预装执行者结论。同为 Codex 不宣称跨模型独立验证。
proceed 仅允许流程前进，不等于科学真理、实验复现或投稿录用。
新文件和哈希只是结构检查；审查必须判断实际信息增益。达到预算可正常阶段性收尾，不强造正结果。
