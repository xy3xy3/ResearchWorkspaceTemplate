# 上游取舍与来源

核对日期：2026-09-21。以下是本次实际阅读的核心入口和设计文件，不是全仓库穷尽审计。脚本与技能说明为新写实现，不直接复制上游代码/长提示词。表中 SHA 是所读文件的 Git blob SHA，不是仓库 commit SHA。

| 来源 | 所读文件与 blob SHA | 提炼/合并到 | 不带入 |
|---|---|---|---|
| [academic-research-skills](https://github.com/Imbad0202/academic-research-skills) | `academic-pipeline/SKILL.md` `5d37b6d84b75e6a9ae6c1e3da1e1d4e62b4e79b6`；README、LICENSE | research-review/writing/autopilot：引用与论断分开核验、可恢复交接、复核后修订 | Claude 配置、共享 hook、每阶段强制人类确认、全投稿工具链 |
| [CCFA-Skills](https://github.com/mikubaka88/CCFA-Skills) | `ccf-experiment-designer/SKILL.md` `40966ae881bd0ae59d009c39e4abd3e28c10166a`；README、LICENSE | ideation/experiment/review：claim→最小充分对照→真实数值→独立判断 | 所有任务强制 humanization/common 前置；17 个角色整套照搬 |
| [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) | `skills/skills-codex/idea-discovery/SKILL.md` `f2a900c6371bbad4ccf77ff8d044e4f4ef08f56f` | autopilot/ideation：方向→调研→假设→小试验→复核，预算与失败退出 | 固定模型、跨模型必需依赖、云/远程 GPU、无限自动通过 |
| ARIS | `AGENT_GUIDE.md` `5a877c3a6d5dcfd419f40e647b37066be2bee72d`；Codex README `9aeec7b38e0ecc3277932d69bf3cbe8e94c1e843` | evidence receipts、同家族审查诚实标注、自包含 helper | `~/aris_repo` 链接、tools 多级外部查找、Claude MCP 桥与运行时 |
| [SceneGenWorkspace](https://github.com/xy3xy3/SceneGenWorkspace) | `AGENTS.md` `b094e9afae995089fed1d1ac4bd1dddca4e777b1`；`.gitignore` `60a5394885d8e6a214cbc2c50050d608444513a1` | workspace、原生 subagents：单一整合者、少量并行、实现/工作区分仓 | 特定研究结果/规格、机器细节、无界 task 流水 |
| [ResearchTemplate](https://github.com/xy3xy3/ResearchTemplate) | `AGENTS.md` `3c27146af221d5455481d4d0cffca0bc6dd8284e`；`.gitignore` `b5a5105a322d63abf9757fe3aea45b089b145695` | task 四类记录、稳定 spec、ref/refrepo 隔离 | 单一 task 同时承担科研结论与工程状态；外部环境依赖 |

## 去重规则

检索、文献监测、新颖性搜索统一到 literature（不额外常驻监控）；idea creator/reviewer/optimizer 的生成部分合并到 ideation，独立判断保留给 review；实验设计、bridge、run、分析进入 experiment，脚本分工但不重复技能入口；integrity/citation/result-to-claim 的核验合并到 review；paper/report/阶段总结合并到 writing。workspace 管留痕，autopilot 只协调缺失证据与下一步，不替 specialist 再写一套方法学。

## 许可处理

所读 ARS LICENSE 明确为 CC BY-NC 4.0（版权 Cheng-I Wu）；CCFA LICENSE 为 MIT（Chaoyue Li）；ARIS LICENSE 为 MIT（wanshuiyin）。本次没有把这些上游文件原样 vendor 到模板，也没有把 ARS 的非商业许可材料混入一个声称不受限制的合集。来源作为设计参考列出。未来若复制代码、模板或大段提示词，必须按届时对应许可保留声明并评估兼容性。

本 PR 不替仓库所有者决定整个新项目的发布许可证；目前不添加覆盖第三方材料的统一 LICENSE。需要对外再分发时由维护者明确授权范围。
