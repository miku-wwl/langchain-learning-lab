# 01 — LangChain E2E Learning & Verification Lab

以仓库根目录的 [LangChain v1.4 教程](../doc/01.LangChain_v1.4_架构解读与学习路线.md) 为学习范围，使用 LangChain 1.4.2 和本地 Foundry Local 模型，从 Model 一步步运行到 Agent Loop、短期记忆、最小 LangGraph 和 MCP。原教程保留原样。

本 Lab 已在 Windows / Python 3.13.9 上运行；实测结果见 [验证报告](docs/04-verification-report.md)。所有命令从本目录执行。

## 1. 创建环境并安装依赖

```powershell
cd D:\workshop\sep\langchain-learning-lab\01-langchain-foundations
python -m venv .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```

如未安装 `uv`，可运行 `.venv\Scripts\python.exe -m pip install -r requirements.txt`。依赖固定在 [requirements.txt](requirements.txt)；虚拟环境不会提交到 Git。

## 2. 启动已缓存的本地模型

```powershell
foundry model list --cached --type chat
foundry model load phi-4-mini
foundry model load qwen2.5-0.5b
foundry server status
```

本机验证使用 `Phi-4-mini-instruct-generic-gpu:5`（模型、Prompt、Memory）和 `qwen2.5-0.5b-instruct-generic-gpu:4`（工具调用、Agent、MCP）。两者此前已缓存，加载没有重新下载模型。`model_factory.py` 自动读取 Foundry 当前端口与已加载 ID；端口会变化，无需写死。

如果使用其他本地 OpenAI-compatible 端点，可参考 [.env.example](.env.example) 在 PowerShell 中设置 `LOCAL_LLM_BASE_URL` 和 `LOCAL_LLM_MODEL` 环境变量。该示例文件不会自动加载；所选模型需要支持 tool calling 才能通过工具阶段。

## 3. 单独运行 Stage

```powershell
.venv\Scripts\python.exe src\stage_a_model.py
.venv\Scripts\python.exe src\stage_b_prompt.py
.venv\Scripts\python.exe src\stage_c_tools.py
.venv\Scripts\python.exe src\stage_d_manual_tool_loop.py
.venv\Scripts\python.exe src\stage_e_agent.py
.venv\Scripts\python.exe src\stage_f_memory.py
.venv\Scripts\python.exe src\stage_g_extensions.py
.venv\Scripts\python.exe src\stage_h_graph.py
.venv\Scripts\python.exe src\stage_i_mcp.py
```

| Stage | 观察重点 |
| --- | --- |
| A | `init_chat_model`、`invoke`、`ainvoke`、stream 的实际模型输出 |
| B | Prompt 变量展开为 System/Human 消息 |
| C | `@tool` schema 与模型生成 `tool_calls`；此时没有自动 Tool Loop |
| D | Python 工具执行、ToolMessage、模型最终回答 |
| E | `create_agent` 自动管理相同的 Tool Loop |
| F | 同线程 Alice 两轮与新线程 UNKNOWN |
| G | Middleware 调用与 Pydantic 结构化输出 |
| H | StateGraph `compile().invoke()` 的状态更新 |
| I | 本地 FastMCP stdio Server → MCPAdapter → Agent → ToolMessage |

## 4. 测试和完整 E2E 验证

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe scripts\verify_all.py
```

测试覆盖确定性工具、Prompt 输入、工具派发、Checkpointer 线程隔离和 Graph 状态。统一入口会逐项实际运行本地链路；只有关键项全部成功才输出 `LOCAL_E2E_PASS`，否则输出 `PARTIAL` 并列出失败项。LangSmith 是 `OPTIONAL / NOT REQUIRED FOR LOCAL E2E`。

## 5. 从哪里开始学习

1. [知识点矩阵](docs/01-syllabus-analysis.md)：原文每章如何映射到可验证内容、哪些示例做了本地化。
2. [E2E 设计](docs/02-e2e-design.md)：每个 Stage 的输入、输出和通过标准。
3. [从头到尾的学习指南](docs/03-learning-guide.md)：Concept → Architecture → Code → Run → Result → Why。
4. [验证报告](docs/04-verification-report.md)：真实环境、命令、结果、修复和限制。

01 里的 LangGraph 与 MCP 仅是原教程涉及的最小预览；后续章节可分别深入学习，01 本身可独立运行和验证。
