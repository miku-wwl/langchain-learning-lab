# 05 — LangGraph Core Graph

```text
Input → StateGraph Builder → compile() → CompiledStateGraph
      → Node → Partial State Update → Reducer
      → Routing (Edge / Conditional Edge / Command / Send)
      → Loop / Fan-out / Subgraph → Output
```

纯 Python 本地学习实验：无 LLM、云服务、数据库或前面章节依赖。按 A→K 顺序运行，每段源码都带实际断言及 PASS 标记。

## 环境与运行

在 PowerShell 中从本目录执行：

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe src\stage_a_minimal_graph.py
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe scripts\verify_all.py
```

若 Python 环境使用 `uv`，可用 `uv pip install --python .venv\Scripts\python.exe -r requirements.txt`。每个 `src/stage_*.py` 都可以像 Stage A 一样单独运行。总入口会逐段启动新进程、检查退出码与 PASS 标记、检查 Mermaid，并运行测试；全部成功才输出 `05_LANGGRAPH_CORE_PASS_LOCAL`。

## 学习顺序

| Stage | 学习内容 | 源码 |
| --- | --- | --- |
| A | Builder、compile、invoke、普通 Edge | `src/stage_a_minimal_graph.py` |
| B | Input/Overall/Output State、局部更新 | `src/stage_b_state_boundaries.py` |
| C | 普通覆盖、reducer、MessagesState | `src/stage_c_reducers.py` |
| D | Runtime Context 与 Config | `src/stage_d_runtime_context.py` |
| E | 条件路由、循环、递归保护 | `src/stage_e_routing_loop.py` |
| F | Cache、Retry、Error Handler | `src/stage_f_runtime_policies.py` |
| G | Send fan-out 与 reducer fan-in | `src/stage_g_send.py` |
| H | Command 更新并跳转 | `src/stage_h_command.py` |
| I | 父图调用子图 | `src/stage_i_subgraph.py` |
| J | updates、values、custom、tasks stream | `src/stage_j_streaming.py` |
| K | 快路径与动态 fan-out 综合图 | `src/stage_k_final_graph.py` |

教程原文在 [`doc/05.LangGraph_v1.2_Core_Graph_更新版.md`](../doc/05.LangGraph_v1.2_Core_Graph_更新版.md)。先读 [`docs/01-syllabus-analysis.md`](docs/01-syllabus-analysis.md) 与 [`docs/02-e2e-design.md`](docs/02-e2e-design.md)，再按 A–K 阅读源码与 [`docs/03-learning-guide.md`](docs/03-learning-guide.md)。运行 K 后可在 [`docs/final-graph.mmd`](docs/final-graph.mmd) 查看真实 compiled graph 导出的 Mermaid。实测数据在 [`docs/04-verification-report.md`](docs/04-verification-report.md)。

## 本次验证

| 项目 | 结果 |
| --- | --- |
| OS / Python | Windows / 3.13.9 |
| LangGraph / langchain-core | 1.2.12 / 1.6.4 |
| 模型 / runtime | 无模型；本地纯 Python |
| pytest | 21 passed |
| A–K 与总入口 | `05_LANGGRAPH_CORE_PASS_LOCAL` |
| 阻塞 | 无 |
