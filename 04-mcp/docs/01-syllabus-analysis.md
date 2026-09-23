# 04 教程知识点矩阵

唯一 syllabus：[04.LangChain_v1.4_MCP_更新版.md](../../doc/04.LangChain_v1.4_MCP_更新版.md)。本章只做本地 MCP 协议与 LangChain 接入实验；04 不 import 01–03。

| ID | Markdown 章节 | 知识点 | MCP Server | LLM | Transport | E2E 方式 |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | 一 | MCP Host / Client / Server 职责 | 否 | 否 | 无 | 指南画清三层边界 |
| 02 | 一、六 | Tool、Resource、Prompt 三类 primitive | 是 | 否 | in-process | 分别 list/call/read/get |
| 03 | 二、九 | Tool Calling 与 MCP 的区别 | 否 | 否 | 无 | A 直接 Python 调用；H 对比 |
| 04 | 四 | 官方 MCP Python SDK v2、`MCPServer` | 是 | 否 | in-process | B 建立并注册能力 |
| 05 | 四 | Raw `Client`、Tool Discovery | 是 | 否 | in-process | C `list_tools` 检查名称/schema |
| 06 | 四 | Raw Tool Call | 是 | 否 | in-process | C `call_tool('add')` 返回 5 |
| 07 | 三.1 | STDIO、JSON-RPC、stdin/stdout、stderr 日志 | 是 | 否 | STDIO | D 客户端启动子进程并检查协议流 |
| 08 | 三.2 | Streamable HTTP、request-scoped 响应 | 是 | 否 | HTTP | E 本机端口启动、发现/调用、关闭 |
| 09 | 五 | 一方 `langchain.mcp.MCPAdapter` | 是 | 否 | STDIO | F 列出并转换成 BaseTool |
| 10 | 五 | Local Foundry 模型与 `create_agent` | 是 | 是 | STDIO | G 验证 AI tool_calls → ToolMessage → 最终回答 |
| 11 | 五 | Agent Runtime 与 MCP Server 边界 | 是 | 是 | STDIO | G 记录完整消息循环 |
| 12 | 二、九 | Direct Tool / Dedicated Adapter / MCP | 否 | 否 | 对比 | H 教学对比与适用条件 |
| 13 | 八 | Unknown tool、invalid args、server unavailable | 是 | 否 | STDIO/HTTP | I 明确失败、短超时 |
| 14 | 八 | Security boundary、最小权限、Human Approval | 是 | 否 | 两种 | I 只模拟敏感动作，文档解释审批层 |

## 本地适配

- 模型使用机器上已缓存且支持 Tool Calling 的 Foundry Local 模型；模型工厂动态发现本机 `/v1` 地址。
- 同一 `MCPServer` 暴露 Tool、Resource、Prompt，通过 in-process、STDIO 与本机 HTTP 分别验证。in-process 只作独立协议 baseline，不能代替跨进程和 HTTP 证据。
- `MCPAdapter`、SDK 返回值及传输参数以安装版本为准；差异与修复写入验证报告。
