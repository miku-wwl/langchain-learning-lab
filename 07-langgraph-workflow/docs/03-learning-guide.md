# 07 学习指南

阅读顺序：Concept → Architecture → Code → Run → Observed Result → Why。所有命令在 `07-langgraph-workflow` 目录执行，以 `& .venv/Scripts/python.exe` 作为下文的 `python`。

## A. Raw Streaming

**Concept** `updates` 是节点的局部状态更新，`values` 是每一步后的完整状态；`custom` 是节点自己发出的业务进度。`messages` 用于模型 token/message，metadata 用来区分来自哪个 graph node，尤其是多个 Agent 同时输出时。

**Architecture** `router → worker`，worker 调用 `get_stream_writer()`。**Code** `src/runtime_graph.py`、`src/stage_a_raw_streaming.py`。**Run** `python src/stage_a_raw_streaming.py`。**Observed Result** router 更新 `route=worker`，worker 更新 `result=handled:hello`，完整末态同时包含 query/route/result，并收到 started/finished 两条 custom。`astream()` 的末态与同步 stream 一致。**Why** 先分清增量与快照，才能正确解释 Graph 的执行轨迹。

Raw `tasks`、`debug` 在 B 实际收到，`checkpoints` 在 C 配置 saver 后收到。无 Chat Model 节点，所以这里不产生 `messages` token；没有把空流冒充为模型流验证。

## B. Event Streaming v3

**Concept** raw `stream(..., stream_mode=...)` 返回底层事件，应用可自行检查 type；`stream_events(..., version="v3")` 提供 `values`、`messages`、`subgraphs`、`interrupts`、`output` 等 typed projections。**Architecture** A 图加一个独立的 parent/child 子图。**Code** `src/stage_b_event_streaming.py`。**Run** `python src/stage_b_event_streaming.py`。**Observed Result** 3 个 values snapshot，output 是最终完整状态；子图投影报告 `child`。**Why** 多 Agent 嵌套执行时，typed subgraph 投影省去手动解析 namespace。当前 1.2.12 会发出 v3 experimental warning；本章实跑仍 PASS。

## C. Checkpointer 与 thread_id

**Concept** saver 保存 thread 的 Graph State checkpoint，`messages` 只是可能的一个字段。`thread_id` 是执行线程的 checkpoint key，不等于用户 ID。**Architecture** `add → finish`，编译时传 `InMemorySaver()`。**Code** `src/stage_c_checkpointer.py`。**Run** `python src/stage_c_checkpointer.py`。**Observed Result** `thread-a` 两轮 total 2→5，`thread-b` total 7；checkpoint stream 非空。**Why** 同一 thread 可延续状态，另一 thread 有独立执行历史。

## D. State 与历史

**Concept** `get_state` 返回当前 `StateSnapshot`；`get_state_history` 返回历史 checkpoint，包括 `values`、`next`、`config` 和 `checkpoint_id`。**Architecture** 在 C 图完成后检查，按 `next == ("finish",)` 查找中间点。**Code** `src/stage_d_state_history.py`。**Run** `python src/stage_d_state_history.py`。**Observed Result** 末态 `next=()`；历史中存在 `next=('finish',)` 且 checkpoint ID 不同。**Why** 历史顺序按实际 API，不能假定 `history[0]` 是最早状态；特定 checkpoint 是 Replay/Fork 的入口。

## E. Checkpointer vs Store

**Concept** Checkpointer 保存 thread 范围内执行状态，Store 保存由 namespace/key 指定的跨 thread 应用数据。**Architecture** 两个 thread 共享 `InMemoryStore` 中 `("users", "user_123")/preference`，各自有 `InMemorySaver` 状态。**Code** `src/stage_e_store.py`。**Run** `python src/stage_e_store.py`。**Observed Result** 两个 thread 都读到 `concise`，但 checkpoint label 分别为 a、b。**Why** 用户偏好不属于某条执行线程。两种内存实现都不跨进程持久化。

## F. HITL Approve / Reject

**Concept** `interrupt(payload)` 暂停，`Command(resume=...)` 提供审批值；必须使用同一 `thread_id` 才能恢复该线程。**Architecture** `prepare → approval → execute/stop`。**Code** `src/stage_f_hitl.py`。**Run** `python src/stage_f_hitl.py`。**Observed Result** 先看到 `__interrupt__` 的 approval payload，approve 得 `SIMULATED_WRITE`，reject 得 `REJECTED`。**Why** saver 保留待执行任务和状态；换 thread ID 是另一条执行历史，不会恢复原审批。

## G. Resume Semantics

**Concept** 恢复是 checkpoint + node restart + resume value，不是 Python 从 `interrupt()` 那一行继续。**Architecture** 错误例把内存事件写在 interrupt 前；正确例把模拟动作放在审批后的独立节点。**Code** `src/stage_g_resume_semantics.py`。**Run** `python src/stage_g_resume_semantics.py`。**Observed Result** approval node runs=2，错误位置事件=2，正确位置事件=1。**Why** interrupt 前的外部副作用可能重复；真正外部 API 还需 idempotency key。Checkpoint 不能自动提供 exactly-once。

## H. Replay

**Concept** 从历史 checkpoint 重新执行未来节点。**Architecture** `choose_topic → build_output`，选择 `next=('build_output',)`。**Code** `src/stage_h_replay.py`。**Run** `python src/stage_h_replay.py`。**Observed Result** choose count 保持 1，build count 从 1 变 2。**Why** Replay 不是读取旧结果；后续 Tool/API/LLM 都可能再次执行，结果也可能变化。

## I. Fork

**Concept** `update_state` 从旧 checkpoint 产生新 checkpoint/branch；`as_node='choose_topic'` 明确后续边。**Architecture** 在 H 的中间 checkpoint 把 topic 从 cloud 改为 ai。**Code** `src/stage_i_fork.py`。**Run** `python src/stage_i_fork.py`。**Observed Result** fork 输出 `topic=ai`，原 snapshot 仍为 `topic=cloud`。**Why** 这类似 Git branch，而非修改旧历史。

## J. Multi-Agent Streaming + Persistence

**Concept** 将运行时观察和状态保存加到最小路由图。**Architecture** `router → record_worker/doctor_worker → aggregate`。**Code** `src/stage_j_multi_agent_runtime.py`。**Run** `python src/stage_j_multi_agent_runtime.py`。**Observed Result** route=record、worker started/finished、aggregate final，随后 `get_state` 能读取结果。**Why** 07 的目标是运行时能力；worker 保持合成、简短。

## K. Multi-Agent HITL + Time Travel

**Concept** 高风险模拟 worker 前审批，并从路由后的 checkpoint 切换 worker。**Architecture** risky route 经 approval，approve 到 risky worker，reject 到 fallback；普通 route 可从 record fork 到 doctor。**Code** `src/stage_k_multi_agent_hitl_time_travel.py`。**Run** `python src/stage_k_multi_agent_hitl_time_travel.py`。**Observed Result** v3 `interrupts` 投影发出审批请求；approve/reject 两条结果不同；从审批前 checkpoint replay 会再次 interrupt；原路线是 record，fork 是 doctor。**Why** Time Travel 再经过 interrupt 节点需要新的审批决策；不能沿用上一次批准作为永久授权。

## L. 综合 Runtime

**Concept** 同一小图具备 observe、pause、resume、inspect、replay、fork。**Architecture** K 图，两个 thread 分别展示审批链和路线分叉。**Code** `src/stage_l_final_runtime.py`。**Run** `python src/stage_l_final_runtime.py`。**Observed Result** `FINAL_RUNTIME_PASS`。**Why** 单进程 local runtime 证明控制流机制；`InMemorySaver` 退出即丢失状态，真实外部动作必须自己处理幂等、重试和补偿。

## 常见误解

- `interrupt` 可等待多久取决于 saver 的耐久性、保留策略和业务超时；这里的内存 saver 只适合当前进程。
- 多个并行 interrupt 需要按 interrupt ID 对应 resume value，本章只实跑单个审批，不构造复杂 UI。
- checkpoint 保存 Graph 状态与控制流，不是外部 API 的事务日志；崩溃发生在 API 执行后、checkpoint 前时，恢复可能重复调用。
