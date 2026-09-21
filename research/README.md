# 科研记录，而非工程任务列表

`brief.md` 保存人类初始方向；初始化命令创建它，不覆盖已有文件。其余目录按研究语义组织：`questions/`、`ideas/`、`literature/`、`experiments/`、`findings/`、`decisions/`、`reviews/`、`cycles/`。

长期主线是问题 → 假设 → 证据 → 决策。工程执行任务在 `task/`，科研结论不要只藏在任务流水中。发现必须引用证据；失败也保存，不覆盖旧结果。实验 JSON 是可版本化的执行收据，完整 stdout/原始指标位于忽略的 `.runtime/`。

阶段报告可放在 `research/reports/`，按需创建；图表和论文由真实证据派生。每个结论说明事实、推断、未知与限制；来源包含文件/论文、版本和页码/段落/代码位置。`STATUS.md` 可由 workspace status --write 重建，不是第二份状态源。
