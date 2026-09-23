# 07 课程知识矩阵

唯一 syllabus：`doc/07.LangGraph_v1.2_多智能体工作流_更新版.md`。本章复用已学的路由概念，只实现运行时能力；所有执行均为纯 Python 合成数据。

| ID | 知识点 | Checkpointer | Streaming | HITL | Time Travel | Multi-Agent | E2E 方式 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | `stream()` / `astream()`；`updates`、`values`、`custom` | — | ✓ | — | — | — | 观察 node 增量、完整状态、进度事件及异步消费 |
| B | `messages` metadata；`checkpoints`、`tasks`、`debug`；`stream_events(version="v3")` typed projections；subgraphs | 可选 | ✓ | — | — | 子图 | 本地 deterministic graph 的 raw/event 流；无模型时 messages 不产生 token |
| C | Checkpointer、`InMemorySaver`、`thread_id` | ✓ | — | — | — | — | A/B 两个 thread 的状态隔离与同 thread 延续 |
| D | `StateSnapshot`、`get_state`、`get_state_history`、`checkpoint_id` | ✓ | — | — | 基础 | — | 找 `next` 指定的历史点并打印配置/值 |
| E | Store、`InMemoryStore` | ✓ | — | — | — | — | 两个 thread 独立 checkpoint、共享 namespace/key |
| F | `interrupt`、interrupt payload、`Command(resume)` | ✓ | — | ✓ | — | — | approve/reject 两条模拟动作 |
| G | Resume semantics、side-effect boundary、idempotency | ✓ | — | ✓ | — | — | 计数证明 node 重跑；内存列表展示错误放置与正确放置 |
| H | Replay | ✓ | — | — | ✓ | — | 从历史 checkpoint 重跑未来 node 的计数 |
| I | Fork、`update_state`、`as_node` | ✓ | — | — | ✓ | — | 新旧 branch 各自保留输出 |
| J | Multi-Agent runtime integration | ✓ | ✓ | — | — | ✓ | 小型 router/worker 流和状态检查 |
| K | HITL + Time Travel + multi-agent | ✓ | ✓ | ✓ | ✓ | ✓ | 模拟危险 worker 审批与路线分叉 |
| L | 综合验证与可靠性边界 | ✓ | ✓ | ✓ | ✓ | ✓ | 自动 verifier、确定性测试、文档 |

`thread_id` 是执行线程的 checkpoint key，不是 user ID。`InMemorySaver` 和 `InMemoryStore` 都只在当前进程有效。Replay 重新执行未来节点；checkpoint 不保证外部副作用 exactly-once。
