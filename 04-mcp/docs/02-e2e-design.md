# 04 MCP 本地 E2E 设计

```text
User → LangChain Agent → Local LLM → AIMessage(tool_calls)
                        ↓
               Agent Runtime → MCPAdapter → MCP Client
                                             ↓  STDIO / HTTP
                                           MCP Server
                                             ↓
                                           add(a,b)
                                             ↓
                         ToolMessage ← Tool Result → Final AIMessage
```

| Stage | 最小输入 | 真实检查 | PASS 条件 |
| --- | --- | --- | --- |
| A Direct Tool | `add(2,3)` | 直接 Python 返回 5 | 不依赖 MCP |
| B MCP Server | 两个 Tool、一项 Resource、一项 Prompt | 注册及 schema | 三类能力分开存在 |
| C Raw Client | Server 对象 | `list_tools`、`call_tool`、Resource、Prompt | 不使用 LangChain/LLM，add=5 |
| D STDIO | Python 子进程 | Discovery、Call、stderr 日志、stdout 协议 | 子进程退出且无协议污染 |
| E HTTP | loopback 独立进程 | `/mcp` 发现与调用、启动和关闭 | 没有孤儿进程 |
| F MCPAdapter | `Path` 指向 STDIO Server | MCP Tool → BaseTool schema | adapter tool 可调用 |
| G Agent MCP | 37+58 | AI tool_calls、MCP 执行、ToolMessage、最终 AI | 本地模型完整循环且结果 95 |
| H 对比 | 同一能力 | Direct / Dedicated / MCP 边界 | 文档解释权衡 |
| I 失败与安全 | unknown、invalid、unavailable | 明确错误、超时、模拟敏感操作 | 无实际破坏性副作用 |

每关独立运行后再进入下一关。`scripts/verify_all.py` 必须重新执行本地链路与确定性测试，所有核心检查真实通过才输出 `04_MCP_PASS_LOCAL`。先得到 PASS_LOCAL，再整理 7–9 笔可运行的学习提交，最终 HEAD 复跑后正常推送。
