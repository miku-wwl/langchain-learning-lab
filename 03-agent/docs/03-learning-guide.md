# 03 LangChain Agent：从模型调用到可验证的 Agent Harness

本章按 [原教程](../../doc/03.LangChain_v1.4_构建简单Agent_更新版.md) 的概念顺序运行 A–I。每个 `src/stage_*.py` 都可单独执行；完整入口是 `python scripts/verify_all.py`。这里的 Agent 指 `create_agent()` 建立的运行循环，而不是给模型绑定几个函数就结束。

```text
User → Agent Harness（prompt、消息、middleware、checkpointer、HITL）
                   ↓
              本地聊天模型
                   ↓
        AIMessage(tool_calls) 或最终回答
                   ↓
         Tool 执行 → ToolMessage → 再次调用模型
```

模型提出工具调用及其参数；Harness 保存状态、调度工具、把结果送回模型，也在生命周期钩子上运行 Middleware。Tool 是普通 Python 代码，结果是否正确由代码决定。`bind_tools()` 只告诉模型工具 schema，不负责完整的循环、执行、状态或中断。

## A — `create_agent` 与消息状态

**Concept / Architecture**：`create_agent(model, tools, system_prompt)` 包装一次或多次模型调用，返回含 `messages` 的 Agent State。系统提示与用户消息分别进入模型。

**Minimal Code**：`src/stage_a_agent.py` 使用 `@wrap_model_call` 捕获 `request.system_message`，然后调用无工具 Agent。

**Run**：`python src/stage_a_agent.py`。

**Observed Result / Why**：本地模型返回 `HumanMessage → AIMessage`；捕获到的系统提示与设置值一致。它证明提示进入模型请求，而非只存在于调用方变量。

## B — Streaming 与 PII Middleware

**Concept / Architecture**：`stream_mode="updates"` 给节点状态更新，`stream_mode="messages"` 给消息流片段；二者观察同一 Agent 循环的不同侧面。`PIIMiddleware` 在模型调用前处理输入。

**Minimal Code**：`src/stage_b_streaming_pii.py` 分别消费两种流；把假的邮箱与卡号送入 Agent，再从 `@wrap_model_call` 捕获模型实际看到的文本。

**Run**：`python src/stage_b_streaming_pii.py`。

**Observed Result / Why**：两种流都有事件；模型前文本中邮箱是 `[REDACTED_EMAIL]`，卡号只保留末四位。断言比较的是送往模型的输入，不是模型回答里是否重述敏感文本。
