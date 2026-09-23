# 04 LangChain MCP 学习指南

本章按 [04 教程](../../doc/04.LangChain_v1.4_MCP_更新版.md) 的路线，先证明 MCP 本身能发现与调用能力，再把 MCP Tool 交给 LangChain Agent。每个 Stage 的完整代码在 `src/stage_*.py`；以下命令都在 `04-mcp/` 内运行。

```text
User → Host（本章的 LangChain 应用）
          ├─ Local LLM + Agent Runtime：决定何时调用、保存消息并循环
          └─ MCP Client：按协议发现与调用能力
                         ↓ STDIO 或 Streamable HTTP
                      MCP Server：只暴露显式注册的能力
                         ├─ Tools：执行动作
                         ├─ Resources：提供内容
                         └─ Prompts：提供可复用模板
```

MCP 规范负责能力的描述、发现与调用；模型的 Tool Calling 负责提出工具名称和参数；Agent Runtime 负责执行与后续循环。MCP Server 不承担 Agent 的推理职责。官方 [Python SDK Client 文档](https://py.sdk.modelcontextprotocol.io/client/) 说明了这几类协议操作；[LangChain MCPAdapter 参考](https://reference.langchain.com/python/langchain/mcp/adapter/MCPAdapter/list_tools) 说明了工具转换接口。

## A — 直接 Python Tool baseline

**Concept**：计算能力存在于普通 Python 函数里，本身与 MCP 无关。

**Architecture**：Caller → `direct_tool.add(2,3)` → `5`。

**Minimal Code**：`src/direct_tool.py` 定义有整数检查的 `add`；`src/stage_a_direct_tool.py` 直接调用。

**Run**：`.\.venv\Scripts\python.exe -u src\stage_a_direct_tool.py`

**Observed Result / Why**：返回 5。后面不论换 STDIO、HTTP 或 Agent，计算语义应保持一致；协议只改变接入方式。

## B — MCP Server 的三类 primitive

**Concept**：`MCPServer` 同时注册 `add`、`get_course_stage` 两个 Tool，`course://summary` Resource 和 `explain_mcp` Prompt。

**Architecture**：注册函数 → MCP Server 的工具、资源、提示列表。

**Minimal Code**：`src/mcp_server.py` 用 `@mcp.tool()`、`@mcp.resource()`、`@mcp.prompt()` 注册；`src/stage_b_server.py` 读取 Server 注册表和 `add` 参数 schema。

**Run**：`.\.venv\Scripts\python.exe -u src\stage_b_server.py`

**Observed Result / Why**：列出两个 Tool、一项 Resource、一项 Prompt；`add` schema 中 `a`/`b` 是整数。Tool 做动作，Resource 给数据，Prompt 给模板，三者不可混称 Tool。

## C — Raw MCP Client：先发现，再调用

**Concept**：`Client(mcp)` 是 SDK 的 in-process 测试模式。它仍走 MCP Client API，但不证明子进程或网络传输。

**Architecture**：Client → `list_tools()` → 选 `add` → `call_tool()` → 结构化 `{'result': 5}`。Resource 用 `read_resource()`，Prompt 用 `get_prompt()`。

**Minimal Code**：`src/raw_client.py` 的 `inspect_client` 先检查发现列表与 schema，再做工具调用、资源读取、提示渲染；`src/stage_c_raw_client.py` 不 import LangChain。

**Run**：`.\.venv\Scripts\python.exe -u src\stage_c_raw_client.py`

**Observed Result / Why**：发现 `add`/`get_course_stage`，调用结果是 5；还读到 Resource 与 Prompt，协商协议版本为 `2026-07-28`。这一关把 MCP 自身故障与后续模型选择问题分开。
