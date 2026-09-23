# 06 学习指南：从独立 Worker 到两种多 Agent 模式

所有命令从 `06-multi-agent` 目录执行，使用 `& .\.venv\Scripts\python.exe src\stage_a_workers.py`；将文件名换成后续 Stage 即可。`scripts/verify_all.py` 会全部重跑。本章的领域数据全部为 synthetic/simulated，不供真实医疗用途。

## A — Independent Worker Agents

**Concept**：先让每个专家单独完成一件事。**Architecture**：Record、Guideline、Doctor 各有独立 system prompt 和唯一内部工具。**Minimal Code**：`workers.build_workers()` 调用三次 `create_agent`；`invoke_worker()` 检查 AI 工具调用和 ToolMessage。**Run**：`src/stage_a_workers.py`。**Observed Result**：三类工具各执行一次，得到合成记录、笔记和目录，三个 Worker 均 PASS。**Why**：未证明专家自身可用时，增加 Supervisor 只会增加诊断困难。

## B — Deterministic Router

**Concept**：Router 是一次分类，不是 Supervisor。**Architecture**：query → `classify_query` → record/guideline/doctor/refuse。**Minimal Code**：`router.py` 的关键词函数。**Run**：`src/stage_b_router.py`。**Observed Result**：四条查询各落到预期分支。**Why**：先隔离 Graph 路由行为与 LLM 分类波动。

## C — LangGraph Router Workflow

**Concept**：条件边真正进入选中的 Worker Agent。**Architecture**：START → router → 四条分支 → END。**Minimal Code**：`router_graph.build_router_graph` 的 `add_conditional_edges`；节点调用 `invoke_worker`。**Run**：`src/stage_c_router_graph.py`。**Observed Result**：三条领域查询各调用对应底层工具；refuse 不调用任何 Worker。**Why**：只检查 route 字符串不能证明 Worker 执行。

## D — Aggregate Node

**Concept**：把 `worker_result` 到 `final_answer` 做成显式步骤。**Architecture**：router → worker → aggregate → END。**Minimal Code**：`aggregate.aggregate_result` 确定性格式化，不新增模型调用。**Run**：`src/stage_d_aggregate.py`。**Observed Result**：stream updates 依次显示 router、record、aggregate；`final_answer` 为合成结果格式。**Why**：Router 模式的响应格式可以保持可预测。

## E — Subagent-as-Tool

**Concept**：Supervisor 看的是高层能力，Worker 看的是自己的底层工具。**Architecture**：`ask_*_agent(task)` → Worker Agent → 内部工具。**Minimal Code**：`subagent_tools.create_subagent_tools` 返回三个 `@tool`。**Run**：`src/stage_e_subagent_tools.py`。**Observed Result**：高层工具名集合只有三个 `ask_*`，底层工具仍真实执行。**Why**：Tool Namespace Isolation 减少主 Agent 需要选择的工具，并保留 Worker 的专业边界。

## F — Real Supervisor Agent

**Concept**：Supervisor 本身是 `create_agent`，会产生 AIMessage tool_call，等待子 Agent ToolMessage，再给最终回答。**Architecture**：User → Supervisor → ask_* → Worker → 内部 Tool → Supervisor。**Minimal Code**：`supervisor.build_supervisor` 使用三个高层工具；`invoke_supervisor` 提取真实消息证据。**Run**：`src/stage_f_supervisor.py`。**Observed Result**：三条单领域请求分别只调用对应 `ask_*`，且对应底层工具各执行。**Why**：这条完整 Agent Loop 才与单次 Router 分类不同。

## G — Multiple Delegation

**Concept**：一个请求可需要两个专家。**Architecture**：Supervisor → Record → Doctor → synthesis。**Minimal Code**：`src/stage_g_multi_delegate.py` 检查两个不同高层/底层工具及最终两份数据。**Run**：运行 G。**Observed Result**：Record 和 Doctor 顺序调用，最终同时含 2026 模拟记录与 Dr Demo 目录；`MULTI_DELEGATE_PASS`，并行可选。**Why**：多专家正确调用与同轮并行是不同的验收条件。

## H — Context Isolation and Output Filtering

**Concept**：工具名隔离、输入上下文隔离、输出过滤是三件事。**Architecture**：Supervisor 的完整请求 → `ask_record_agent` 只提取 `user_123` → Worker；Worker 的四条内部消息 → 只返回经工具数据核对的简洁字符串。**Minimal Code**：`subagent_tools.capture` 记录 `worker_task`、内部消息类型和 `returned`；`router_graph.scoped_task` 规范化参数。**Run**：`src/stage_h_context_isolation.py`。**Observed Result**：主请求里的无关 canary/weather/directory 不在 Worker task；Supervisor ToolMessage 只含 `SYNTHETIC RECORDS`，不含 ToolMessage/调用轨迹。**Why**：只把完成子任务所需信息送入独立窗口，同时控制返回主上下文的信息量。

## I — Failure Isolation

**Concept**：无数据和工具执行失败必须有不同语义。**Architecture**：`user_missing` 返回 `NO_DATA`；`simulate_failure` 使 Doctor 内部工具抛异常，由 `ask_doctor_agent` 捕获为 `DOCTOR_AGENT_ERROR: RuntimeError`。**Minimal Code**：`tools.find_demo_doctors` 的模拟失败分支与 `subagent_tools` 异常边界。**Run**：`src/stage_i_failure_isolation.py`。**Observed Result**：跨域请求中 Record 成功、Doctor 失败，Supervisor 最终分别报告两者。**Why**：一个 Worker 的异常不能被伪装为没有数据，也不应污染另一个 Worker 的结果。

## J — Router vs Supervisor

**Concept**：两种模式适合不同控制需求。**Architecture**：同一单域及跨域请求分别运行 Pattern A/B。**Minimal Code**：`src/stage_j_compare.py`；完整维度见 [实测对比](router-vs-supervisor.md)。**Run**：运行 J。**Observed Result**：单域都能完成；跨域 Router 只走 Record，Supervisor 走 Record + Doctor。**Why**：若需确定性分发/固定格式，Router 更简单；若需动态组合专家，Supervisor 更合适。少量简单工具时单 Agent 也可能更省成本；复杂固定流程可直接用 Custom Workflow。

## 关键问题速答

| 问题 | 答案 |
| --- | --- |
| 为什么分类节点不是 Supervisor？ | 它只决定一次去向，不持续协调工具和结果。 |
| Router / Supervisor / Subagent 是什么？ | 一次分流 / 持续协调的 Agent / 拥有独立 Prompt、Tool、上下文的专家。 |
| 为什么把子 Agent 包成 Tool？ | 主 Agent 只看高层能力，调用接口稳定，内部细节隔离。 |
| 为什么不把所有底层 Tool 给 Supervisor？ | 增加选择负担且暴露不相关细节。 |
| Subagent spec/input/output 怎么设计？ | 清楚的名称与描述；任务所需最少输入；只返回可用最终结果。 |
| Tool Namespace 与 Context Isolation 区别？ | 前者限制可见工具集合；后者限制送入 Worker 的消息和数据。 |
| Output Filtering 又是什么？ | Worker 内部消息/轨迹不回流，只回经工具数据核对的简洁结果。 |
| 多 Agent 一定更好吗？ | 否；单 Agent 在少量清晰 Tool 场景更简单、通常更省调用。 |
| Router / Supervisor / Custom Workflow 怎么选？ | 固定单域分流 / 动态多专家协调 / 强制顺序与确定性控制。 |
| 并行何时有意义？ | 独立子任务可同时运行且本地模型/运行时能稳定发多工具调用时。 |
| 为什么隔离失败？ | 区分 NO_DATA 与 EXECUTION_ERROR，同时保留其他 Worker 的成功结果。 |

本地模型选择也有教学价值：`qwen3-4b` 初次未产出结构化 tool_calls，强制工具后最终答案误报无数据；`phi-4-mini` 在本章经首轮工具约束后完成链路。首轮工具约束用于要求 Worker 的真实工具调用；输出过滤从 ToolMessage 的合成 JSON 生成可信结果，避免把模型追加的无据细节传给 Supervisor。
