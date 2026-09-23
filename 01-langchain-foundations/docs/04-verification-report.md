# 01 本地验证报告

**日期：2026-09-23。当前默认 Qwen3-4b 配置的最终状态：PASS_LOCAL。** 在本机执行了各 Stage、5 个确定性测试和统一 E2E 入口，统一入口输出 `LOCAL_E2E_PASS`。此结论只覆盖下面列出的本地环境与执行链路。

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
| 当前聊天模型 | `qwen3-4b-generic-gpu:2`，GPU、已缓存；A–I 的全部模型调用 |
| 本地 API | Foundry Local OpenAI-compatible `/v1`；本次运行地址 `http://127.0.0.1:53494/v1`（端口动态变化） |
| 云模型与 LangSmith | 未使用；统一验证入口关闭 tracing |

## 实际执行命令

从 `01-langchain-foundations` 目录执行：

```powershell
python -m venv .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
foundry model load qwen3-4b
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
| A Model | PASS_LOCAL | `invoke`、`init_chat_model`、`ainvoke`、stream 都真实返回；本次 `STREAM_CHUNKS=194`。Qwen3 的 `<think>` 输出在短上限下可能截断最终句。 |
| B Prompt | PASS_LOCAL | System/Human 两条消息正确展开；本地模型返回非空内容。 |
| C Tools | PASS_LOCAL | 工具 schema 要求整数 `a`、`b`；Python 调用得 `42`；模型 `tool_calls` 为 `add(17,25)`。 |
| D Manual Tool Loop | PASS_LOCAL | `AI_TOOL_CALLS` → Python add 真实执行 → `TOOL_MESSAGE=42` → 最终回答含 `42`。 |
| E `create_agent` | PASS_LOCAL | Agent 消息中有 `add` tool call、内容为 `42` 的 ToolMessage、最终回答含 `42`；执行日志确认函数运行。 |
| F Memory | PASS_LOCAL | 同线程第一轮/第二轮均为 Alice；新线程 `UNKNOWN`；检查点消息数 `4,2`。 |
| G Extensions | PASS_LOCAL | `MIDDLEWARE_CALLS=[1]`；结构化响应 `name='Alice' age=30`。 |
| H LangGraph | PASS_LOCAL | `compile().invoke()` 返回 `{'value': 42, 'visited': ['increment', 'double']}`。 |
| I MCP | PASS_LOCAL | `MCP_DISCOVERED_TOOLS=['add']`；Agent 调用 `add(17,25)`；本地 MCP ToolMessage 文本为 `42`；最终回答含 `42`。 |
| J LangSmith | OPTIONAL | `OPTIONAL / NOT REQUIRED FOR LOCAL E2E`；未配置 API key 或远程 tracing。 |

**测试**：`.venv\Scripts\python.exe -m pytest -q` 的最终默认配置复跑输出 `5 passed in 1.40s`。测试分别覆盖 Tool 与 schema、Prompt 必填变量、Tool dispatch 与 ID、Checkpointer 线程隔离、Graph 状态顺序。

**统一 E2E**：`.venv\Scripts\python.exe scripts\verify_all.py` 依次重新执行 A–I，所有项目显示 `PASS`，末行显示 `LOCAL_E2E_PASS`。

## 原文示例的修复与运行中发现的问题

| 来源/症状 | 原因 | 修复与验证 |
| --- | --- | --- |
| 原文 `from config.load_key import load_key` | 原文没有附带 `config.load_key`；云端示例还需要账户 secret。 | 改用本地 Foundry Local 配置探测器；Stage A–I 无云端密钥运行通过。 |
| 原文 `qwen-plus`、DashScope URL 与 `ChatTongyi` | 属于特定云 provider 示例；本次禁止使用付费云 API。 | 保留原文，另建 `model_factory.py` 使用本地 OpenAI-compatible 端点；验证统一 LangChain 模型接口。 |
| 原文 MCP `https://example.com/mcp`、`openai:gpt-5.5` | 分别是示意地址和云模型，不能证明本地 MCP E2E。 | 本地 `mcp_server.py` 经 stdio 由 `MCPAdapter(Path(...))` 连接，配合本地 Qwen，Stage I 完整通过。 |
| `GET /openai/loadedmodels` 返回 404 | 本机 Foundry CLI 0.10.3 未提供该路径。 | 用 `foundry server status --output json` 与 `foundry model list --loaded --output json` 读取当前 URL 和模型 ID；之后 A–I 通过。 |
| 初始 Phi-4-mini `bind_tools([add])` 后 `tool_calls=[]` | 本地模型直接回答了 `42`；强制 `tool_choice='required'` 可产生调用，但不能验证自主选工具。 | 初始版本用 Qwen 2.5 0.5B；现已在 Qwen3-4b 上实测 Stage C/D/E/I 的结构化工具调用。 |
| Stage B、统一验证器在 Windows cp1252 终端打印中文时报 `UnicodeEncodeError` | 控制台默认输出编码不能表示中文。 | Python 输出切到 UTF-8；重跑 Stage B 与统一 E2E 通过。 |
| MCP 首次返回 `MCP_ADD_EXECUTED=42`，ToolMessage 到达但 Qwen 最终回答未写出数字 | 小模型没从复杂工具文本复制数字。 | MCP 工具改为直接返回整数 `42`，提示词要求复述工具值；Stage I 和统一 E2E 重跑通过。 |

原文的 `selected_tool.invoke(tool_call)`、`create_agent`、`ChatPromptTemplate`、`InMemorySaver` 和 `MCPAdapter` 在安装的 1.4.2 环境中均可运行；没有发现这些 API 本身需要改名。`langchain.mcp` 在 [官方文档](https://docs.langchain.com/oss/python/langchain/mcp) 中标为 beta，本 Lab 固定了相关依赖版本。

## 阻碍与结论

**当前 blocker：无。** LangSmith 没有接入，因为它是可选观测平台，不能作为本地 Agent E2E 的必需条件。Qwen3 的自然语言措辞可能随重复运行变化，所以 E2E 校验结构、工具执行和关键事实，不比较整句文本。部分示例会输出 `<think>`，不应将其当作面向用户的最终句子。

**最终结论：PASS_LOCAL。** 这证明本机当前已缓存模型、Foundry Local 服务和固定依赖组合下的 01 学习链路真实运行成功；并不表示任何云 provider、跨进程持久化或生产部署已经验证。

## 2026-09-23：Qwen3-4b 复核与修复

本机已缓存并加载 `qwen3-4b-generic-gpu:2`。初次只用临时 `LOCAL_LLM_MODEL` 覆盖模型时，Stage C 返回结构化 `add(17,25)`，但整章为 **PARTIAL**：一次复跑的 Middleware / Structured Output 和 MCP 各超时 180 秒；再次复跑的结构化阶段超时，MCP 已发现本地工具但模型未发出 `tool_calls`。两个失败都发生在本地 Foundry Local 调用链，不能归因于外网。

定向检查发现 Middleware 本身已完成，阻塞在结构化 schema 工具调用。给 Qwen3-4b 的结构化 Agent System Prompt 追加 `/no_think` 后，真实返回 `Person(name='Alice', age=30)`；给 MCP Agent 同样追加后，实际执行本地 `add(17,25)`，ToolMessage 为 `42`，最终回答包含 `42`。这两处仅在模型 ID 含 `qwen3` 时追加指令。随后以 Qwen3 覆盖模型重新运行 A–I，全部 PASS，统一入口输出 `LOCAL_E2E_PASS`，因此将 01 默认聊天模型切为 Qwen3-4b。最终默认配置的独立复跑结果见本报告上方。
