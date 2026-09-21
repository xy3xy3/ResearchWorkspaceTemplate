# 活动与归档

`active/<id>/meta.json` 保存 planned/running/blocked 状态、决策和验证事件；`task.md` 保存目标边界、实现计划、验证记录、结论交接。避免在多个文件手工维护同一状态。

使用 research-workspace 的 `task-new`、`task-event`、`task-close`。completed 必须链接非空的已存在证据；abandoned 需要明确原因。两者移动到 `archive/<id>/`。归档不代表假设成立，也不删除原研究报告；后续追问创建关联任务，不修改旧记录。

该目录随工作区 Git 保存，**不忽略**。异步并行 Agent 不要共同改一个 meta.json；由主 Agent 统一调用命令落盘。移动前后都可从任务 ID 找到同一任务，引用研究证据尽量指向 research/ 的稳定文件，而不是会移动的任务路径。
