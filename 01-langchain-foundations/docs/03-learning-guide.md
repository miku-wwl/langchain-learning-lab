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
