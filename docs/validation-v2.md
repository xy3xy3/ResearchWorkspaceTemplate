# 第二版验证记录

## 已实际执行

在生成环境的 Linux / Python 3.13 中：

```text
python -m unittest discover -s tests -p test_v2.py -v
Ran 44 tests
OK
python -m compileall -q .agents tests
通过
```

新增测试实际运行了临时文件/独立 Git 仓库、受控本地进程超时、Markdown 文本归档、忽略规则、检查点状态/预算与模板静态检查。Matplotlib 在该环境可用，已真实生成 SVG/PDF 和来源记录，并执行生成的独立 figure.py 重绘。这些图使用明确的合成测试数据，不是科研结果。

HTTP/MCP、alphaXiv/Sciverse 返回内容、本地 MinerU/PaddleOCR 解析输出和远端 clone 被模拟。克隆测试在模拟传输后创建真实临时 Git 仓库并核对 commit，但没有访问 GitHub 网络。测试覆盖密钥层级/空值/别名、认证跳转拒绝、错误脱敏、MCP 会话与分页、源文件不覆盖、临时产物清理、失败/预算/STOP 留痕、参考 URL/路径边界、TeX 静态检查及图表输入验证。

## 保留的首版回归

test_workflow.py 保留 24 项工作区、实验、文献与运行库回归契约，更新技能/角色数量；4 项只服务于已退役 Codex CLI 驱动器的模拟测试被删除，改由 test_v2.py 的原生检查点与无模型子进程测试覆盖。

当前生成环境重建的是变更文件集，不是可联网克隆的完整基线，所以不把这 24 项描述成本次已本地重跑。仓库现有 GitHub Actions 会在完整检出上执行全部测试和 Python 3.11/3.12/3.13 矩阵；以 PR 中实际检查结果为准。CI 未安装可选 matplotlib 时，真实绘图测试会明确 skip，而不是假称已渲染。

## 未验证与能力边界

没有真实在线 API、Codex 原生模型派发、模型账号可用性、GPU 论文解析或 latexmk 编译的端到端验证。TOML/命令/响应模拟通过不替代这些验证。PDF 生成测试不等于论文排版已视觉检查；引用结构检查不证明语义支持；检查点中的角色身份由主 Agent 报告，不是加密认证。

原生编排没有后台守护进程，也没有对模型调用的强制抢占。预算检查在主 Agent 执行检查点时生效；本地实验进程有独立超时。模板不自动安装依赖、不申请云资源、不推送独立代码或论文仓库。
