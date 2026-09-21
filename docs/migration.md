# 从旧工作区迁移

这是手工审查指导，不会自动遍历或修改你原来的科研仓库。先分别备份工作区 Git 与代码 Git，再迁移。

| 原位置/习惯 | 新位置/处理 |
|---|---|
| `.project/tasks/<date-slug>/task.md` | 按真实状态放 `task/active` 或 `task/archive`；生成稳定 ID 和 meta.json |
| `.project/journal.md` 或个人 journal | 原文作为历史附件保留；关键科学判断抽取到 research/decisions；工程进度关联 task |
| `.project/specs/*.md` | 经人工确认后移入 spec/；不能顺便放宽研究约束 |
| note 中的调研/想法 | 分到 research/literature、questions、ideas、findings；未经实验证实的内容不能标为 finding |
| 独立的 SceneGen/、src/ 等代码 repo | 保留其独立历史；登记为相邻目录，或移动到忽略的 repos/ 下 |
| ref、refrepo | 保留元数据和定位；克隆和 PDF 仍忽略 |
| 原外部 skills/hook 安装 | 逐项解除旧入口，避免新旧编排同时写任务状态；不要批量删用户全局配置 |

先迁移正在推进的一条研究主线，检查可恢复性，再搬历史。completed 的旧任务没有证据时明确标出“历史记录，未重新验证”，不能由迁移脚本伪造验证事件。需要继续的归档问题建立新任务并链接旧任务，不改写当时结论。

新模板不保留旧项目特定研究内容、人员信息、私有仓库代码、模型密钥或机器路径。该 PR 只创建通用工作流，不代表已经迁移旧仓库的任何进展。
