# 06 — LangGraph Multi-Agent Learning Lab

```text
Pattern A — Router                 Pattern B — Supervisor
User Query                         User
    ↓                               ↓
Router                         Supervisor Agent
 ├→ Record Agent                ├→ Record Subagent
 ├→ Guideline Agent             ├→ Guideline Subagent
 ├→ Doctor Agent                └→ Doctor Subagent
 └→ Refuse                           ↓
    ↓                           Worker Result(s)
Aggregate                            ↓
    ↓                         Supervisor Synthesis
  Answer                              ↓
                                    Answer
```

这是独立的本地教学实验：合成记录、合成指南笔记、合成医生目录；不接真实医疗数据，也不提供真实诊断或治疗建议。Router 是一次确定性分流；Supervisor 是真实 `create_agent`，可连续调用多个子 Agent。A→J 每个脚本均有实际执行断言。

## 本地准备与运行

从本目录在 PowerShell 执行：

```powershell
foundry --version
foundry server status
foundry model list --cached
foundry model list --loaded
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -u src\stage_a_workers.py
& .\.venv\Scripts\python.exe -u src\stage_b_router.py
& .\.venv\Scripts\python.exe -u src\stage_f_supervisor.py
& .\.venv\Scripts\python.exe -u src\stage_g_multi_delegate.py
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -u scripts\verify_all.py
```

其余阶段文件在 `src/stage_c_*.py` 到 `src/stage_j_*.py`，按字母顺序运行。`model_factory.py` 从运行中的 Foundry Local 动态发现 `/v1` 地址与已加载的 `phi-4-mini` 模型 ID，不硬编码端口。当前模型为已缓存、支持工具调用的 GPU 版本。`uv` 可替代 pip：`uv pip install --python .venv\Scripts\python.exe -r requirements.txt`。验证入口会重新实际执行 A–J 和测试；核心链路全部成功才输出 `06_MULTI_AGENT_PASS_LOCAL`。

## 学习路径

| Stage | 重点 |
| --- | --- |
| A | 三个独立 Worker Agent 与各自工具 |
| B | 四路确定性 Router |
| C | LangGraph 条件路由与真实 Worker 执行 |
| D | 显式 Aggregate 节点 |
| E | 子 Agent 作为高层工具、Tool Namespace |
| F | Supervisor Agent 与完整 ToolMessage loop |
| G | 单请求多个子 Agent，顺序/并行证据 |
| H | Context Isolation 与 Output Filtering |
| I | NO_DATA、执行错误和部分成功 |
| J | 同一请求对比 Router 与 Supervisor |

先读 [教程原文](../doc/06.LangChain_v1.4_LangGraph_v1.2_多智能体_更新版.md)、[知识点矩阵](docs/01-syllabus-analysis.md) 和 [E2E 设计](docs/02-e2e-design.md)，再沿 A–J 阅读 [学习指南](docs/03-learning-guide.md)。[实测对比](docs/router-vs-supervisor.md) 和 [验证报告](docs/04-verification-report.md) 记录结果与修复。

## 本次结果

| 项目 | 结果 |
| --- | --- |
| Python / LangChain / LangGraph | 3.13.9 / 1.4.2 / 1.2.12 |
| Runtime / 模型 | Foundry Local 0.10.3 / GPU `phi-4-mini` |
| 模型选择 | `qwen3-4b` 工具/结果不稳定，实测后改用已缓存 `phi-4-mini` |
| 测试 | 20 passed |
| Router / Supervisor / A–J | `06_MULTI_AGENT_PASS_LOCAL` |
| 并行调用 | 可选；本机观察到顺序调用 |
| 阻塞 | 无 |
