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

## D — STDIO：真正跨进程

**Concept**：Client 启动 Server 子进程，JSON-RPC 经 stdin/stdout 传递。普通日志只能走 stderr，否则可能破坏协议流。

**Architecture**：Client PID → `stdio_client` → Server PID → MCP Tool → Client。

**Minimal Code**：`src/raw_stdio_client.py` 显式提供 Python 路径、Server 路径及最小环境变量；`src/stage_d_stdio.py` 用有真实文件描述符的临时文件捕获 Server stderr。

**Run**：`.\.venv\Scripts\python.exe -u src\stage_d_stdio.py`

**Observed Result / Why**：Client/Server PID 不同；Tool、Resource、Prompt 均可访问；stderr 包含 `MCP_STDIO_STARTING pid=...`，JSON-RPC 调用没有被日志污染。Windows 上 `io.StringIO` 没有子进程需要的 `fileno()`，所以这里使用 `tempfile.TemporaryFile`。

## E — Streamable HTTP：本机网络边界

**Concept**：同一个 Server 以 Streamable HTTP 监听回环地址；Client 连接 `/mcp`。按当前[传输规范](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)，客户端消息经 HTTP POST，请求可得到 JSON 或该请求范围内的 SSE 响应。

**Architecture**：Client → `127.0.0.1:<动态端口>/mcp` → 独立 Server 进程。

**Minimal Code**：`src/raw_http_client.py` 选临时端口、启动并在 `finally` 中终止/回收子进程；`src/stage_e_http.py` 用原生 `Client(url)` 调用。

**Run**：`.\.venv\Scripts\python.exe -u src\stage_e_http.py`

**Observed Result / Why**：HTTP 路径同样发现两个 Tool、读取 Resource/Prompt、调用 `add` 得到 5；测试结束时子进程已回收。本例设置 `json_response=True`，没有把 Streamable HTTP 误当成必须常驻的 SSE 连接。

## F — MCPAdapter：MCP Tool 转为 LangChain BaseTool

**Concept**：`MCPAdapter(Path(server))` 明确选择本地脚本，列出 MCP Tools 并转换成 LangChain `BaseTool`。给模型的仍是普通工具 schema。

**Architecture**：MCP Server → MCP Client → MCPAdapter → `BaseTool` → Agent 可使用的工具列表。

**Minimal Code**：`src/stage_f_mcp_adapter.py` 在 `async with MCPAdapter(...)` 生命周期内检查名称、描述、`a`/`b` schema，并 `ainvoke` 调用转换后的工具。

**Run**：`.\.venv\Scripts\python.exe -u src\stage_f_mcp_adapter.py`

**Observed Result / Why**：发现 `add`/`get_course_stage`，`add` 是 `BaseTool` 且返回文本内容 5。安装版的 `tool_call_schema` 为 `dict`，教学代码兼容这一实际类型。适配器完成协议到 LangChain Tool 的转换，不替代 Agent Runtime。

## G — 本地 Agent → MCP → Tool → Agent

**Concept**：这是本章 E2E 判定链路；原生 Client/Adapter 的手动调用不能冒充模型驱动的 Agent 调用。

```text
HumanMessage("37 + 58")
  → 本地 Qwen3-4B
  → AIMessage(tool_calls=[add(a=37,b=58)])
  → Agent Runtime → MCPAdapter → STDIO Client → MCP Server → add()
  → ToolMessage("95") → 模型 → 最终 AIMessage("95")
```

**Minimal Code**：`src/model_factory.py` 从 Foundry Local 发现动态 `/v1` 地址及已加载工具模型；`src/stage_g_agent_mcp.py` 检查每一种消息类型、参数与结果。

**Run**：`.\.venv\Scripts\python.exe -u src\stage_g_agent_mcp.py`

**Observed Result / Why**：本地模型产生 `add(37,58)` 的真实结构化调用；MCP-backed ToolMessage 含 95，最终 AIMessage 含 95。Agent 负责选择与循环，MCP 负责跨进程能力接入。

## H — Direct Tool、专用 Adapter、MCP

**Concept**：三种接入方式各有适用场景；MCP 不会总是比专用 Adapter 更好。

| 接入 | 优势 | 代价 |
| --- | --- | --- |
| 同进程 Direct Tool | 最少代码，适合小能力 | 发现与跨应用复用需另做 |
| 专用 Adapter | 可针对一个系统做精确映射 | 每个系统各写一套集成 |
| MCP Client/Server | 标准化发现、schema、调用与跨进程复用 | 增加协议、Server 生命周期及安全边界 |

**Minimal Code**：`src/stage_h_compare.py` 用同一 `add(2,3)` 演示三条路径。专用 Adapter 中的 Service 是进程内教学替身，不声称验证了真实外部系统。

**Run**：`.\.venv\Scripts\python.exe -u src\stage_h_compare.py`

**Observed Result / Why**：三条路径均得到 5；MCP 路径额外需要先发现 `add`。

## I — 失败与安全边界

**Concept**：MCP 暴露 capability，不自动决定其调用权限。未知 Tool、错误参数、Server 不可用必须清楚失败；敏感动作应在调用之前由应用政策/HITL 阻断。

**Architecture**：Agent proposes Tool → 确定性审批门 → MCP Client → MCP Server。拒绝时不发出 MCP 调用。

**Minimal Code**：`src/stage_i_security.py` 验证未知工具、Pydantic 参数校验、未监听端口的短超时与 STDERR；单独的 `delete_resource` 只返回 `SIMULATED delete`，审批函数先拒绝，再允许模拟调用。

**Run**：`.\.venv\Scripts\python.exe -u src\stage_i_security.py`

**Observed Result / Why**：未知 Tool 得到 error result，`add('abc',3)` 被 schema 拒绝，不可用 Server 明确报错；拒绝时工具零执行，批准后只产生模拟字符串。没有真实删除动作。03 的 Human Approval 思路是调用 MCP Tool 前的控制层，Tool 描述本身不是安全策略。
