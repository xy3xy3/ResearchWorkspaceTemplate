---
name: research-review
description: "独立审查假设、实验和报告的科学证据，验证运行记录及引用定位；合并完整性核验与评审，保持只读，不替执行者自证。"
---

# 独立证据审查

输入仅为待审文件路径、原始方向/约束、必要代码/数据定位。直接阅读，不把执行者摘要当作证据。
原生 evidence_reviewer subagent 或脚本式单独 Codex 只读会话均可使用；同家族模型不是跨模型验证。

```bash
python3 .agents/skills/research-review/scripts/audit.py
python3 .agents/skills/research-review/scripts/audit.py --output research/reviews/integrity-001.json
```

脚本只检查记录结构、已记录哈希、原始指标一致性、种子覆盖和明显证据违规。
PASS 不是科学正确性证明；无可查记录返回 NOT_APPLICABLE；缺本地原始输出返回 WARN 而非假称复现。

人工/模型审查还必须检验：问题是否仍对齐人类目标，引用是否支持对应主张，最近邻方法是否真正比较，
实现是否对应宣称机制，数据划分是否泄漏，基线与预算是否公平，替代解释是否排除，
失败/负结果是否完整，smoke 或模型评分是否被冒充客观实验，误差和适用范围是否足够。
检查最重要的证据缺口，避免与目标无关的形式主义修补。

输出 proceed / revise / blocked，给出证据定位、关键问题和一个可执行下一步。
proceed 只表示在注明局限的前提下可继续，不表示录用或科学独立确认。
保持只读，返回主 agent 整合；不递归派发、不修改源文件、不自行给自己通过结论。

可选 research/claims.json 是数组；supported 条目需要 evidence 中的 path、sha256、locator。
脚本验证引用结构；语义支持仍需阅读与独立复核。未证实内容保持 hypothesis/inconclusive。
