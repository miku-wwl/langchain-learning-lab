# 07 本地验证报告

## 环境与边界

| 项目 | 实际值 |
| --- | --- |
| OS | Windows / PowerShell |
| Python | 3.13.9 |
| LangGraph | 1.2.12 |
| LangChain | 1.4.2 |
| LangChain Core | 1.6.4 |
| pytest | 8.4.2 |
| Checkpointer / Store | `InMemorySaver` / `InMemoryStore` |
| Model/runtime | 无模型；纯 Python deterministic workflow |
| Cloud/API/secret | 未使用 |
| Final status | **PASS_LOCAL** |

## 执行命令与结果

在 `07-langgraph-workflow`：

```powershell
python -m venv .venv
& .venv/Scripts/python.exe -m pip install -r requirements.txt
& .venv/Scripts/python.exe src/stage_a_raw_streaming.py
& .venv/Scripts/python.exe src/stage_b_event_streaming.py
& .venv/Scripts/python.exe src/stage_c_checkpointer.py
& .venv/Scripts/python.exe src/stage_d_state_history.py
& .venv/Scripts/python.exe src/stage_e_store.py
& .venv/Scripts/python.exe src/stage_f_hitl.py
& .venv/Scripts/python.exe src/stage_g_resume_semantics.py
& .venv/Scripts/python.exe src/stage_h_replay.py
& .venv/Scripts/python.exe src/stage_i_fork.py
& .venv/Scripts/python.exe src/stage_j_multi_agent_runtime.py
& .venv/Scripts/python.exe src/stage_k_multi_agent_hitl_time_travel.py
& .venv/Scripts/python.exe src/stage_l_final_runtime.py
& .venv/Scripts/python.exe -m pytest -q
& .venv/Scripts/python.exe scripts/verify_all.py
```

| Stage | 观察证据 | 状态 |
| --- | --- | --- |
| A raw stream | router/worker updates；完整末态；started/finished custom；async values 末态一致 | PASS |
| B event stream | 3 个 typed values，最终 output，`child` 子图；raw tasks/debug 均有 4 事件 | PASS |
| C checkpoint | thread-a total 2→5，thread-b=7；checkpoint 流 4 事件 | PASS |
| D state/history | 当前 next=()；历史含 next=('finish',) 和不同 checkpoint_id | PASS |
| E Store | 两线程读取 concise，共享 Store，checkpoint label 分别 a/b | PASS |
| F HITL | approval payload；approve=`SIMULATED_WRITE`，reject=`REJECTED` | PASS |
| G Resume | approval node 2 次；错误位置内存事件 2 次、正确位置 1 次 | PASS |
| H Replay | choose_topic=1，build_output=2 | PASS |
| I Fork | 原始 `topic=cloud`，新分支 `topic=ai`，原 snapshot 保留 | PASS |
| J multi-agent | route/worker/aggregate updates + custom，`get_state` 保存结果 | PASS |
| K HITL/time travel | v3 interrupt；模拟高风险双路径；回放再中断；record→doctor fork | PASS |
| L integrated | observe、pause、inspect、resume、replay、fork 在同一小图贯通 | PASS |

`pytest -q`：**12 passed, 2 warnings**。`verify_all.py`：**`07_WORKFLOW_RUNTIME_PASS_LOCAL`**。

## API 差异与修复

- 系统 Python 没有安装 LangGraph；创建了 07 独立 `.venv` 并安装 pinned requirements。
- 初次 B 测试错误地预期子图投影 `graph_name=demo_child`；1.2.12 实际返回嵌入节点名 `child`。改为断言实际 API 输出，重跑通过。
- v3 `stream_events` 在 1.2.12 发出 `LangChainBetaWarning`（experimental），但 `values`、`output`、`subgraphs`、`interrupts` 投影全部实测可用。
- 本章没有 Chat Model，所以 `messages` token / metadata 仅在指南解释，未声称实测通过；多 Agent 模型行为也由纯 Python 合成 worker 替代。`as_node` 显式用于 Fork，避免依赖推断。

## 范围与风险

所有动作都是 `SIMULATED_*` 字符串或内存列表，未发生真实写入、删除或发送。`InMemorySaver`/`InMemoryStore` 不验证跨进程恢复；checkpoint 不保证外部系统 exactly-once。没有付费云 API、模型下载或 secret。当前无阻塞项。源码教程位于仓库 `doc/07.LangGraph_v1.2_多智能体工作流_更新版.md`。
