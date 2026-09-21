# ResearchWorkspaceTemplate

Codex 专用科研工作区。人类给方向和资源边界，主 Agent 用原生 subagent（子智能体）推进调研、idea、实验和论文；脚本负责实际工具操作，不负责启动其他 Codex 进程。

## 仓库布局

```text
.agents/skills/       10 个技能，脚本、参考协议和模板随包存放
.codex/agents/       8 个原生角色，含模型与推理强度
research/            问题、idea、证据、实验收据、决策、报告
task/active/        进行中任务（planned/running/blocked）
task/archive/       已完成或放弃任务，不覆盖历史
spec/                人类确认的约束与预算
ref/<id>/            paper.md、source.json、repo.txt、notes.md
repos/               独立代码仓库，外层忽略
paper/               独立论文仓库，外层忽略
refrepo/             参考实现克隆，外层忽略
.runtime/            临时解析、日志、原始指标，忽略
workspace.local.json 本机路径登记，忽略
```

`task/`、`research/`、`spec/` 和资料文本随工作区版本管理。代码、论文与参考仓库不复制进外层 Git；也支持相邻独立仓库。解析原文与阅读笔记分开，避免摘要覆盖原文。

## 开始

基础工具需要 Python 3.11+、Git；本地实验与检查点面向 Linux/macOS/WSL。实际研究在你已登录的 Codex 环境运行。主 Agent 模型保留你的配置，子角色配置见下表。

```bash
python3 .agents/skills/research-workspace/scripts/workspace.py init \
  --direction '研究问题、现有方法、可用数据与资源边界' --code-repo repos/implementation
python3 .agents/skills/research-workspace/scripts/workspace.py doctor
```

代码仓库应另行克隆并已有提交；登记不会下载代码或安装依赖。补全 `research/brief.md` 和 `spec/` 后，在工作区根目录的 Codex 中输入：

```text
$research-autopilot 根据 research/brief.md 推进研究。
优先用原生子智能体，复用已有证据和 active 任务；在已批准预算内继续。
遇到资源、权限、预算或重大方向变更时停下并保存下一步。
```

旧 `loop.py` 已停止执行模型，只返回迁移提示。不要再使用 `loop.py --execute`。新检查点保存原生会话状态，不是自动运行器：

```bash
python3 .agents/skills/research-autopilot/scripts/checkpoint.py start
python3 .agents/skills/research-autopilot/scripts/checkpoint.py check N-<实际编号>
```

主 Agent 在派发和昂贵步骤前检查预算，并记录证据与下一步。默认预算仍由 `spec/autonomy.json` 决定；检查点墙钟时间包括会话间的空闲时间，不在恢复时重置。旧 C- 状态不自动解释为新 N- 状态。原生会话预算是协作式检查，不能强制中断一个未返回的模型调用；本地实验运行器仍有独立超时。关闭 Codex 后不会自动继续。

## 模型分工

| 角色 | 模型 | 推理强度 |
|---|---|---|
| quick_scan | gpt-5.6-luna | low |
| literature_researcher、verifier | gpt-5.6-terra | medium |
| code_explorer、experiment_implementer、manuscript_writer | gpt-5.6-terra | high |
| idea_generator、evidence_reviewer | gpt-6-astra | high |

配置参考你的 ResearchTemplate，不是实测速度排名。通常只并行 1–3 个独立工作；简单任务主 Agent 直接完成。项目需被信任后加载配置，实际账号需有对应模型权限。模型不可用时明确处理，不假称调用成功；缺原生子智能体时可顺序推进适合的工作，但不以另起 Codex 进程补位。

## 技能

| Skill | 主要职责 |
|---|---|
| research-workspace | 初始化、任务 active/archive、决策和验证留痕 |
| research-autopilot | 原生委派、证据整合、预算和恢复 |
| research-literature | alphaXiv、Sciverse、arXiv、Crossref、Semantic Scholar 检索与来源核对 |
| research-paper-prep | 导入解析 Markdown、本地 PDF 解析、忽略目录中的参考仓库克隆 |
| research-ideation | 多视角候选生成、机制去重、反证和最小实验 |
| research-experiment | 本地实验、失败留痕、代码版本与配对分析 |
| research-review | 原生独立审查、引用支持与收据结构审计 |
| research-writing | 调研和阶段报告 |
| research-latex | 独立论文仓库中的大纲、写作、修订、引用检查、编译 |
| research-figures | 数据图、可编辑方法图、绘图源码与来源记录 |

技能使用英文工作流程与必要中文说明；面向用户默认简洁中文，专有英文术语首次出现带中文释义。精简不删除证据或不确定性；英文论文、代码和 API 字段不插入聊天式括注。无需额外安装 caveman 或其他工作区。

## 文献与本地资料

复制文献技能的 `.env.example` 到同级 `.env`，只填需要的服务密钥：`ALPHAXIV_API_TOKEN`（兼容 ALPHAXIV_API_KEY）、`SCIVERSE_API_TOKEN`、可选 `SEMANTIC_SCHOLAR_API_KEY`。顺序为进程环境 > 当前 skill/.env > 项目 .env；不通过 shell source 执行配置。

```bash
python3 .agents/skills/research-literature/scripts/alphaxiv.py tools
python3 .agents/skills/research-literature/scripts/sciverse.py semantic \
  --args '{"query":"functional scene generation","mode":"balanced"}'

python3 .agents/skills/research-paper-prep/scripts/prepare.py \
  --id paper-slug --source /local/parsed/paper.md --parser mineru \
  --source-url https://arxiv.org/abs/2601.01234 --repo-url https://github.com/owner/repository
python3 .agents/skills/research-paper-prep/scripts/clone_ref.py paper-slug --execute
```

将示例标识换成真实来源。优先导入已有 Markdown，避免重复 OCR（光学字符识别）；需要解析 PDF 时，显式 `--execute` 使用已安装的 MinerU 或 PaddleOCR。只发布文本和来源，删除自己的临时副本，不删除原文件。解析器可能首次下载模型权重，离线使用需提前配置；不自动安装或上传 PDF 到云解析 API。参考克隆默认仅计划，`--execute` 才克隆，不覆盖、不 pull/reset、不运行第三方代码。

文献客户端的网络权限和 Codex 内置搜索权限不同；默认配置不开放 shell 网络或绕过审批。外部服务会收到查询内容，私密材料外传要另获授权。返回的元数据/摘要不自动成为已核验的科学证据。

## LaTeX 与作图

先准备并登记一个独立 paper_repo；它不能是工作区本身。下面以已有独立 `paper/` 仓库为例：

```bash
python3 .agents/skills/research-latex/scripts/latex.py --paper-repo paper init
python3 .agents/skills/research-latex/scripts/latex.py --paper-repo paper check
python3 .agents/skills/research-latex/scripts/latex.py --paper-repo paper build --execute

python3 .agents/skills/research-figures/scripts/plot.py --paper-repo paper \
  --csv research/findings/verified-results.csv --out figures/main-comparison \
  --kind bar --x method --y score --xlabel Method --ylabel 'Success rate (%)'
```

`init` 不覆盖已有论文；内置的是通用 article，不是假定会议模板。实际编译需要本机 latexmk/TeX，绘图需要 matplotlib；均不自动安装。图表保存 SVG/PDF、数据、独立可运行绘图源码及来源哈希。资料库 ref/ 的不保留图片规则，不影响独立论文仓库中自己制作的图。

## 证据与验证边界

实验仍在独立本地代码仓库内运行，记录 commit、seeds、协议、有限数值指标、失败和代码漂移。烟测数据、模型打分、成功编译或多个模型赞同都不等于科学结论成立。同家族审查不冒充跨模型家族验证；静态引用检查不证明原文支持。

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q .agents tests
```

测试中的 HTTP、MCP（模型上下文协议）、解析器和模型调度协议使用模拟，不等于真实在线服务、本地 GPU 解析、Codex 原生委派或 LaTeX 端到端验证。具体执行记录见 [本次验证](docs/validation-v2.md)。

[架构](docs/architecture.md) · [Codex 兼容性](docs/codex-compatibility.md) · [迁移](docs/migration.md) · [本次上游参考与取舍](docs/upstream-v2.md) · [首版来源](docs/upstream-map.md)
