# LangChain 01：从模型调用到 Agent Loop

这份指南按真实实验顺序学习。先在 [README](../README.md) 中完成本地环境准备，再从 Stage A 顺序运行。原始课程范围见 [01 教程](../../doc/01.LangChain_v1.4_架构解读与学习路线.md)，知识点与原文代码处理见 [syllabus analysis](01-syllabus-analysis.md)。

## 先建立心智模型

| 层 | 解决的问题 |
| --- | --- |
| Model | 接收消息并产生回复或工具调用请求；它本身不执行 Python 函数。 |
| LangChain `create_agent` | 提供模型、工具、提示词、Middleware 与状态周围的 Agent Loop。 |
| LangGraph | 用 State、Node、Edge 显式描述和运行流程；`create_agent` 也以它为运行基础。 |
| MCP | 规定外部工具如何被发现、描述和调用；`MCPAdapter` 把 MCP 工具接入 LangChain。 |
| Deep Agents | 在普通 Agent 之上组合规划、文件系统、子 Agent 等较完整能力；本课程只认识其定位。 |
| LangSmith | tracing、debug、dataset、evaluation、monitoring 平台；本地代码运行不依赖它。 |

这里的 **Agent = Model + Harness**：模型决定下一步，Harness 把消息、工具调用与结果组织成循环。下面先手工写出循环，再看框架封装。

## Stage A — Model、`invoke`、`ainvoke`、stream

**Concept**：LangChain 的 Chat Model 接受文本或消息并返回 `AIMessage`。同步、异步和流式调用是同一个模型接口的不同执行方式。

**Architecture**：`User → ChatOpenAI 适配器 → Foundry Local /v1 → 本地 Qwen3-4b → AIMessage`。`model_factory.py` 从 Foundry CLI 发现动态端口和已加载模型 ID，学习代码只依赖 LangChain 模型对象。

**Code**（[完整代码](../src/stage_a_model.py)）：

```python
model = create_local_model()
reply = model.invoke("Say hello in one short sentence.")
initialized = init_chat_model(model_id, model_provider="openai", base_url=base_url, api_key="local")
initialized_reply = initialized.invoke("Reply with one short greeting.")
async_reply = await model.ainvoke("Say your name in one short sentence.")
chunks = list(model.stream("Write a short greeting."))
```

**Run**：`.venv\Scripts\python.exe src\stage_a_model.py`

**Result**：Qwen3-4b 的同步、异步和流式调用均返回非空内容；本次流式输出有 `STREAM_CHUNKS=194`。当前 Foundry Local 会把部分 `<think>` 文本放入原始回复，短输出上限可能截断最终句子。

**Why**：后面换成其他本地模型、端点或获批准的 provider 时，Agent 上层调用方式可保持一致。流式片段不是完整回复，应用需要逐片段合并或展示。

## Stage B — Prompt 与 Messages

**Concept**：`ChatPromptTemplate` 把变量变成有角色的消息。System 消息表达规则，Human 消息表达用户输入；模板本身不访问模型。

**Architecture**：`{language, text} → ChatPromptTemplate → [SystemMessage, HumanMessage] → Model → AIMessage`。

**Code**（[完整代码](../src/stage_b_prompt.py)）：

```python
template = ChatPromptTemplate.from_messages([
    ("system", "Translate the following from English into {language}."),
    ("user", "{text}"),
])
prompt = template.invoke({"language": "Chinese", "text": "Hello, how are you?"})
reply = create_local_model().invoke(prompt)
```

**Run**：`.venv\Scripts\python.exe src\stage_b_prompt.py`

**Result**：模板产生 System/Human 两条消息；本地模型返回非空内容。测试还验证缺少 `language` 时会报缺少模板变量。Qwen3-4b 的短输出上限可能只显示其 `<think>` 段，因此本阶段以模板展开和真实调用为主要证据。

**Why**：Prompt 与 Model 是两步。看清模板展开后的 Messages，才能判断错误来自输入、提示词，还是模型本身。

## Stage C — `@tool`、schema 与 `bind_tools`

**Concept**：`@tool` 把 Python 函数及参数类型转成工具 schema。`bind_tools` 把这个 schema 提供给模型，模型可生成 `tool_calls`；此时 Python 工具还没有被模型自动执行。

**Architecture**：`User → Model(bind_tools) → AIMessage.tool_calls`，停在工具请求处。

**Code**（[工具](../src/tools.py)、[完整 Stage](../src/stage_c_tools.py)）：

```python
@tool
def add(a: int, b: int) -> int:
    """Add two integers and return the sum."""
    return a + b

reply = create_local_model().bind_tools([add]).invoke(
    "Use the add tool to calculate 17 + 25. Return the tool result."
)
print(reply.tool_calls)
```

**Run**：`.venv\Scripts\python.exe src\stage_c_tools.py`

**Result**：直接调用工具返回 `42`；Qwen 的 `tool_calls` 包含 `name='add'`、`args={'a': 17, 'b': 25}`。模型原始文本也出现 `<tool_call>`，程序以解析后的 `tool_calls` 为准。

**Why**：`bind_tools != Agent`。这一阶段只证明模型会请求工具；下一阶段才执行它。

## Stage D — 手工 Tool Loop

**Concept**：收到 `tool_calls` 后，调用方必须派发到正确的 Python 工具，把结果以带相同 `tool_call_id` 的 `ToolMessage` 放回消息序列，再次调用模型。

**Architecture**：

```text
HumanMessage → Model → AIMessage.tool_calls
                         ↓
                    Python add(17, 25)
                         ↓
                  ToolMessage("42")
                         ↓
                      Model → 最终 AIMessage
```

**Code**（[完整代码](../src/stage_d_manual_tool_loop.py)）：

```python
first_reply = model.invoke(messages)
messages.append(first_reply)
for call in first_reply.tool_calls:
    messages.append(dispatch_tool_call(call))
final_reply = model.invoke(messages)
```

**Run**：`.venv\Scripts\python.exe src\stage_d_manual_tool_loop.py`

**Result**：真实调用为 `add(17,25)`，`TOOL_MESSAGE=42`，最终回答包含 `42`；`ADD_EXECUTIONS` 还证实 Python 函数确实执行。

**Why**：LLM Tool Calling 是“请求执行”的消息格式；Agent Runtime 才负责重复执行模型、工具和消息传递，直到形成最终结果。

## Stage E — `create_agent`

**Concept**：`create_agent` 将 Stage D 的手工循环封装为 Agent Harness。输入输出仍是 Messages，工具定义仍是同一个 `add`。

**Architecture**：`HumanMessage → Agent(Model ↔ Tool) → AIMessage`。Agent 内部保留 AI 工具调用和 ToolMessage，便于检查真实执行链。

**Code**（[完整代码](../src/stage_e_agent.py)）：

```python
agent = create_agent(model=create_local_model(), tools=[add])
result = agent.invoke({"messages": [{"role": "user", "content": "Calculate 17 + 25 using add."}]})
```

**Run**：`.venv\Scripts\python.exe src\stage_e_agent.py`

**Result**：输出同时包含 `add` 的 tool call、内容为 `42` 的 ToolMessage 与包含 `42` 的最终回答；执行日志确认 Python 工具运行。

**Why**：Agent 消除了业务代码里的派发循环，但并没有改变“模型请求 → 工具执行 → 工具结果 → 模型回答”的机制。
