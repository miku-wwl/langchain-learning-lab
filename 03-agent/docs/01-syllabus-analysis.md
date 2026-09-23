# 03 教程知识点矩阵

原文：[03.LangChain_v1.4_构建简单Agent_更新版.md](../../doc/03.LangChain_v1.4_构建简单Agent_更新版.md)。本章只做 Agent Harness 教学实验，不导入 01/02，也不实现 MCP 或 RAG。

| ID | 原文章节 | 知识点 | 有代码 | 需 LLM | 需 Tool | 需 State | 本地验证 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | 0、一 | Agent、Model、Harness、`create_agent`、LangGraph runtime 边界 | 是 | 是 | 否 | 是 | A 输出完整消息类型与最终 AIMessage |
| 02 | 二.1–2 | 本地模型、动态端口、`system_prompt` | 是 | 是 | 否 | 是 | A 使用 Foundry Local 已缓存工具模型 |
| 03 | 二.3 | `stream`、`stream_mode=updates`、messages；typed projections 定位 | 是 | 是 | 否 | 是 | B 打印并断言实际事件 |
| 04 | 二.4 | `PIIMiddleware`、email redact、credit card mask | 是 | 是 | 否 | 是 | B 检查送入模型前的消息 |
| 05 | 三.1–2 | `@tool`、schema、Tool Calling、ToolMessage、Agent Loop | 是 | 是 | 是 | 是 | C 检查 AI tool_calls → Python 执行 → ToolMessage → AI 回答 |
| 06 | 三.3 | str/dict/`Command` 返回与 `return_direct` | 概念 | 可选 | 是 | 是 | C 演示普通返回和直接返回；Command 放在 F/H 解释 |
| 07 | 三.4 | `ToolErrorMiddleware`、错误转换、`ToolRetryMiddleware` 区别 | 是 | 是 | 是 | 是 | D 让 `divide(1,0)` 抛错，再检查 error ToolMessage |
| 08 | 四.1 | `InMemorySaver`、短期记忆、`thread_id` | 是 | 是 | 否 | 是 | E 同线程延续、新线程隔离、检查 checkpoint |
| 09 | 四.2 | State / Context / Store 与 `thread_id` / `user_id` | 表 | 是 | 是 | 是 | F 从 State 和 ToolRuntime 读取 user_id；指南解释 Context/Store |
| 10 | 四.3 | 自定义 `AgentState`、`ToolRuntime` 注入 | 是 | 是 | 是 | 是 | F 检查 runtime.state 与工具 schema |
| 11 | 四.4 | `before_model`、`RemoveMessage`、Trim、工具消息配对 | 是 | 可选 | 否 | 是 | G 量化裁剪前后消息数并检查合法历史 |
| 12 | 四.5 | `SummarizationMiddleware`、按消息数触发摘要 | 是 | 是 | 否 | 是 | G 触发短摘要并检查旧/新消息 |
| 13 | 五.1–2 | 安全 Tool / 模拟高风险 Tool、`HumanInTheLoopMiddleware` | 是 | 是 | 是 | 是 | H 安全工具直行，危险工具中断前零执行 |
| 14 | 五.3 | `version=v2`、`interrupts`、`Command(resume)`、approve/reject/edit/respond | 是 | 是 | 是 | 是 | H 真实 approve/reject；edit/respond 按当前 API 作可选探索 |
| 15 | 六 | `SKILL.md`、`load_skill`、渐进式披露、Context Engineering | 是 | 是 | 是 | 是 | I 先只暴露摘要，再按需读取完整 Skill |
| 16 | 六 | Deep Agents 正式 Skills 的定位 | 概念 | 否 | 否 | 否 | I 指南说明，本章不安装 Deep Agents |
| 17 | 七、八 | Harness 总图、概念边界、后续学习路线 | 图/文 | 否 | 否 | 否 | Learning Guide 与报告逐项对应 |

## 本地适配与待核对处

- 原文 `.env` 手填模型与动态端口；本 Lab 独立从 Foundry CLI 读取当前地址和已加载模型 ID。
- 优先试已缓存的 GPU `qwen3-4b`。对需要可靠结构化工具调用的 Agent Prompt 使用 `/no_think`；只有真实调用通过才保留。若某 Stage 不稳定，再试已缓存的工具模型。
- HITL 的 `execute_sql` 只返回 `SIMULATED SQL: ...`，绝不连接数据库；审批、拒绝分别使用独立线程。
- `ToolErrorMiddleware`、`PIIMiddleware`、Summarization 与 HITL API 以安装的 LangChain 1.4.2 实际运行结果为准；差异与修复记录在验证报告。
