---
name: research-literature
description: "检索与去重论文、阅读原始方法、核验引用和检查参考代码；合并文献检索/监测/新颖性线索，不负责把线索认定为已证实创新。"
---

# 文献与代码证据

输入研究问题、时间范围和检索限制；输出 `research/literature/` 的检索记录与综合报告、
`ref/catalog.json` 的标识目录，以及 `ref/<paper-id>/paper.md` 的阅读笔记。
下载的 PDF 与 cloned repo 默认不进入工作区 Git；元数据、来源、阅读范围和代码定位可追踪。

```bash
python3 .agents/skills/research-literature/scripts/search.py --query "embodied scene generation" --limit 10
python3 .agents/skills/research-literature/scripts/search.py --query "task-driven scene" --provider semanticscholar
python3 .agents/skills/research-literature/scripts/search.py --import-file /path/to/metadata.json
```

检索脚本支持 arXiv、Crossref 和可选 Semantic Scholar；每来源上限 50 条、有限重试与超时，
不假装系统综述已穷尽全量。API 不可达时保留失败记录；用 Codex 可用搜索工具/人工资料补充，并标注途径。
只通过进程环境 → 当前 skill/.env → 项目 .env 读取 `SEMANTIC_SCHOLAR_API_KEY`，不打印它。
导入数据必须是有 title 的 JSON 数组；导入并不等于在线核验。

按 DOI、arXiv 去版本标识、Semantic Scholar ID 合并；无标识才用规范化标题兜底。
不要按相似标题武断合并不同论文，也不要把预印本与正式版的差异抹掉。内容冲突写进报告。

元数据仅证明检索到了某条记录。方法/结果主张必须读原文，记录页码/章节/公式；
代码主张必须查看实际文件、函数、commit 和运行入口。模型总结不得替代这些来源。
参考代码放 refrepo/<name> 或 ref/<id>/repo；仅从已核对来源 clone，先读再执行，不自动运行第三方安装脚本。
记录 repo URL、commit、许可证和本地定位，不将参考代码复制进工作区主仓库。

对近期相近工作，报告共同点、可核验差异与不确定性；“没搜到”不是新颖性证明。
多轮复用目录及检索日期，仅增量查询新线索，不重复下载、重复完整阅读或制造冗余报告。
