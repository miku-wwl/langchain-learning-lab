# 07 — LangGraph Multi-Agent Workflow Runtime

```text
Multi-Agent Workflow → Streaming → Checkpointer → State History
                    → Interrupt → Resume → Replay / Fork → Durable Runtime concepts
```

本章学习一个运行中的小型 Graph 怎样被观察、保存、暂停、恢复、回放和分叉。所有输入和动作均为合成数据；不调用云 API，也不需要模型。这里的 `InMemorySaver` 只证明单进程内恢复，进程退出后状态会丢失。

## 安装

在本目录执行（Windows PowerShell）：

```powershell
python -m venv .venv
& .venv/Scripts/python.exe -m pip install -r requirements.txt
```

Python 3.13.9、LangGraph 1.2.12、LangChain 1.4.2 为本次验证环境。

## 按顺序运行

```powershell
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
```

| 阶段 | 学习重点 | 关键输出 |
| --- | --- | --- |
| A–B | Raw `updates` / `values` / `custom`，v3 typed event、子图 | `RAW_STREAM_*_PASS`、`EVENT_STREAM_PASS` |
| C–E | checkpoint、thread、历史、Store | `THREAD_ISOLATION_PASS`、`STATE_HISTORY_PASS` |
| F–G | interrupt/resume、节点重跑、副作用边界 | `HITL_*_PASS`、`RESUME_REEXECUTION_PASS` |
| H–I | 历史 checkpoint Replay、Fork | `REPLAY_PASS`、`FORK_PASS` |
| J–L | 小型多 Agent 图上的流、审批、分叉 | `FINAL_RUNTIME_PASS` |

推荐按 A→L 顺序学习；逐个 Git commit 复习从 `feat(07): add raw graph streaming modes` 开始。

## 一键验证

```powershell
& .venv/Scripts/python.exe -m pytest -q
& .venv/Scripts/python.exe scripts/verify_all.py
```

只有所有真实 stage 断言通过时，脚本才打印 `07_WORKFLOW_RUNTIME_PASS_LOCAL`。运行状态与证据见 [验证报告](docs/04-verification-report.md)，概念与代码见 [学习指南](docs/03-learning-guide.md)。

## 07 与 06 的关系

06 讲 Router / Supervisor / Worker 如何分工。07 使用一个 `router → record_worker / doctor_worker → aggregate` 小图承载 runtime 验证，避免复制 06 的完整实现，也不 import 06 的代码。
