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

## C — Tool Calling 与 Agent Loop

**Concept / Architecture**：`@tool` 产生名称、描述和参数 schema。模型只给出 `AIMessage.tool_calls`；Harness 执行 Python 函数，生成 `ToolMessage`，再让模型产生最终 `AIMessage`。

```text
HumanMessage → AIMessage(tool_calls=[add]) → add(17,25)
             → ToolMessage("42") → AIMessage(final)
```

**Minimal Code**：`src/tools.py` 定义 `add`、`get_current_date` 和 `echo_direct`；`src/stage_c_tools.py` 打印消息类型、调用参数、工具返回及最终消息。

**Run**：`python src/stage_c_tools.py`。

**Observed Result / Why**：`add(17,25)` 实际执行并返回 42；日期工具返回本地日期。`echo_direct` 的 `return_direct=True` 使最后一条成为 `ToolMessage`，省去工具之后的模型回答。普通工具结果不会自动成为最终答复，`return_direct` 才会改变循环终止方式。

## D — Tool Error Middleware

**Concept / Architecture**：`divide(1,0)` 抛出 `ZeroDivisionError`，`ToolErrorMiddleware` 转成 `status="error"` 的 `ToolMessage`，Agent 继续解释。

**Minimal Code**：`src/stage_d_tool_errors.py` 中 `on_tool_error` 生成简短错误文本。

**Run**：`python src/stage_d_tool_errors.py`。

**Observed Result / Why**：工具尝试一次、错误处理一次、Agent 又生成 AI 消息。**错误处理**把失败交给模型；**重试**会再执行工具。本例没有装 `ToolRetryMiddleware`，所以零除不会重复运行。

## E — Short-term Memory

**Concept / Architecture**：`InMemorySaver` 按 `thread_id` 保存 State。模型自身不会自动拥有之前调用的上下文。

**Minimal Code**：`src/stage_e_memory.py` 在 `thread-a` 告诉 Agent 用户名 Alice，再问名字；在另一线程单独提问，并检查 `get_state()` 的消息列表。

**Run**：`python src/stage_e_memory.py`。

**Observed Result / Why**：第一线程有四条消息且包含 Alice；第二线程只有自己的两条消息，没有 Alice。自然语言回答也被显示，但状态检查才是隔离的主要证据。

## F — Agent State 与 ToolRuntime

**Concept / Architecture**：`CustomState(AgentState)` 添加 `user_id`；`ToolRuntime` 把当前 State 注入工具，模型的工具 schema 不包含 `runtime` 参数。

**Minimal Code**：`src/stage_f_state_runtime.py` 的 `get_user_info(runtime)` 读取 `runtime.state["user_id"]`。

**Run**：`python src/stage_f_state_runtime.py`。

**Observed Result / Why**：输入的 `user_123` 出现在 Agent State、工具执行记录和 `ToolMessage` 中；模型没有自行生成此 ID。

| 概念 | 生命周期 | 用途 |
| --- | --- | --- |
| State | 当前 thread 的可变运行状态 | messages、计数器、这里的 `user_id` |
| Context | 单次 invoke 的只读上下文 | 请求级身份或配置，不进消息状态 |
| Store | 跨 thread 的共享长期数据 | 用户偏好、长期记忆 |
| `thread_id` | Checkpointer 的会话键 | 选择哪段短期历史 |
| `user_id` | 业务身份 | 可在多个 thread 中相同 |

`thread_id` 与 `user_id` 有不同职责；本例只演示 State 注入，不实现 Store。
