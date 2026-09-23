# 05 本地验证记录

## 环境

| 项目 | 实际值 |
| --- | --- |
| OS | Windows / PowerShell |
| Python | 3.13.9 |
| LangGraph | 1.2.12 |
| langchain-core | 1.6.4 |
| pytest | 8.4.2 |
| 模型/runtime | 无 LLM；本地纯 Python |
| 外部服务 | 无 |

依赖安装：`uv pip install --python .venv\Scripts\python.exe -r requirements.txt`。`.venv` 留在本地且被忽略。

## 实际执行

从 `05-langgraph-core` 执行：

```powershell
& .\.venv\Scripts\python.exe -u src\stage_a_minimal_graph.py
# 上述命令中的文件名依次换成 stage_b_state_boundaries.py 至 stage_k_final_graph.py
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -u scripts\verify_all.py
```

| Stage | 关键观察 | 状态 |
| --- | --- | --- |
| A | 构建器/编译图类型，A→B 顺序 | PASS |
| B | 内部局部更新，输出仅 `graph_output` | PASS |
| C | `[10,20]` 聚合，消息追加 | PASS |
| D | Runtime user_id 与 Config recursion_limit；State 不泄露 user_id | PASS |
| E | 正负路由，count=3，GraphRecursionError | PASS |
| F | 缓存调用一次，三次 retry，handler fallback | PASS |
| G | 三个 Send 任务，结果经 reducer 汇合 | PASS |
| H | score 80/40 两个 Command 路径 | PASS |
| I | 父子 log 各追加一次 | PASS |
| J | updates、values、custom、tasks 均收到实际事件 | PASS |
| K | 快路径与 fan-out 路径、stream、Mermaid 文件 | PASS |

`pytest -q`：**21 passed**。`scripts/verify_all.py`：A–K、Mermaid、测试全 PASS，输出 `05_LANGGRAPH_CORE_PASS_LOCAL`。K 导出的 `docs/final-graph.mmd` 由真实编译图生成，无需在线 PNG 渲染器。

## 与教程/API 的核对和修复

- 教程旧说法 “Graph 只能是 DAG” 不适用：E 的回边真实执行。`timeout`、`trace_policy`、`set_node_defaults` 只核对 API 和说明适用边界；本章没有人为制造长时间等待。
- 子图首次运行得到 `['parent','parent','subgraph']`：直接将父图现有 reducer 字段带入子图，完整子图输出回父图时再次追加了已有 `parent`。改为 wrapper 给子图空日志，仅把新增项返回父图，再次运行得到 `['parent','subgraph']`。
- `tasks` 模式在本地安装版本实际产生 increment/double 的开始和结果事件；因此也纳入当前验证。
- 所有测试只断言确定性状态、路径、计数和事件，不断言随机任务 ID 或并行任务顺序。

**阻塞：无。最终状态：PASS_LOCAL。**
