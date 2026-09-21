# ResearchWorkspaceTemplate

Codex 专用、本地实验优先的科研工作区。人类给出方向和资源边界，Codex 在边界内完成文献检索、可证伪假设、实现与实验、结果分析、独立复核和下一轮选择。它不是新的 Agent 平台，也不是必须安装外部 hooks 的工具集合。

## 仓库边界

```text
ResearchWorkspace/                    # 本仓库：研究记录与协作协议
├── AGENTS.md
├── .agents/skills/                    # 7 个去重后的技能；脚本/模板随技能分发
├── .codex/agents/                     # Codex 原生 subagent 定义
├── research/                         # 问题、文献、idea、实验收据、发现、决策、复核
├── task/active/                      # planned / running / blocked
├── task/archive/                     # completed / abandoned，不覆盖历史
├── spec/                             # 人类确认的约束与预算
├── ref/                              # 文献目录、定位信息、阅读笔记
├── repos/implementation/             # 独立代码 Git 仓库，外层忽略
├── paper/                            # 未来独立 LaTeX Git 仓库，外层忽略
├── refrepo/                          # 参考实现 clone，外层忽略
├── .runtime/                         # 本地日志、原始指标、锁、临时输出，忽略
└── workspace.local.json              # 本机路径登记，忽略
```

**`task/` 不加入 gitignore。** 忽略的是独立代码仓库、论文仓库和本地运行产物；任务、决策和科研报告应随工作区版本化。也支持代码仓库放在相邻目录。工作区不替代码仓库 commit、push 或维护 submodule。

## 开始

需要 Python 3.11+、Git，以及已经安装和登录的 Codex CLI；实验驱动支持 Linux、macOS 和 WSL。Python 工具仅使用标准库。模型和推理强度继承你的 Codex 配置，不固定模型名称。

```bash
# 在克隆下来的工作区根目录执行。该路径应指向你另行克隆的独立 Git 仓库。
python3 .agents/skills/research-workspace/scripts/workspace.py init \
  --direction '研究一个可测量的问题；描述现有方法、可用数据与计算资源' \
  --code-repo repos/implementation
python3 .agents/skills/research-workspace/scripts/workspace.py doctor
```

登记不会下载代码或安装依赖。没有代码仓库时仍可先调研，开始实验前需要独立仓库已有提交。编辑 `research/brief.md` 和 `spec/`，写清数据许可、指标、对照、资源预算、不可改动项。项目级 Codex 配置在项目被信任后生效；始终从**工作区根目录**启动 Codex。

交互运行：在 Codex 中输入：

```text
$research-autopilot 根据 research/brief.md 开始研究，在 spec 的预算内连续推进。
先检查已有证据和 active 任务。能自主决定的继续做；遇到权限、预算、数据缺失或重大方向变更再停下。
不要将 smoke test 当成科学证据。结束时落盘下一步和阻塞原因。
```

需要在自己机器上由脚本驱动多轮独立 Codex 会话时：

```bash
# 默认只检查配置，不执行 Codex
python3 .agents/skills/research-autopilot/scripts/loop.py
# 明确开始前台执行；每轮后启动新的只读 Codex 会话复核
python3 .agents/skills/research-autopilot/scripts/loop.py --execute
# 恢复时使用上次输出的实际 cycle ID，不重置原预算
python3 .agents/skills/research-autopilot/scripts/loop.py --execute --resume C-xxxxxxxxxxxx
```

驱动器不是守护服务，关掉进程不会自行继续。`touch .runtime/STOP` 请求停止；恢复前人工删除该文件。默认最多 6 轮、总计 7200 秒、单轮 1200 秒；一份实验计划的全部 seeds 最多 600 秒，连续两轮无进展或两次修订停下。硬时间限制由脚本模式执行；纯交互模式由主 Agent 遵守相同协议。预算只约束本地墙钟时间和轮数，**不是 API 费用、显存、网络或完整 OS 安全沙箱**。

## 技能职责

| Skill | 合并后的职责 | 内置程序 |
|---|---|---|
| `research-workspace` | 初始化、任务活动/归档、决策留痕、上下文恢复 | `workspace.py` |
| `research-autopilot` | 根据证据选择下一步；预算与恢复；执行/复核循环 | `loop.py`、输出 schema |
| `research-literature` | 检索、去重、阅读定位、相关工作与新颖性核对 | `search.py`，arXiv/Crossref/Semantic Scholar |
| `research-ideation` | 将方向变成可证伪假设、最小对照与淘汰标准 | 假设模板，不伪装成自动科学判断脚本 |
| `research-experiment` | 实验设计、实现交接、本地运行、配对分析 | `run.py`、`analyze.py`、合成 smoke 示例 |
| `research-review` | 冷启动复核、claim–evidence 检查、诚信审计 | `audit.py`，结构检查不等于科学证明 |
| `research-writing` | 调研/阶段报告、论证整理、未来 LaTeX 交接 | 报告模板 |

不会为一次小任务强制加载所有技能；也不复制上游的 Claude hooks、全家桶安装器、跨模型 MCP 桥、云 GPU 或发布流程。编排技能依赖已安装的专用技能；每个执行技能自己的脚本依赖都在它的目录内，没有 `~/other-repo/tools` 回退。

## 密钥与网络

每个声明的变量按 **进程环境 > 当前 skill/.env > 工作区根 .env** 解析。值按字面解析，不运行 `source`，不进行 `${VAR}` 展开；进程中的空值也优先。只传入工具明确声明的变量，禁止用 `.env` 覆盖 PATH 等运行时路径。未声明的常见敏感环境变量不会传给子进程。

Codex 可复用已有登录；只有采用 API key 认证时才需要相应 key。文献 helper 的可选 key 是 `SEMANTIC_SCHOLAR_API_KEY`；arXiv 和 Crossref 路线无需该 key。复制 `.env.example` 到 `.env` 后按需填入，绝不提交真实密钥。已知密钥在运行日志和模型最终 JSON 中脱敏，但不能保证识别任意秘密，commit 前仍需检查。

Codex 沙箱内调用外部文献 API 可能需要网络许可；内置 web search 与 Python 网络权限不同。默认配置不开放 shell 网络，也不绕过审批。网络不可用时记录缺口或导入已有元数据，不能用模型记忆伪造在线检索。

## 实验与证据

计划使用 argv 数组、固定 code commit、seeds、数据版本/划分、对照组和指标方向。每次生成新的输出目录；退出码成功且指标为有限数值才算执行成功。代码脏状态默认拒绝；仅 smoke/pilot 可显式 `--allow-dirty`，confirmatory 必须干净。实验期间代码改变会标成 tainted，不能作为正常证据。

`assets/toy_experiment.py` 是可真实执行的合成回归 **smoke fixture**，不代表你的项目结果。脚本模式不自动把示例改为科研实验证据；真实数据、依赖与 GPU 配置在独立代码仓库内定义。实操步骤见 [实验技能](.agents/skills/research-experiment/SKILL.md)。

文献存在不意味着它支持某个论断；成功退出不意味着方法正确；同模型新会话审查不意味着跨模型独立验证。负结果保留，无法验证的声明保持 unknown，不把 review 的 proceed 写成“科研成功”。

## 文档与测试

- [架构与权威记录](docs/architecture.md)，[旧工作区迁移](docs/migration.md)。
- [上游取舍与文件级来源](docs/upstream-map.md)，[Codex 配置与验证边界](docs/codex-compatibility.md)。

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q .agents tests
```

测试使用临时独立 Git 仓库、真正的本地子进程和合成数据；API 与 Codex 协议使用 mock，不要求模型账户或 GPU。通过这些测试不等于已经通过真实 Codex / 科研 GPU 端到端验证。
