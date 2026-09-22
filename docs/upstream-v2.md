# 第二版：来源与取舍

本次按用户给定仓库读取相关入口和技能片段，并非全仓库穷尽审计。下列 SHA 是所读文件的 blob SHA。新技能文字和脚本按目标架构重写，不整包安装外部 workspace，不复制私人研究成果或密钥。

| 来源文件 | 所读 blob SHA | 本次采用 |
|---|---|---|
| xy3xy3/ResearchTemplate: scripts/paper_retrieval/alphaxiv.py | fb41da45dbe4ff776c6256f416c1513ba122cf25 | MCP 握手、只读工具与字段；重写为同技能标准库传输，密钥不进入 curl 参数 |
| xy3xy3/ResearchTemplate: scripts/paper_retrieval/sciverse.py | 24c1b92e2621922844851622e4eb859552fd1d7b | 检索/content/schema/evidence 的明确子集；不宣称完整旧功能镜像 |
| xy3xy3/ResearchTemplate: scripts/parse_ref_papers.py（前 175 行） | d4fa0187c0c7fc880db6884a9ca0665f346a5193 | 解析文本归档思路；改为现有 MD 导入/显式本地 CLI，不搬入云解析包 |
| xy3xy3/ResearchTemplate: .codex/agents/quick_scan.toml | aa9f5c50bf2dcac589903edd712f81ef57413f37 | Luna/low 窄范围事实提取 |
| xy3xy3/ResearchTemplate: .codex/agents/default.toml | ad0fce4d0bf76b0ff197f78f760aa28bf7d77df4 | Terra/medium 综合检索 |
| xy3xy3/ResearchTemplate: .codex/agents/code_explorer.toml | 1602ca6c9a74c41d65ca30210f901c314306256a | Terra/high 调用链分析 |
| xy3xy3/ResearchTemplate: .codex/agents/verifier.toml | 721c9e147e491f778be313d07d6ac59559820485 | Terra/medium 限定验证 |
| xy3xy3/ResearchTemplate: .codex/agents/reviewer.toml | 2c9cb300fcbffe026a8a4d1304282f361409c6ad | Astra/high 独立审查；扩展困难 idea 角色 |
| mikubaka88/CCFA-Skills: ccf-paper-writer/SKILL.md | e4fc88279068056f3ecfa9828ca5c26369035f0d | 分模式写作、论证与证据对齐、保留现有 TeX、按范围复核 |
| mikubaka88/CCFA-Skills: ccf-visual-composer/SKILL.md | 4356f4844be17ce2e97c5a0999e9c9030ee6a9c3 | 数据图与机制图分离、可编辑源码、实际视觉检查 |
| wanshuiyin/Auto-claude-code-research-in-sleep: skills/skills-codex/idea-creator/SKILL.md（前 170 行） | c27ab50fab6e34cf3033a9ae2cc6b94d88ef054c | 按分析视角发散、主 Agent 去重、独立质疑、预算内 pilot |
| Imbad0202/academic-research-skills: academic-paper/SKILL.md（前 120 行） | bfa6dc2f2aa6d858a7c59ded855fb6116a8d0a78 | 大纲、论证、引用、正文、图表的职责拆分；只借鉴流程，不搬运 CC BY-NC 文本 |
| JuliusBrussee/caveman: skills/caveman/SKILL.md | 31b0c7c8a43cbfd1998d5406f5f56dfa17b8545d | 精简冗词、保留技术含义、清晰优先；不采用残句、删不确定性或完全禁止进度更新 |

文件定位：在各仓库 `blob/<branch>/<上表路径>` 查看；服务/角色源取自用户指定 master，外部技能源为 main。源码实现为本次重写，未复制上游图片、论文或完整模板。首版来源及许可证说明保留在 upstream-map.md；本次没有替仓库选择新的统一许可证。

去重结果：增强原 research-ideation，不再增加 idea-creator/optimizer/reviewer 同义家族；research-writing 专注报告，新增 research-latex 管正文与编译，research-figures 管绘图，research-paper-prep 管源材料。共 10 个技能。

明确舍弃：外部 hook、全局 ARIS 路径解析、Claude 兼容层、云 GPU、Codex CLI/SDK 编排桥、强制全家族预检、把模型评分当客观证据。英文技能正文用于明确任务协议，不宣称英文必然提高模型智能；用户交流仍遵循中文与首次术语释义规则。
