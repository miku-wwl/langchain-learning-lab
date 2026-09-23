# 05 本地 E2E 设计

独立依赖：Python 3.13、`langgraph==1.2.12`、`langchain-core==1.6.4`、`pytest==8.4.2`。模型/runtime：纯 Python；不启动 Foundry，也不依赖 01–04。每个 Stage 自带断言和明确 PASS 标记，`scripts/verify_all.py` 逐个启动新进程并检查退出码与标记。

| Stage | 输入与边界 | 可观察结果 | 通过条件 |
| --- | --- | --- | --- |
| A Minimal Graph | `text=START` | builder/compiled 类型、A/B 顺序 | `START -> A -> B`; `MINIMAL_GRAPH_PASS` |
| B State Boundaries | `user_input='  langgraph  '` | prepare 的 `working_text`、最终外部输出 | 仅 `graph_output=LANGGRAPH`; `STATE_BOUNDARY_PASS` |
| C Reducers | 两次 value/status 更新；HumanMessage | `[10,20]`、`B`、两条消息 | 覆盖与 reducer/消息追加真实发生；`REDUCER_PASS` |
| D Runtime Context | message 与 `user_id` | 节点读取 Runtime、config 递归限额 | context 不泄露到 State；`RUNTIME_CONTEXT_PASS` |
| E Routing/Loop | `number=5/-5`、`count=0` | 正负分支、0→3、故意循环被阻止 | 三个独立标记均 PASS |
| F Runtime Policies | 同输入两次；前两次失败；永远失败 | 真实调用计数、三次尝试、fallback | CACHE/RETRY/ERROR_HANDLER 均 PASS |
| G Send | `subjects=[A,B,C]` | 三个不同任务输入、三个输出 | 比较集合不依赖顺序；`SEND_FANOUT_PASS` |
| H Command | `score=80/40` | update + goto 两个结果 | pass/fail 都正确；`COMMAND_PASS` |
| I Subgraph | `log=[]` | 父与子节点各一次 | `['parent','subgraph']`; `SUBGRAPH_PASS` |
| J Streaming | `value=1` | updates、values、custom、tasks | 各事件含预期节点/状态；前三者为核心 PASS |
| K Final Graph | 快路径与拆分路径各一次 | normalize、条件路由、Send/reduce、finalize、stream、Mermaid | 输出准确，Mermaid 文件来自实际 compiled graph；`FINAL_GRAPH_PASS` |

确定性测试覆盖每项状态和路由规则，避免只靠打印。最终门槛是所有 Stage A–K、测试及集成图都通过，统一入口才输出 `05_LANGGRAPH_CORE_PASS_LOCAL`。图可以有循环；递归保护实验使用很小的 `recursion_limit` 并捕获 `GraphRecursionError`，不会无限挂起。
