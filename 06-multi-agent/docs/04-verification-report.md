# 06 本地验证报告

## 环境与模型

| 项目 | 实测值 |
| --- | --- |
| OS | Windows / PowerShell |
| Python | 3.13.9 |
| LangChain / langchain-core | 1.4.2 / 1.6.4 |
| LangGraph | 1.2.12 |
| langchain-openai / pytest | 1.6.4 / 8.4.2 |
| Foundry Local CLI | 0.10.3；服务 Ready |
| 最终模型 | 已缓存 GPU `phi-4-mini`，运行时 ID `Phi-4-mini-instruct-generic-gpu:5`，Tools=支持 |
| 失败模型 | 已缓存 GPU `qwen3-4b`；见下方真实失败 |
| Endpoint | 本次运行发现 `http://127.0.0.1:53494/v1`；代码每次从 Foundry 查询动态 URL，不固定端口 |
| 云/真实医疗数据 | 无；仅 `resources/` 合成 JSON |

执行过 `foundry --version`、`foundry server status`、`foundry model list --cached`、`foundry model list --loaded`、`python --version`。Ollama 未安装；无需使用它。06 独立虚拟环境通过 `python -m venv .venv` 与 `uv pip install --python .venv\Scripts\python.exe -r requirements.txt` 建立。

## 命令与结果

在 `06-multi-agent` 目录，A–J 依次使用 `& .\.venv\Scripts\python.exe -u src\stage_<letter>_<name>.py` 实际运行。统一命令：

```powershell
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -u scripts\verify_all.py
```

| Stage | 关键实证 | 状态 |
| --- | --- | --- |
| A | 三个 Worker 均产生 AI tool_call、内部 ToolMessage 和最终答复 | PASS |
| B | record/guide/doctor/refuse 四类纯 Python 路由 | PASS |
| C | 对应 Worker/内部 Tool 实际执行；拒绝分支无 Worker 调用 | PASS |
| D | Graph stream 依次 router → record → aggregate | PASS |
| E | 高层工具只有三个 ask_*；底层工具仍执行 | PASS |
| F | 三条单域 Supervisor → Subagent Tool → Worker Tool → Supervisor final | PASS |
| G | 一个请求调用 Record 和 Doctor；最终包含两份合成数据 | PASS |
| G 并行 | 本地模型顺序调用两个工具；同轮并行未观察到 | OPTIONAL |
| H | Worker task 不含无关 canary；回传不含内部消息轨迹 | PASS |
| I | NO_DATA 与 DOCTOR_AGENT_ERROR 区分；跨域部分成功/失败均被报告 | PASS |
| J | 同请求对比：Router 单 worker；跨域 Supervisor 两 worker | PASS |

`pytest -q`：**20 passed**。`scripts/verify_all.py` 对 A–J 的真实本地执行、标记与测试全部通过，输出 **`06_MULTI_AGENT_PASS_LOCAL`**。没有用 mock 代替 E2E；mock 仅用于确定性单元测试。阻塞：无。最终状态：**PASS_LOCAL**。

## 实际失败与修复

1. `qwen3-4b` 在 Worker 首次运行把 tool-call 文本写进普通 AI 内容，`tool_calls=[]`。使用官方 `wrap_model_call` 设置首轮 `tool_choice=required` 后，它能产出结构化调用，但对有数据的 Record/Doctor 结果仍误报 `NO_DATA`。选用另一款已缓存的 tool-capable GPU 模型 `phi-4-mini`，没有下载或接入收费服务。
2. `phi-4-mini` 无强制约束时也曾直接回答、跳过工具。Worker middleware 首轮要求调用工具，已有 ToolMessage 后要求直接答复；验证检查 AIMessage、ToolMessage 和实际函数计数。
3. Doctor 的首次结果追加了无据 `NO_DATA`；去掉容易被模型回显的状态词提示。Supervisor 首次把指南查询扩写为不存在的键，目录请求还选错高层工具；修正本地关键词检索、明确高层工具职责，并在 wrapper 规范化 Worker 输入。
4. 跨域 Supervisor 初次虽调用了两个子 Agent，最终答复却遗漏记录；目录任务的 `general` 也被改写丢失。Wrapper 将任务规范化为本地数据键后，两份工具结果与最终答复均通过。
5. 模拟失败请求被 Supervisor 改写为 “simulate directory execution error”；任务规范化层识别这类明确模拟错误表达，底层 Doctor 工具实际抛出 RuntimeError，wrapper 输出 `DOCTOR_AGENT_ERROR: RuntimeError`，Supervisor 最终分别报告 Record 成功和 Doctor 失败。

Worker 的模型原始最终答复和 `ToolMessage` 都留在本地调用结果供验证；传给 Supervisor 的是从合成工具 JSON 生成的简洁 `filtered` 结果。这是本章的 Output Filtering 边界，防止模型附加无据内容。教程原文中的一次分类“supervisor”在实现里更名为 Router；真正 Supervisor 使用 `create_agent` 和高层工具。Handoff、持久化、HITL 与时间回溯保持在概念/后续章节边界。
