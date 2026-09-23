# 04 — LangChain MCP 本地 E2E 学习实验

```text
User
 ↓
LangChain Agent → Local LLM
                    ↓ Tool Call
                Agent Runtime
                    ↓
                MCPAdapter
                    ↓
                 MCP Client
                    ↓ STDIO / Streamable HTTP
                 MCP Server
                    ↓ Tool
                Tool Result
                    ↓ ToolMessage
                Agent → Answer
```

本章依据 [04 教程](../doc/04.LangChain_v1.4_MCP_更新版.md)，先验证 MCP Server/原生 Client，再验证两个传输，最后由本地模型实际调用 MCP Tool。04 独立于 01–03，不用云 API、真实数据库或部署基础设施。

## 环境与安装

- Windows、Python 3.13.9。
- `langchain==1.4.2`、官方 MCP Python SDK `mcp==2.2.0`，见 `requirements.txt`。
- Foundry Local 已加载、支持 Tool Calling 的 `qwen3-4b`。模型工厂动态发现本机 `/v1` 端口；可用 `.env.example` 中的变量覆盖。

PowerShell：

```powershell
cd D:\workshop\sep\langchain-learning-lab\04-mcp
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
foundry server status
foundry model list --loaded
.\.venv\Scripts\python.exe -u scripts\verify_all.py
```

模型若尚未加载且已缓存，可执行 `foundry model load qwen3-4b`。所有 MCP Server 都在本机运行；自动 HTTP 测试会选临时端口并在退出时回收进程。

## 逐步运行

| Stage | 关注点 | 命令（前缀均为 `.\.venv\Scripts\python.exe -u`） |
| --- | --- | --- |
| A | 直接 Python Tool | `src\stage_a_direct_tool.py` |
| B | Tool / Resource / Prompt 注册 | `src\stage_b_server.py` |
| C | 原生 Client 发现与调用 | `src\stage_c_raw_client.py` |
| D | STDIO 子进程 / stderr | `src\stage_d_stdio.py` |
| E | Streamable HTTP 本机调用与清理 | `src\stage_e_http.py` |
| F | MCPAdapter 转成 LangChain BaseTool | `src\stage_f_mcp_adapter.py` |
| G | 本地 Agent → MCP → add(37,58) | `src\stage_g_agent_mcp.py` |
| H | Direct / 专用 Adapter / MCP 对比 | `src\stage_h_compare.py` |
| I | 错误与模拟审批边界 | `src\stage_i_security.py` |

手动启动 STDIO Server：

```powershell
.\.venv\Scripts\python.exe -u src\mcp_server.py
```

STDIO 没有人类可读的普通 stdout；Client 会负责启动 Server 子进程。手动启动 HTTP Server：

```powershell
.\.venv\Scripts\python.exe -u src\mcp_server.py --http --port 8000
```

另一终端用 `Client("http://127.0.0.1:8000/mcp")` 连接。自动验证不依赖固定 8000 端口。

## 测试与学习资料

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe -u scripts\verify_all.py
```

完整入口仅在测试与 A–I 的实际运行都通过时输出 `04_MCP_PASS_LOCAL`。

- [知识点矩阵](docs/01-syllabus-analysis.md)
- [E2E 设计](docs/02-e2e-design.md)
- [学习指南](docs/03-learning-guide.md)
- [验证报告](docs/04-verification-report.md)

`delete_resource` 只在 Stage I 的独立教学 Server 中返回 `SIMULATED delete`；拒绝审批时根本不发送 MCP 调用，没有真实删除副作用。
