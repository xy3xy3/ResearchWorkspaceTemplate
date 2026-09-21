# Codex 兼容性与验证边界

配置依据 2026-09-21 查阅的 OpenAI 官方说明：

- [Agent skills](https://developers.openai.com/codex/skills)：项目 `.agents/skills/<name>/SKILL.md`，frontmatter 包含 name/description；scripts、references、assets 随技能存放。
- [Subagents](https://developers.openai.com/codex/subagents)：原生自定义角色在 `.codex/agents/*.toml`，必需 name、description、developer_instructions。**不是** `.agents/agents`；skill 的 `agents/openai.yaml` 也不是原生 subagent 定义。
- [Non-interactive mode](https://developers.openai.com/codex/noninteractive)：`codex exec --json --sandbox ... --output-schema ... -o ...`；默认认证继承本机登录，可按实际模式使用 CODEX_API_KEY。

不固定 CLI 版本、模型 ID 或高推理参数。当前项目配置使用 `[agents].enabled` 和 `max_concurrent_threads_per_session`；旧版本不认识时应升级或按其官方配置调整，不静默假装 subagent 已运行。项目配置需要信任项目后加载。执行器向登记的代码目录传 `--add-dir`；独立 reviewer 使用 read-only。

仅部署这些文件不自动授予网络、GPU、代码目录或写权限。`--execute` 是明确的本地运行开关，不包含 `--dangerously-bypass-approvals-and-sandbox`。非交互执行遇到审批需求可能阻塞/失败，超时后保留状态，由人类解决资源/审批条件，不绕过限制。

本实现的离线测试能验证 Python 逻辑、命令构造、schema/配置解析、预算/错误/恢复分支以及合成实验。生成环境没有安装 Codex CLI，也无法访问外网，因此真实 Codex 调用、在线文献 API 和实际科研 GPU 实验未验证。mock 通过不说明某个已安装 CLI 的版本一定兼容。先运行 doctor、dry-run，在自己的环境做一轮短预算验证，再增加预算。
