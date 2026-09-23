# E2E 设计

顺序：A 原始流 → B typed event → C–E 状态和存储 → F–G 暂停恢复 → H–I 回放分叉 → J–K 叠加小型多 Agent → L 汇总。

- `runtime_graph.py` 提供 A 的最小 `router → worker` 图。
- 每个 `stage_*.py` 暴露 `run()`，内部断言实际观测并输出明确 PASS 标记；脚本直接运行该 stage。
- `verify_all.py` 依次调用 A–L 的真实运行路径；任何断言失败均不得输出最终 PASS。
- Checkpointer 用 `InMemorySaver`，Store 用 `InMemoryStore`，模型不用。所有动作只是内存列表或 `SIMULATED_*` 字符串。
- 每个 stage 都创建新 graph/store/thread，避免演示之间共享运行态。Time Travel 通过 `snapshot.next` 选择 checkpoint，不依赖历史数组的位置。
- 07 的最小 router/worker 图只提供 06 架构的运行时承载物；不 import 05/06。

最终验证必须看到真实 stream 事件、checkpoint、interrupt、resume、replay 和 fork。证明边界仅限单进程本地执行，不推断跨进程耐久性或外部系统 exactly-once。
