# 03 — LangChain Agent 本地 E2E 学习实验

基于 [03 原教程](../doc/03.LangChain_v1.4_构建简单Agent_更新版.md)，按 A–I 顺序观察 `create_agent`、Agent Loop、Middleware、State、HITL 和 Skill 渐进式加载。本目录独立于 01/02，不依赖云 API、数据库或付费服务。

## 运行架构

```text
User → create_agent / Middleware / Checkpointer
                     ↓
           Foundry Local 聊天模型
                     ↓
       AIMessage.tool_calls → Python Tool
                                ↓
                        ToolMessage → Model
```

默认从本机 `foundry server status` 取得动态 `/v1` 地址，从已加载模型列表取得 ID。A–G 使用 `qwen3-4b`；H/I 的工具选择使用本地 `qwen2.5-0.5b`。两者必须已缓存并加载，且支持工具调用。`LOCAL_OPENAI_BASE_URL` 与 `LOCAL_CHAT_MODEL` 可覆盖默认发现；参见 `.env.example`。

## 准备与运行

在 PowerShell 中：

```powershell
cd D:\workshop\sep\langchain-learning-lab\03-agent
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
foundry model load qwen3-4b
foundry model load qwen2.5-0.5b
.\.venv\Scripts\python.exe -u scripts\verify_all.py
```

若模型已经加载，可跳过两个 `foundry model load`。验证入口运行确定性测试和每个 Stage，只有全部通过才输出 `03_AGENT_PASS_LOCAL`。可逐项运行，如：

```powershell
.\.venv\Scripts\python.exe -u src\stage_c_tools.py
.\.venv\Scripts\python.exe -u src\stage_h_hitl.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

## 目录

| 路径 | 用途 |
| --- | --- |
| `src/stage_a_agent.py` | `create_agent`、system prompt、消息状态 |
| `src/stage_b_streaming_pii.py` | updates/messages Streaming、PII 输入治理 |
| `src/stage_c_tools.py`、`src/tools.py` | 工具 schema、完整 ToolMessage 循环、`return_direct` |
| `src/stage_d_tool_errors.py` | 工具异常转换与非重试语义 |
| `src/stage_e_memory.py` | `InMemorySaver` 与线程隔离 |
| `src/stage_f_state_runtime.py` | 自定义 State 与 ToolRuntime 注入 |
| `src/stage_g_context.py` | Trim 与 Summarization |
| `src/stage_h_hitl.py` | 安全工具、模拟 SQL 的 approve/reject |
| `src/stage_i_skill.py`、`skills/ai_teacher/SKILL.md` | 按需加载 Skill 正文 |
| `tests/test_agent_lab.py` | 无 LLM 的确定性测试 |
| `scripts/verify_all.py` | 完整本地 E2E 验证 |

## 学习资料与结果

- [知识点矩阵](docs/01-syllabus-analysis.md)
- [E2E 设计](docs/02-e2e-design.md)
- [学习指南](docs/03-learning-guide.md)
- [验证报告](docs/04-verification-report.md)

本 Lab 的 SQL 工具只返回 `SIMULATED SQL: ...`，没有数据库连接。HITL 的批准表示教学模拟函数可以执行，不会修改真实数据。
