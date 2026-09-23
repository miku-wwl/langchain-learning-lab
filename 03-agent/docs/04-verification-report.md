# 03 Agent 本地验证报告

日期：2026-09-23（Pacific/Auckland）。范围仅为本目录 A–I 的本地学习实验。依据：[03 原教程](../../doc/03.LangChain_v1.4_构建简单Agent_更新版.md) 与用户提供的执行要求。

## 环境与运行命令

| 项目 | 实测值 |
| --- | --- |
| Python | 3.13.9 |
| LangChain | 1.4.2 |
| langchain-core | 1.6.4 |
| langchain-openai | 1.6.4 |
| LangGraph | 1.2.12 |
| Foundry Local | CLI 0.10.3；本地 `http://127.0.0.1:53494/v1`（端口动态） |
| A–G 模型 | `qwen3-4b-generic-gpu:2`，已缓存/加载、支持工具调用 |
| H/I 模型 | `qwen2.5-0.5b-instruct-generic-gpu:4`，已缓存/加载、支持工具调用 |
| 云 API / 数据库 | 未使用；SQL 只返回模拟字符串 |

在 `03-agent` 执行：

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
foundry server status --output json
foundry model list --loaded --output json
.\.venv\Scripts\python.exe -u src\stage_a_agent.py
.\.venv\Scripts\python.exe -u src\stage_b_streaming_pii.py
.\.venv\Scripts\python.exe -u src\stage_c_tools.py
.\.venv\Scripts\python.exe -u src\stage_d_tool_errors.py
.\.venv\Scripts\python.exe -u src\stage_e_memory.py
.\.venv\Scripts\python.exe -u src\stage_f_state_runtime.py
.\.venv\Scripts\python.exe -u src\stage_g_context.py
.\.venv\Scripts\python.exe -u src\stage_h_hitl.py
.\.venv\Scripts\python.exe -u src\stage_i_skill.py
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe -u scripts\verify_all.py
```

## 逐阶段实测证据

| Stage | 关键观察 | 状态 |
| --- | --- | --- |
| A `create_agent` | 模型前捕获到系统提示；状态为 `HumanMessage, AIMessage` | PASS_LOCAL |
| B Streaming / PII | updates 1 个、messages 27 个流片段；模型前输入为 `[REDACTED_EMAIL]` 和 `****-****-****-5100` | PASS_LOCAL |
| C Tools | `add(17,25)` 的 `AIMessage.tool_calls` → `ToolMessage('42')` → 最终 AI；日期工具实际返回本地日期；`return_direct` 最后一条为 `ToolMessage` | PASS_LOCAL |
| D ToolError | `divide(1,0)` 执行 1 次；`ZeroDivisionError` 变为 `status='error'` 的 `ToolMessage`；随后有 AI 消息 | PASS_LOCAL |
| E Memory | Alice 线程状态 4 条，另一线程 2 条且没有 Alice | PASS_LOCAL |
| F State / ToolRuntime | `user_123` 在 State、工具执行与 ToolMessage 中；模型可见工具 schema 无 `runtime` 参数 | PASS_LOCAL |
| G Trim / Summary | Trim 8 → 5，保留 `old-add` 的 AI Tool Call 与 ToolMessage；摘要保留 Python generators、短例子偏好和最近提问 | PASS_LOCAL |
| H HITL | 安全读取不触发中断；SQL 提议产生 v2 interrupt，批准前 0 执行、批准后 1 次模拟执行；拒绝不增加执行次数 | PASS_LOCAL |
| I Skill | 首轮模型视图无 `LESSON_PLAN_SEQUENCE`；`load_skill(ai_teacher)` 后工具结果和第二轮视图才含该标记 | PASS_LOCAL |

确定性测试：`7 passed`，覆盖工具函数/schema/执行、错误转换、无 LLM 线程隔离、State/ToolRuntime、Trim 配对、HITL 策略和 Skill 按需加载。自然语言最终回答不做逐字比较。

## 运行中发现并修复

1. Qwen3 最初有时只生成解释或不完整的文本工具调用，未产出结构化 `tool_calls`。C 的用户提示补充 `/no_think` 后，实际工具调用通过。Qwen3 的 `<think>` 文本仍可能较长；本实验以结构化消息与真实工具执行为判断依据。
2. `ToolRuntime` 的原始 `args_schema.model_json_schema()` 无法生成 JSON schema，因为运行时参数包含不可序列化的 callable。改为检查给模型使用的 `tool_call_schema`，实际工具调用通过。
3. H 使用 Qwen3 时出现不可解析的工具调用，Phi-4-mini 直接回答而未调用工具；改用已缓存的 qwen2.5-0.5b 后，安全、批准、拒绝路径均实际通过。
4. I 在自由工具选择下，小模型会直接回答，跳过 `load_skill`。本教学请求在首轮设置 `tool_choice="required"`，并把参数限制为 `Literal["ai_teacher"]`，从而稳定验证逐步加载。它不证明模型在任意任务中都能自主挑选 Skill。

## E2E 结果与边界

统一入口 `scripts/verify_all.py` 顺序复跑 A–I 与确定性测试；只有进程退出码为 0 且每项实际运行标记出现时才允许打印 `03_AGENT_PASS_LOCAL`。

**最终状态：PASS_LOCAL。** 统一入口退出码 `0`，输出 `03_AGENT_PASS_LOCAL`。Environment、Local Tool-capable Model、Deterministic Tests 及 A–I 所有核心检查均为 `PASS`。

Blocker：无。`InMemorySaver` 只在当前进程保存状态；本章没有验证持久化存储、真实 SQL、云模型、生产级权限或任意任务的 Skill 自主发现。
