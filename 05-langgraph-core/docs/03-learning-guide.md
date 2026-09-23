# 05 学习指南：逐段看见 Graph 执行

在 `05-langgraph-core` 目录，以下命令使用同一个本地虚拟环境：

```powershell
& .\.venv\Scripts\python.exe src\stage_a_minimal_graph.py
```

把文件名依次换成 B–K。每段都由源码断言确认实际执行结果；`scripts/verify_all.py` 可一次重跑全部。

## A — Minimal StateGraph

**Concept**：`StateGraph` 是构建器，`compile()` 产出可执行的 `CompiledStateGraph`。**Architecture**：START → step_a → step_b → END。**Code**：`builder.add_edge(...)` 与 `graph.invoke({"text": "START"})`，见 `src/stage_a_minimal_graph.py`。**Run**：运行该文件。**Observed Result**：顺序 `A,B`，最终 `START -> A -> B`，`MINIMAL_GRAPH_PASS`。**Why**：固定边明确连接节点；构建器本身并不执行。

## B — State boundaries

**Concept**：输入、内部、输出 schema 可以不同；节点只返回它修改的键。**Architecture**：InputState → prepare (`working_text`) → process (`graph_output`) → OutputState。**Code**：`StateGraph(OverallState, input_schema=InputState, output_schema=OutputState)`，见 `src/stage_b_state_boundaries.py`。**Run**：运行 B。**Observed Result**：输入 `"  langgraph  "`，局部更新依次为 `working_text=langgraph`、`graph_output=LANGGRAPH`，外部仅收到 `{"graph_output":"LANGGRAPH"}`。**Why**：局部更新避免每个节点重建完整状态，输出 schema 隔离内部字段。

## C — Reducer and messages

**Concept**：默认字段后写覆盖；`Annotated[list, operator.add]` 聚合；`MessagesState` 为 messages 使用 `add_messages`。**Architecture**：first → second，另一个图 HumanMessage → reply。**Code**：`AggregationState.values` 与 `CustomMessageState.messages`，见 `src/stage_c_reducers.py`。**Run**：运行 C。**Observed Result**：`values=[10,20]`、`status=B`，两种消息 schema 均有 HumanMessage 与 AIMessage，`REDUCER_PASS`。**Why**：并行节点写同一键时必须定义合并语义；消息 reducer 还理解 message ID 等消息操作。

## D — State, Context, Config

**Concept**：State 是可更新业务数据，Runtime Context 是本次调用的只读依赖，Config 控制执行。**Architecture**：`greet(state, runtime, config)` 读取 `user_id` 与 `recursion_limit`。**Code**：`StateGraph(MessageState, context_schema=RunContext)`，见 `src/stage_d_runtime_context.py`。**Run**：运行 D。**Observed Result**：节点读到 `user-123` 与 `10`，只返回 `message=hello user-123`；`user_id` 不在 State。**Why**：把运行身份与执行上限混入 State 会污染业务状态。

## E — Conditional routing and loops

**Concept**：普通 Edge 总走；Conditional Edge 按 State 选目的地，也可返回前面的节点。**Architecture**：正负分支；increment 回到自身直到 count=3。**Code**：`add_conditional_edges` 和 `config={"recursion_limit":4}`，见 `src/stage_e_routing_loop.py`。**Run**：运行 E。**Observed Result**：5→positive、-5→negative、0→3；故意无限循环触发 `GraphRecursionError`。**Why**：图允许回边，所以 LangGraph 不是只能执行 DAG；递归上限防止失控。

## F — Runtime policies

**Concept**：Cache 复用结果，Retry 重试可恢复异常，Error Handler 处理最终失败。**Architecture**：三个独立小图，第三个在两次失败后 goto fallback。**Code**：`CachePolicy`、`RetryPolicy`、`NodeError` 与 handler 返回的 `Command`，见 `src/stage_f_runtime_policies.py`。**Run**：运行 F。**Observed Result**：同输入两次函数只执行一次；retry 尝试 `[1,2,3]`；handler 在 `[1,2]` 后转 fallback。**Why**：Retry 和 handler 的触发时机不同，handler 在重试耗尽后接手。若缓存节点依赖 Runtime Context，默认 cache key 只基于节点输入，可能把不同用户的结果混用；应把影响结果的 context 纳入自定义 key，或禁用该缓存。本实验缓存节点只依赖 number。

## G — Send fan-out and fan-in

**Concept**：`Send` 运行时创建多个不同输入的任务；Conditional Edge 通常只选择路径。**Architecture**：fan_out → 三个 process(subject) → END。**Code**：`[Send("process", {"subject": subject}) ...]` 和 `results: Annotated[list[str], operator.add]`，见 `src/stage_g_send.py`。**Run**：运行 G。**Observed Result**：A/B/C 各执行一次，三个结果全在 State，`SEND_FANOUT_PASS`。**Why**：动态 Map-Reduce 的 map 任务数由输入决定，reducer 安全汇合并行写入；测试按集合比较，不假设顺序。

## H — Command

**Concept**：一个节点可用 `Command(update=..., goto=...)` 同时更新 State 和路由。**Architecture**：decide → pass_node 或 fail_node。**Code**：`src/stage_h_command.py` 中 score≥60 返回 pass 的 Command。**Run**：运行 H。**Observed Result**：80 到 pass，40 到 fail；目的节点看到了更新后的 result。**Why**：当节点自己决定后继且必须同时更新状态时 Command 简洁；可独立表达的路由规则仍适合 Conditional Edge。

## I — Subgraph

**Concept**：图可以被父图作为一个步骤调用。**Architecture**：parent_step → child wrapper → 子图 sub_step；父子 State 都有追加型 `log`。**Code**：`child.invoke({"log": []})`，只把子图新增日志返回给父 reducer，见 `src/stage_i_subgraph.py`。**Run**：运行 I。**Observed Result**：`["parent","subgraph"]`，每项一次。**Why**：直接将父 `log` 传入子图再将完整子图 `log` 追加回父图，会把 parent 重复一次。父子 schema 不同时也用 wrapper 显式转换输入/输出，而不假设自动共享所有键。

## J — Streaming

**Concept**：`invoke()` 给最终 State；`stream()` 暴露执行过程。**Architecture**：increment → double。**Code**：`graph.stream(..., stream_mode=...)` 与节点内 `get_stream_writer()`，见 `src/stage_j_streaming.py`。**Run**：运行 J。**Observed Result**：updates 是 `increment:2`、`double:4` 的局部更新；values 是 `1,2,4` 的完整快照；custom 是 `progress=doubling`；tasks 包含两个节点的任务事件。**Why**：选 `updates` 看谁改了什么，选 `values` 看每一步全状态；custom 由应用定义。无 LLM，所以不做 messages stream；无 checkpointer，所以不把 checkpoints 当本章门槛。

## K — Integrated graph and Mermaid

**Concept**：将 State、reducer、固定/条件边、Send、stream 与图导出组成一个可追踪闭环。**Architecture**：normalize → fast 或动态 worker → finalize → END。**Code**：`src/stage_k_final_graph.py` 中 `build_graph()`、`initial_state()` 和 `draw_mermaid()`。**Run**：运行 K。**Observed Result**：`Hello`→`fast:hello`；`A,B,C`→三个聚合结果；X/Y 的 stream 出现 normalize、两个 worker、finalize；真实 compiled graph 写出 `docs/final-graph.mmd`。**Why**：从输入到可执行图、局部更新、路由与最终输出都经过真实运行，不需要图片 renderer 或 LLM。

## 概念速查

| 问题 | 简答 |
| --- | --- |
| 为什么不是 DAG-only？ | E 的回边运行到 count=3。 |
| StateGraph 与 CompiledStateGraph？ | 前者构建，后者执行。 |
| Node 为何返回 Partial State？ | 只声明改变的字段，合并交给状态通道。 |
| Reducer 是什么？ | 指定同一状态键的合并函数。 |
| MessagesState 做了什么？ | 内建带 `add_messages` 的 messages 通道。 |
| State 与 Runtime Context？ | 前者节点可更新，后者每次运行只读。 |
| 普通 Edge 与 Conditional Edge？ | 前者固定后继，后者按状态选择。 |
| Send 是什么、为何适合 Map-Reduce？ | 创建不同输入的运行时任务；结果经 reducer 汇合。 |
| Command 与 Conditional Edge？ | Command 在节点返回值中合并 update/goto；条件边单独路由。 |
| Subgraph 是什么？ | 在父图步骤中调用另一个已编译图。 |
| values 与 updates？ | 全状态快照与节点局部更新。 |
| Retry 与 Error Handler？ | 先重试，仍失败才交给 handler。 |
| Cache key 与 Context？ | 缓存必须区分所有会影响结果的输入，包括适用时的 context。 |
