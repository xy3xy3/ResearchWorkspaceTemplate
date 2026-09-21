---
name: research-experiment
description: "在独立本地代码仓库执行有预算的实验并保存真实指标、失败、代码版本与配对分析；合并实验桥接、运行、结果分析，不做远程调度。"
---

# 本地实验与分析

脚本、运行库和演示资产都在当前 skill 内。需要 Python 3.11+、Git 和本地实验自身的依赖；
不安装云运行时，不依赖外部 tools/ 或 hooks。当前运行器支持 Linux/macOS/WSL。

## 计划与执行

复制 `assets/plan.example.json` 到 `research/experiments/<plan-id>.plan.json`，替换问题、假设、
代码完整 HEAD、数据版本/划分、基线、指标、种子、比较组、命令和预算。
代码必须在 workspace.local.json 注册的独立 Git 仓库；计划文件和运行记录属于工作区。

```bash
python3 .agents/skills/research-experiment/scripts/run.py --plan research/experiments/my-plan.plan.json
python3 .agents/skills/research-experiment/scripts/analyze.py --baseline research/experiments/E-baseline.json --candidate research/experiments/E-candidate.json --output research/findings/comparison.json
```

argv 是参数数组，不走 shell 拼接。`{seed}`、`{run_dir}` 会替换为本次值；
同时提供 `RW_SEED`、`RW_RUN_DIR`。实现必须把新指标写到 `$RW_RUN_DIR/metrics.json`，
不能复用代码目录中的旧 metrics.json。指标必须是 JSON 对象的有限数值，布尔值和 NaN 均拒绝。
新 run ID 和 seed 子目录避免旧输出被误读；一个工作区同时只运行一个实验计划。

运行器记录退出码、所有已尝试种子、预算终止、代码 HEAD/差异哈希、环境摘要和指标哈希。
成功要求全部计划种子完成且代码在运行中未变化；失败、超时和源代码变化不能变成 succeeded。
原始输出与补丁在 .runtime/，摘要在 research/experiments/。墙钟预算不是 GPU-hours 精确计费。
默认拒绝脏代码；smoke/pilot 可显式 `--allow-dirty`，记录补丁及未跟踪文件哈希，并标明恢复限制；
confirmatory 需要干净代码 commit。禁止为了过门禁执行 reset/clean 或删除用户修改。

只传递 plan.env_keys 显式列出的密钥，按进程环境 → skill/.env → 项目 .env 解析。
不要把密钥放 argv；PATH/HOME/加载器路径不能通过 .env allowlist 覆盖。
脚本不是不受信任代码的安全沙箱。先检查实验程序；不得自行脱离进程组、启动远程任务或改预算。

## 分析

只比较成功、非 smoke、比较组/数据/指标一致且种子相同的结果；保留所有失败种子说明。
输出候选减基线的差值，结合指标方向解释，不能一律把正值称作提升。
脚本给出描述性均值、标准差和可复现配对 bootstrap 区间；不足 3 个种子不出区间。
种子变异不等于数据总体不确定性，区间不是自动显著性结论。

`assets/toy_experiment.py` 仅用于端到端 smoke 演示，不是本项目的科研结果。
