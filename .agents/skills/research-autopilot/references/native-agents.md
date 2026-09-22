# Native role selection

| Work | Role | Model | Effort | Default access |
|---|---|---|---|---|
| Explicit fact extraction | quick_scan | gpt-5.6-luna | low | read-only |
| Literature synthesis | literature_researcher | gpt-5.6-terra | medium | read-only |
| Cross-module exploration | code_explorer | gpt-5.6-terra | high | read-only |
| Difficult hypothesis generation | idea_generator | gpt-6-astra | high | read-only |
| Scoped implementation | experiment_implementer | gpt-5.6-terra | high | workspace-write |
| Scoped local verification | verifier | gpt-5.6-terra | medium | workspace-write |
| Independent evidence review | evidence_reviewer | gpt-6-astra | high | read-only |
| Manuscript drafting/revision | manuscript_writer | gpt-5.6-terra | high | workspace-write |

These choices adapt the user's ResearchTemplate profiles; they are not measured latency/cost rankings or a guarantee of account access. Main-agent settings remain unchanged. Increase depth only for a concrete unresolved problem; do not assign maximum effort to trivial extraction. Large data does not automatically imply hard reasoning: split bounded extraction before escalation.

A role file's model/effort can take precedence over spawn-time overrides. Edit the role configuration deliberately if a different model is required; do not claim a runtime override succeeded without evidence. Missing model access is a configuration issue: report it and use an explicitly approved available role/model, never silently substitute and record the requested identity as the actual one.

Use the native tool schema exposed by the installed Codex version. No sample JSON here claims a universal spawn signature. Read-only defaults express intended role boundaries; actual inherited sandbox/approval restrictions still govern. Write-capable workers need explicit file ownership and independently granted access to external sibling repositories.

A small single-file task can stay with the parent. Multiple workers are justified by independent deliverables, not by the presence of role files. None of these roles may create grandchildren or launch a second Codex runtime.
