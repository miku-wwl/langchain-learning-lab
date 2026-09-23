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

**Architecture**：`User → ChatOpenAI 适配器 → Foundry Local /v1 → 本地 Phi-4-mini → AIMessage`。`model_factory.py` 从 Foundry CLI 发现动态端口和已加载模型 ID，学习代码只依赖 LangChain 模型对象。

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

**Result**：真实运行得到 `INVOKE=Hello!`、`init_chat_model` 的非空回复、`AINVOKE=I am Phi, an advanced digital assistant.`、`STREAM_CHUNKS=12`。

**Why**：后面换成 Qwen、其他本地端点或获批准的 provider 时，Agent 上层调用方式可保持一致。流式片段不是完整回复，应用需要逐片段合并或展示。

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

**Result**：模板产生 System/Human 两条消息；本地模型回复 `你好，怎么样?`。测试还验证缺少 `language` 时会报缺少模板变量。

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

reply = create_local_model("qwen2.5-0.5b").bind_tools([add]).invoke(
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
agent = create_agent(model=create_local_model("qwen2.5-0.5b"), tools=[add])
result = agent.invoke({"messages": [{"role": "user", "content": "Calculate 17 + 25 using add."}]})
```

**Run**：`.venv\Scripts\python.exe src\stage_e_agent.py`

**Result**：输出同时包含 `add` 的 tool call、内容为 `42` 的 ToolMessage 与包含 `42` 的最终回答；执行日志确认 Python 工具运行。

**Why**：Agent 消除了业务代码里的派发循环，但并没有改变“模型请求 → 工具执行 → 工具结果 → 模型回答”的机制。

## Stage F — State、Checkpointer 与短期记忆

**Concept**：Agent State 存储 Messages；Checkpointer 按 `thread_id` 保存执行状态。下次相同线程的输入会接在已保存消息之后。`InMemorySaver` 只在当前进程中保存状态。

**Architecture**：`thread_id → Checkpointer → Agent State.messages → Model`。

**Code**（[完整代码](../src/stage_f_memory.py)）：

```python
saver = InMemorySaver()
agent = create_agent(model=create_local_model(), tools=[], checkpointer=saver)
config = {"configurable": {"thread_id": "alice-thread"}}
agent.invoke({"messages": [{"role": "user", "content": "My name is Alice."}]}, config=config)
second = agent.invoke({"messages": [{"role": "user", "content": "What is my name?"}]}, config=config)
saved = agent.get_state(config).values["messages"]
```

**Run**：`.venv\Scripts\python.exe src\stage_f_memory.py`

**Result**：`TURN_2=Alice`，新线程 `NEW_THREAD=UNKNOWN`；检查点中分别有 4 条与 2 条消息。

**Why**：记忆来自已保存的消息状态，而不是模型参数被改写。换 `thread_id` 即换一条会话；跨线程用户资料属于另一类长期记忆，不由这个示例解决。

## Stage G — Middleware 与 Structured Output

**Concept**：Middleware 可在运行时影响 Agent 行为。本例 `@dynamic_prompt` 在模型调用前生成 System 提示。`ToolStrategy(Person)` 请求模型按 Pydantic schema 返回结构化对象。

**Architecture**：`User → Middleware → Agent Model → schema tool call → validated Person`。

**Code**（[完整代码](../src/stage_g_extensions.py)）：

```python
@dynamic_prompt
def teaching_prompt(request: ModelRequest) -> str:
    return "Answer the user briefly."

structured_agent = create_agent(
    model=create_local_model("qwen2.5-0.5b"),
    tools=[],
    response_format=ToolStrategy(Person),
)
person = structured_agent.invoke({"messages": [{"role": "user", "content": "Alice is 30 years old."}]})["structured_response"]
```

**Run**：`.venv\Scripts\python.exe src\stage_g_extensions.py`

**Result**：`MIDDLEWARE_CALLS=[1]`，`STRUCTURED_RESPONSE=name='Alice' age=30`。

**Why**：Middleware 改变 Harness 的行为；Structured Output 将结果交给 schema 校验。这里没有扩展成复杂策略系统。

## Stage H — 最小 LangGraph

**Concept**：LangGraph 把状态更新和控制流显式表示。Node 接收当前 State 并返回更新，Edge 指定下一个 Node。`compile()` 生成可运行图，`invoke()` 执行。

**Architecture**：`START → increment → double → END`，初始 `value=20`，先加 1 再乘 2。

**Code**（[完整代码](../src/stage_h_graph.py)）：

```python
builder = StateGraph(NumberState)
builder.add_node("increment", increment)
builder.add_node("double", double)
builder.add_edge(START, "increment")
builder.add_edge("increment", "double")
builder.add_edge("double", END)
result = builder.compile().invoke({"value": 20, "visited": []})
```

**Run**：`.venv\Scripts\python.exe src\stage_h_graph.py`

**Result**：`{'value': 42, 'visited': ['increment', 'double']}`。`visited` 使用 reducer 累积两个节点的更新。

**Why**：普通 Python 函数适合固定、短小的流程；LangChain Agent 适合让模型选择工具并循环；LangGraph 适合需要显式状态、分支和恢复的流程。本例只验证图的基本构造，深入内容留给 05 阶段。

## Stage I — 本地 MCP Server

**Concept**：MCP Server 暴露工具，`MCPAdapter` 发现并转成 LangChain Tool，Agent 再按正常 Tool Loop 执行。MCP 不替代 Agent。

**Architecture**：`LangChain Agent → MCPAdapter → 本地 stdio FastMCP 子进程 → add → ToolMessage → Agent`。

**Code**（[Server](../src/mcp_server.py)、[完整 Stage](../src/stage_i_mcp.py)）：

```python
async with MCPAdapter(Path("src/mcp_server.py")) as adapter:
    tools = await adapter.list_tools()
    agent = create_agent(model=create_local_model("qwen2.5-0.5b"), tools=tools)
    result = await agent.ainvoke({"messages": [{"role": "user", "content": "Use add to calculate 17 + 25."}]})
```

**Run**：`.venv\Scripts\python.exe src\stage_i_mcp.py`

**Result**：发现 `['add']`；Agent 产生 `add(17,25)`，来自 MCP Server 的 ToolMessage 文本为 `42`，最终回答包含 `42`。运行时会看到 `langchain.mcp` beta 警告。

**Why**：直接 LangChain Tool 与 MCP Tool 进入 Agent 后很相似；MCP 增加的是独立工具服务和协议边界。这里用本地进程完整验证，后续 04 阶段再深入 MCP。

## Stage J — LangSmith 与下一步

LangSmith 可以记录 trace，建立 dataset 和 evaluation，并观察运行中的 Agent。本 Lab 没有设置 `LANGSMITH_API_KEY` 或 tracing，状态是 **OPTIONAL / NOT REQUIRED FOR LOCAL E2E**。运行 Agent 与观察 Agent 是不同层；这里先把本地行为跑通。

原教程也提到 Deep Agents、HITL、Interrupt、Persistence、Long-term Memory。这些在 01 中只需认清位置，不展开实现。完成本页后可用 `.venv\Scripts\python.exe scripts\verify_all.py` 重跑完整链路，并查看 [verification report](04-verification-report.md)。
