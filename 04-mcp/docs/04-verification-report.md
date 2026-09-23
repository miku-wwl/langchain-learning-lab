# 04 MCP 本地验证报告

日期：2026-09-23（Pacific/Auckland）。范围：`04-mcp/` 的 A–I 本地学习实验。[唯一 syllabus](../../doc/04.LangChain_v1.4_MCP_更新版.md)。

## 环境

| 项目 | 实测值 |
| --- | --- |
| OS | Windows，PowerShell |
| Python | 3.13.9 |
| LangChain | 1.4.2 |
| LangGraph | 1.2.12 |
| 官方 MCP Python SDK | 2.2.0 |
| Foundry Local | CLI 0.10.3；本机 `http://127.0.0.1:53494/v1`（端口动态） |
| 模型 | `qwen3-4b-generic-gpu:2`，已缓存/加载，GPU，声明支持 Tool Calling |
| 传输 | SDK in-process、STDIO 子进程、回环地址 Streamable HTTP |
| 云 API / Secret | 未使用 |

## 命令

在 `04-mcp/` 下执行：

```powershell
python --version
foundry --version
foundry server status --output json
foundry model list --cached --output json
foundry model list --loaded --output json
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -u src\stage_a_direct_tool.py
.\.venv\Scripts\python.exe -u src\stage_b_server.py
.\.venv\Scripts\python.exe -u src\stage_c_raw_client.py
.\.venv\Scripts\python.exe -u src\stage_d_stdio.py
.\.venv\Scripts\python.exe -u src\stage_e_http.py
.\.venv\Scripts\python.exe -u src\stage_f_mcp_adapter.py
.\.venv\Scripts\python.exe -u src\stage_g_agent_mcp.py
.\.venv\Scripts\python.exe -u src\stage_h_compare.py
.\.venv\Scripts\python.exe -u src\stage_i_security.py
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe -u scripts\verify_all.py
```

## 逐关证据

| Stage | 关键实测 | 状态 |
| --- | --- | --- |
| A Direct | `add(2,3)=5`，没有 MCP | PASS_LOCAL |
| B Server | 注册 `add`、`get_course_stage`、`course://summary`、`explain_mcp`；add schema 含两个整数参数 | PASS_LOCAL |
| C Raw Client | 独立 `list_tools` → `call_tool` 得 `{'result':5}`，Resource/Prompt 可读取，协议版本 `2026-07-28` | PASS_LOCAL |
| D STDIO | Client/Server PID 不同；发现/调用成功；启动日志在 stderr；stdout 协议未污染 | PASS_LOCAL |
| E HTTP | 临时回环端口 `/mcp` 发现/调用成功；子进程最终已回收 | PASS_LOCAL |
| F MCPAdapter | 发现两个 Tool；`add` 是 `BaseTool`，LangChain schema 含 `a`/`b`，`ainvoke` 返回 5 | PASS_LOCAL |
| G Agent | Qwen3-4B 产生 `add(a=37,b=58)` 的 `AIMessage.tool_calls`；MCP ToolMessage 含 95；最终 AIMessage 含 95 | PASS_LOCAL |
| H 对比 | Direct、专用 Adapter 教学替身、MCP Client 三种路径都得到 5 | PASS_LOCAL |
| I 失败/安全 | Unknown Tool、invalid args、Server unavailable 均明确失败；审批拒绝零执行，批准只模拟 | PASS_LOCAL |

测试：`12 passed, 1 warning`。警告是 `langchain.mcp` 当前 beta API 提示，不是测试失败。统一入口再次执行测试及 A–I，退出码 0 并输出 `04_MCP_PASS_LOCAL`。

## 教程与实际 API 的差异、修复

1. LangChain 1.4.2 的 `MCPAdapter` 应在 `async with` 生命周期里列工具。这里使用 `Path` 指向本地 Server；普通字符串 target 是 HTTP(S) URL。
2. 转换后的 `BaseTool.tool_call_schema` 在已装版本中是 `dict`，不支持直接调用 `model_json_schema()`；已按实际类型检查 schema。
3. Windows 子进程 stderr 捕获需要真实文件描述符；`io.StringIO` 报 `UnsupportedOperation: fileno`，改用 `tempfile.TemporaryFile` 后 STDIO E2E 通过。
4. HTTP Server 的测试主动 `terminate()`；Windows 下被终止进程可返回退出码 1。判据是请求成功、进程已回收、没有残留服务，而不是将主动停止的退出码误称 Server 崩溃。

## 安全与结论

STDIO 子进程只接收显式 allowlist 环境变量；HTTP 仅绑定 `127.0.0.1` 的临时端口。模拟 `delete_resource` 不连接文件系统、数据库或服务。这里的审批函数用于证明 MCP 调用前可以阻断动作，不声称它本身就是 03 章完整 HITL Middleware。

**最终状态：PASS_LOCAL。** Blocker：无。本章没有验证公网部署、OAuth、真实外部业务服务或持久化数据。
