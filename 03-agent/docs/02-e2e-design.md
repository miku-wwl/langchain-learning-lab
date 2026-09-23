# 03 Agent 本地 E2E 设计

03 独立使用自己的 `.venv`、模型工厂、工具、Stage、Skill、测试和验证入口。聊天模型走本机 Foundry Local `127.0.0.1`；不需要云 API、数据库或其他章节运行。

```text
User → Agent Harness(prompt / middleware / state / checkpointer / HITL)
                       ↓
                Local Tool-capable Model
                       ↓
                 AIMessage.tool_calls?
                    ├─ no → final AIMessage
                    └─ yes → Harness executes Python Tool
                                   ↓
                              ToolMessage → Model
```

| Stage | 输入 | 必须看见 | PASS_LOCAL 条件 |
| --- | --- | --- | --- |
| A Agent | 简单问题 | HumanMessage、AIMessage、system_prompt | 本地 `create_agent` 真实调用，消息状态完整 |
| B Streaming + PII | 简单问题；含假 email/卡号的文本 | updates/messages 事件；模型前输入 | 流事件非空，敏感原文在送模型前已处理 |
| C Tools | 日期与 `add(17,25)` | tool_calls、执行计数、ToolMessage、最终 AI | 确实执行工具并返回结果；展示 `return_direct` |
| D Tool Error | `divide(1,0)` | 原始异常、error ToolMessage、后续回答 | Middleware 捕获指定异常；不误称为 retry |
| E Memory | Alice 两轮与独立线程 | checkpoint messages | 同线程读到 Alice，新线程没有其历史 |
| F State / ToolRuntime | `user_id=user_123` | State、注入 runtime、tool schema | 工具读取真实 State，user_id 不由模型猜测 |
| G Trim / Summary | 多轮短消息 | 裁剪/摘要前后消息 | Trim 减少消息数，Summary 保留要点和近期消息 |
| H HITL | read_data；模拟 execute_sql | 安全直行、中断、approve/reject | 危险工具批准前零执行，拒绝零执行，批准仅模拟执行 |
| I Skill | AI 课程请求 | 摘要 → load_skill → 完整内容 | 首轮要求工具选择，模型调用 `load_skill` 后才读取 `SKILL.md`，下一轮模型视图包含正文 |

每个 Stage 先运行自身，再进入下一阶段。确定性检查放在 `tests/`；`scripts/verify_all.py` 重新顺序执行 A–I，只有所有核心标记及进程退出码都通过才输出 `03_AGENT_PASS_LOCAL`。若模型最终措辞改变，校验消息结构、工具执行、状态、审批边界和关键事实，不比较整句文本。H/I 使用已缓存的 qwen2.5-0.5b，以提高结构化工具调用稳定性；I 的首轮 `tool_choice="required"` 只用于本教学请求，不代表模型能在任意任务中自主判断 Skill。
