# Router 与 Supervisor：同一请求的实测对比

本章仅使用合成记录、合成指南笔记与合成医生目录。Stage J 将**同一个**单领域请求和跨领域请求分别送进两种模式，而不是只画架构图。

| 维度 | Pattern A：Router Graph | Pattern B：Supervisor Agent |
| --- | --- | --- |
| 控制方式 | 一次确定性分类，固定 Graph 边 | `create_agent` 持续 ToolMessage loop |
| 路由 | `classify_query` 选择一条条件边 | 模型根据高层工具描述决定委派 |
| 单领域请求 | Record Agent 一次，内部 `get_history_records` 一次 | `ask_record_agent` 一次，再进入 Record Agent 与内部工具 |
| 跨领域请求 | 因 `history` 优先级只走 Record；Doctor 未运行 | 先后调用 `ask_record_agent` 和 `ask_doctor_agent`，两份结果都进入最终回答 |
| Worker 数 | 本示例每请求恰好一个 | 本示例可为一个或两个 |
| 上下文所有者 | Graph State 存 query/route/result/final | Supervisor 持有主消息；Wrapper 给 Worker 明确 task |
| 多 Worker 支持 | 需要显式扩展路由/并行图 | 模型可多次调用高层工具；本机观察到顺序调用 |
| 可预测性 | 分类规则和 Aggregate 格式确定 | Tool 选择和自然语言综合受本地模型影响 |
| 模型依赖 | Router 本身不需 LLM；Worker 仍需本地 LLM | Supervisor 与 Worker 都需本地 tool-capable LLM |
| 调试 | 看 Graph update：router → worker → aggregate | 看 AIMessage.tool_calls、ToolMessage、内部工具计数 |
| token/运行时间 | 仅 Worker 的模型调用 | 额外 Supervisor 模型轮次；跨域调用更多 Worker |
| 适用任务 | 清晰、单领域、固定格式 | 跨领域、动态委派与综合 |

**观察**：单领域请求两个模式都返回记录；跨领域请求 Router 只调用 `get_history_records`，Supervisor 依次调用 `get_history_records` 和 `find_demo_doctors`，最终包含 2026 模拟记录与 Dr Demo 目录。并行 delegation 未观察到，因此标为可选。

Router 回答“这个任务交给谁？”。Supervisor 回答“需要哪些专家、如何调用、如何综合？”。两者按需求选择；本章不把一次分类节点称作 Supervisor。需要强制多 Worker、确定性验证或固定顺序时，直接写 LangGraph Custom Workflow 更清晰。
