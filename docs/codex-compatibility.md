# Codex 配置与兼容性

本次对照官方 Agent skills 与 Subagents 说明，以及用户 ResearchTemplate 的真实角色配置：
- https://developers.openai.com/codex/skills
- https://developers.openai.com/codex/subagents

技能放 `.agents/skills/<name>/SKILL.md`。原生角色放 `.codex/agents/*.toml`，包含 name、description、developer_instructions，并可设置 model、model_reasoning_effort、sandbox_mode。不是 `.agents/agents/`，也不是技能的 agents/openai.yaml。

项目配置使用 `[agents]` 的 enabled、max_concurrent_threads_per_session、default_subagent_model 和 default_subagent_reasoning_effort。项目需被信任才加载；实际已安装版本不支持时应核对对应官方文档，而不是声称文件存在就已生效。主 Agent 模型不固定。

角色文件中的模型/推理设置可能优先于派发参数；不要传一个覆盖值就假定切换成功。模型 ID 沿用用户配置，不保证当前账号或代理端点支持。模型不可用时报告实际错误，并由用户明确调整可用配置；不伪造执行模型。

默认不开放 shell 网络，不绕过审批。只读/可写角色仍受实际继承的会话沙箱约束，角色说明不提供额外 OS 隔离。相邻独立代码/论文仓库需要宿主明确授予访问范围。任务文件所有权仍由主 Agent 精确分配。

research-autopilot 仅走当前会话原生子智能体；loop.py 只返回迁移提示，不再调用 codex exec。checkpoint.py 不调用任何模型。缺原生能力时可以主 Agent 顺序完成适合工作，但独立审查不可冒充。

离线测试验证脚本、TOML、状态与协议分支，不验证当前账户实际原生派发、模型可用性、在线 API、真实 GPU 解析器或 TeX 环境。首次本地使用先检查配置和少量真实材料，再扩展范围。完整验证记录见 validation-v2.md。
