# 01 本地验证报告

**日期：2026-09-23。最终状态：PASS_LOCAL。** 在本机执行了各 Stage、5 个确定性测试和统一 E2E 入口，统一入口输出 `LOCAL_E2E_PASS`。此结论只覆盖下面列出的本地环境与执行链路。

## 环境

| 项目 | 实测值 |
| --- | --- |
| OS / shell | Windows / PowerShell |
| Python | 3.13.9；本阶段独立 `.venv` |
| LangChain / langchain-core | 1.4.2 / 1.6.4 |
| langchain-openai | 1.6.4 |
| LangGraph | 1.2.12 |
| FastMCP | 4.0.5 |
| Foundry Local CLI | 0.10.3 |
| Model A | `Phi-4-mini-instruct-generic-gpu:5`，GPU、已缓存；Model、Prompt、Memory、Middleware |
| Model B | `qwen2.5-0.5b-instruct-generic-gpu:4`，GPU、已缓存；Tool Calling、Agent、Structured Output、MCP |
| 本地 API | Foundry Local OpenAI-compatible `/v1`；本次运行地址 `http://127.0.0.1:53494/v1`（端口动态变化） |
| 云模型与 LangSmith | 未使用；统一验证入口关闭 tracing |

## 实际执行命令

从 `01-langchain-foundations` 目录执行：

```powershell
python -m venv .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
foundry model load phi-4-mini
foundry model load qwen2.5-0.5b
foundry server status --output json
foundry model list --loaded --output json
.venv\Scripts\python.exe src\stage_a_model.py
.venv\Scripts\python.exe src\stage_b_prompt.py
.venv\Scripts\python.exe src\stage_c_tools.py
.venv\Scripts\python.exe src\stage_d_manual_tool_loop.py
.venv\Scripts\python.exe src\stage_e_agent.py
.venv\Scripts\python.exe src\stage_f_memory.py
.venv\Scripts\python.exe src\stage_g_extensions.py
.venv\Scripts\python.exe src\stage_h_graph.py
.venv\Scripts\python.exe src\stage_i_mcp.py
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe scripts\verify_all.py
```

## Stage 结果和关键证据

| Stage | 状态 | 实际观察 |
| --- | --- | --- |
| A Model | PASS_LOCAL | `INVOKE=Hello!`；`INIT_CHAT_MODEL=Hello!`；`AINVOKE=I am Phi, an advanced digital assistant.`；`STREAM_CHUNKS=12`。 |
| B Prompt | PASS_LOCAL | System/Human 两条消息正确展开；模型回复 `你好，怎么样?`。 |
| C Tools | PASS_LOCAL | 工具 schema 要求整数 `a`、`b`；Python 调用得 `42`；模型 `tool_calls` 为 `add(17,25)`。 |
| D Manual Tool Loop | PASS_LOCAL | `AI_TOOL_CALLS` → Python add 真实执行 → `TOOL_MESSAGE=42` → 最终回答含 `42`。 |
| E `create_agent` | PASS_LOCAL | Agent 消息中有 `add` tool call、内容为 `42` 的 ToolMessage、最终回答含 `42`；执行日志确认函数运行。 |
| F Memory | PASS_LOCAL | 同线程第一轮/第二轮均为 Alice；新线程 `UNKNOWN`；检查点消息数 `4,2`。 |
| G Extensions | PASS_LOCAL | `MIDDLEWARE_CALLS=[1]`；结构化响应 `name='Alice' age=30`。 |
| H LangGraph | PASS_LOCAL | `compile().invoke()` 返回 `{'value': 42, 'visited': ['increment', 'double']}`。 |
| I MCP | PASS_LOCAL | `MCP_DISCOVERED_TOOLS=['add']`；Agent 调用 `add(17,25)`；本地 MCP ToolMessage 文本为 `42`；最终回答含 `42`。 |
| J LangSmith | OPTIONAL | `OPTIONAL / NOT REQUIRED FOR LOCAL E2E`；未配置 API key 或远程 tracing。 |

**测试**：`.venv\Scripts\python.exe -m pytest -q` 输出 `5 passed in 1.97s`。测试分别覆盖 Tool 与 schema、Prompt 必填变量、Tool dispatch 与 ID、Checkpointer 线程隔离、Graph 状态顺序。

**统一 E2E**：`.venv\Scripts\python.exe scripts\verify_all.py` 依次重新执行 A–I，所有项目显示 `PASS`，末行显示 `LOCAL_E2E_PASS`。

## 原文示例的修复与运行中发现的问题

| 来源/症状 | 原因 | 修复与验证 |
| --- | --- | --- |
| 原文 `from config.load_key import load_key` | 原文没有附带 `config.load_key`；云端示例还需要账户 secret。 | 改用本地 Foundry Local 配置探测器；Stage A–I 无云端密钥运行通过。 |
| 原文 `qwen-plus`、DashScope URL 与 `ChatTongyi` | 属于特定云 provider 示例；本次禁止使用付费云 API。 | 保留原文，另建 `model_factory.py` 使用本地 OpenAI-compatible 端点；验证统一 LangChain 模型接口。 |
| 原文 MCP `https://example.com/mcp`、`openai:gpt-5.5` | 分别是示意地址和云模型，不能证明本地 MCP E2E。 | 本地 `mcp_server.py` 经 stdio 由 `MCPAdapter(Path(...))` 连接，配合本地 Qwen，Stage I 完整通过。 |
| `GET /openai/loadedmodels` 返回 404 | 本机 Foundry CLI 0.10.3 未提供该路径。 | 用 `foundry server status --output json` 与 `foundry model list --loaded --output json` 读取当前 URL 和模型 ID；之后 A–I 通过。 |
| Phi-4-mini 首次 `bind_tools([add])` 后 `tool_calls=[]` | 本地模型直接回答了 `42`；强制 `tool_choice='required'` 可产生调用，但不能验证自主选工具。 | 工具阶段改用已缓存的 Qwen 2.5 0.5B；未强制工具选择，Stage C/D/E/I 均产生结构化 tool call。 |
| Stage B、统一验证器在 Windows cp1252 终端打印中文时报 `UnicodeEncodeError` | 控制台默认输出编码不能表示中文。 | Python 输出切到 UTF-8；重跑 Stage B 与统一 E2E 通过。 |
| MCP 首次返回 `MCP_ADD_EXECUTED=42`，ToolMessage 到达但 Qwen 最终回答未写出数字 | 小模型没从复杂工具文本复制数字。 | MCP 工具改为直接返回整数 `42`，提示词要求复述工具值；Stage I 和统一 E2E 重跑通过。 |

原文的 `selected_tool.invoke(tool_call)`、`create_agent`、`ChatPromptTemplate`、`InMemorySaver` 和 `MCPAdapter` 在安装的 1.4.2 环境中均可运行；没有发现这些 API 本身需要改名。`langchain.mcp` 在 [官方文档](https://docs.langchain.com/oss/python/langchain/mcp) 中标为 beta，本 Lab 固定了相关依赖版本。

## 阻碍与结论

**当前 blocker：无。** LangSmith 没有接入，因为它是可选观测平台，不能作为本地 Agent E2E 的必需条件。Phi/Qwen 的自然语言措辞可能随重复运行变化，所以 E2E 校验结构、工具执行和关键事实，不比较整句文本。

**最终结论：PASS_LOCAL。** 这证明本机当前已缓存模型、Foundry Local 服务和固定依赖组合下的 01 学习链路真实运行成功；并不表示任何云 provider、跨进程持久化或生产部署已经验证。

## 2026-09-23：Qwen3-4b 候选模型复核

本机已缓存并加载 `qwen3-4b-generic-gpu:2`。本次仅通过临时 `LOCAL_LLM_MODEL` 环境变量覆盖模型，未改动 01 的默认选择。单独的 Stage C 工具调用返回结构化 `add(17, 25)`，状态 PASS。随后统一入口实测 Model、Prompt、工具调用、手写工具循环、`create_agent`、短期记忆和 LangGraph 为 PASS；Middleware / Structured Output 与 MCP 各在 180 秒后超时，候选模型的整章结果为 **PARTIAL**。Qwen3-4b 在本机还会输出较长的 `<think>` 文本。现有 Phi-4-mini 与 qwen2.5-0.5b 组合仍是上文已经完整通过的 01 默认配置；不能把候选模型这次的部分通过当成 01 的新 E2E PASS。
