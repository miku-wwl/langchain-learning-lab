# 01 教程知识点盘点

原文：[01.LangChain_v1.4_架构解读与学习路线.md](../../doc/01.LangChain_v1.4_架构解读与学习路线.md)（仓库根目录的 `doc/`，本 Lab 不修改原文）。本文以原教程的章节为边界，运行代码固定使用 LangChain 1.4.2。

| ID | 原文章节 | 知识点 | 原文代码 | 需模型 | 外部服务 | 本地验证 |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | 课程目标、第一章 | LangChain、LangGraph、Deep Agents、LangSmith 分工；Agent = Model + Harness | 否 | 否 | 否 | 学习指南中说明各层职责 |
| 02 | 第一章 v1.3 → v1.4 | 第一方 `langchain.mcp.MCPAdapter`、beta、FastMCP | 否 | 否 | 否 | 检查安装版本和本地 MCP 接入 |
| 03 | 第二章 1 | Python 与依赖安装、LangSmith 环境变量 | 是 | 否 | 否 | 虚拟环境安装及版本检查；LangSmith 为可选 |
| 04 | 第二章 2 | 模型抽象、`init_chat_model`、`invoke`、本地兼容接口 | 是 | 是 | 本地模型服务 | Stage A 真实模型回复 |
| 05 | 第六章路线 1 | `ainvoke`、streaming | 仅提及 | 是 | 本地模型服务 | Stage A 异步调用和至少一个流片段 |
| 06 | 第二章 5 | `ChatPromptTemplate`、模板变量、System/Human 消息 | 是 | 否/是 | 本地模型服务 | Stage B 检查模板输入并调用模型 |
| 07 | 第二章 3 | `@tool`、工具 schema、确定性工具执行 | 是 | 否 | 否 | Stage C 直接执行和检查 schema |
| 08 | 第二章 3 | `bind_tools` 与 `AIMessage.tool_calls` | 是 | 是 | 本地模型服务 | Stage C 模型生成结构化工具调用 |
| 09 | 第二章 3 | 手工 Tool Loop、`ToolMessage`、二次模型调用 | 是 | 是 | 本地模型服务 | Stage D 真实执行工具并返回模型 |
| 10 | 第二章 4 | `create_agent` 与 Agent Loop | 是 | 是 | 本地模型服务 | Stage E 检查 AI/Tool/AI 消息链 |
| 11 | 第二章 6 | Messages、Agent State、Checkpointer、`thread_id`、短期记忆 | 是 | 是 | 本地模型服务 | Stage F 同线程 Alice 两轮及异线程隔离；检查保存状态 |
| 12 | 第二章 5、第五章、第六章 | Context、Middleware、Structured Output 的定位 | 概念 | 是 | 本地模型服务 | Stage G 最小中间件与结构化输出；记录模型兼容性 |
| 13 | 第一章、第五章、第六章 | LangGraph State、Node、Edge、compile、invoke | 概念 | 否 | 否 | Stage H 最小确定性图和状态更新 |
| 14 | 第三章 | MCP Server、Adapter、`list_tools`、Agent | 是 | 是 | 本地 MCP 子进程与模型 | Stage I 本地 stdio MCP 工具完整调用链 |
| 15 | 第四章 | LangSmith tracing、debug、dataset、eval、monitoring | 环境变量 | 否 | 可选云平台 | 解释平台职责；本地 E2E 不启用 tracing |
| 16 | 第五至七章 | 组件关系、学习顺序、v1.4 基线 | 否 | 否 | 否 | 学习指南与最终验证报告逐项映射 |

## 原文代码的本地化处理

| 原文代码/设置 | 本 Lab 的处理与原因 |
| --- | --- |
| `from config.load_key import load_key` | 原文没有提供此模块；本 Lab 使用本地 Foundry URL 和占位 API key，无需云端 secret。 |
| `qwen-plus`、DashScope URL、`ChatTongyi` | 它们依赖云端账户或额外 provider；用已缓存的 Foundry Local 模型验证同一 LangChain 接口。 |
| `model="openai:gpt-5.5"` | 示例会访问云端；MCP Stage 使用与其他 Stage 相同的本地模型对象。 |
| `MCPAdapter("https://example.com/mcp")` | 这是不可执行的示意地址；改为本地 FastMCP server 的 stdio 脚本路径。 |
| 原文只提及 streaming、Structured Output、Middleware、LangGraph，无完整示例 | 在本阶段加入最小教学实例，作为原文概念的可运行验证；后续阶段仍可深入。 |

原文工具循环的 `selected_tool.invoke(tool_call)` 和 `InMemorySaver` 用法先按 1.4.2 实际运行检查，若发现版本差异或模型兼容问题，记录在 `04-verification-report.md`。
