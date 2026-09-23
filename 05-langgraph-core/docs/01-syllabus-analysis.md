# 05 教程知识点盘点

唯一 syllabus：[05.LangGraph_v1.2_Core_Graph_更新版.md](../../doc/05.LangGraph_v1.2_Core_Graph_更新版.md)。本章只用本地 Python；无需 LLM、前面章节或外部服务。下表的阶段与 `src/stage_*.py` 对应。

| ID | Markdown 章节 | 知识点 | State | Routing | 并行 | 本地 E2E 证据 |
| --- | --- | --- | --- | --- | --- | --- |
| 01 | 一 | `StateGraph` builder、`compile()`、`CompiledStateGraph`、`invoke()` | 是 | 固定 Edge | 否 | A：类型、执行顺序、最终文本 |
| 02 | 二 | TypedDict State、Node 的 Partial State Update | 是 | 固定 Edge | 否 | A/B：节点只返回更新的字段 |
| 03 | 二.2 | Input / Overall / Output State | 是 | 固定 Edge | 否 | B：输入只需 `user_input`，输出只有 `graph_output` |
| 04 | 三.1 | 普通字段覆盖、`Annotated` reducer | 是 | 固定 Edge | 否 | C：status 覆盖，values 聚合 |
| 05 | 三.2 | `MessagesState`、`add_messages` | 是 | 固定 Edge | 否 | C：HumanMessage 后追加 AIMessage；自定义 reducer 等价 |
| 06 | 四 | `context_schema`、`Runtime`、只读 run context | 是 | 固定 Edge | 否 | D：`user_id` 不进入返回 State |
| 07 | 四.2 | `RunnableConfig`、`recursion_limit` | 是 | 循环 | 否 | D/E：执行配置与业务 context 分离；递归上限阻断错误循环 |
| 08 | 五 | Node 名称与清晰的 Partial Update | 是 | 固定 Edge | 否 | A–K：每个节点职责可见 |
| 09 | 五.2 | `CachePolicy`、`InMemoryCache` | 是 | 固定 Edge | 否 | F：相同输入两次只执行一次函数 |
| 10 | 五.3 | `RetryPolicy` | 是 | 固定 Edge | 否 | F：两次 ConnectionError、第三次成功 |
| 11 | 五.4 | `error_handler`、`NodeError`、`Command` fallback | 是 | 动态 goto | 否 | F：重试耗尽后进入 fallback |
| 12 | 五.5 | `timeout`、`trace_policy`、`set_node_defaults` | 是 | 无 | 否 | F 文档说明及已安装 API 签名核对；无阻塞等待实验 |
| 13 | 六.1 | 普通 Edge、START、END | 是 | 固定 | 否 | A：START → A → B → END |
| 14 | 六.2 | Conditional Edge | 是 | 条件 | 否 | E：正、负两条分支 |
| 15 | 六.3 | Loop；LangGraph 并非 DAG-only | 是 | 回边 | 否 | E：count 0→3；错误循环触发 GraphRecursionError |
| 16 | 七 | `Send`、动态 fan-out、reducer fan-in | 是 | 动态 | 是 | G：A/B/C 三个 Send；结果集合完整 |
| 17 | 八 | `Command(update, goto)` | 是 | 动态 | 否 | H：score 80/40 两条路径 |
| 18 | 九 | Subgraph、共享 schema、不同 schema 的 wrapper | 是 | 嵌套 | 否 | I：父子共用 log 得到 parent/subgraph；wrapper 概念见指南 |
| 19 | 十 | `invoke()` 与 `stream()` | 是 | 固定 | 否 | J：`stream()` 中间事件；A–K 用 `invoke()` 取得最终结果 |
| 20 | 十 | `updates`、`values`、`custom`、`tasks` | 是 | 固定 | 否 | J：逐节点局部更新、完整状态、writer 事件、任务事件 |
| 21 | 十 | `messages`、`checkpoints`、`debug` | 是 | 无 | 否 | 指南说明适用条件；无 LLM、无 checkpointer，因此不作为核心门槛 |
| 22 | 十一 | Mermaid text | 是 | 多路径 | 是 | K：`draw_mermaid()` 保存 `.mmd`，检查节点与边 |
| 23 | 十二至十五 | State/Node/Routing 设计方法和最终工作流 | 是 | 条件 + Send | 是 | K：两条路径、真实 fan-out、最终输出与 stream |

`langgraph` 可独立使用。教程把 Graph 视为 DAG 的旧说法不成立：E 中实际运行回边。Node 返回部分更新，合并语义由字段 reducer 决定。Runtime Context 用于本次调用的只读业务依赖，`RunnableConfig` 用于运行配置。`timeout` 在当前参考中只对可安全取消的异步节点有效，本章只解释，不制造真实等待或外部故障。
