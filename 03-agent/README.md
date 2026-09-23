# 03 — LangChain Agent 本地学习实验

本章基于当前 03 教程，按概念逐步实现；每个已提交阶段都可以独立运行。

## 准备

```powershell
cd D:\workshop\sep\langchain-learning-lab\03-agent
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -u scripts\verify_all.py
```

## 已实现阶段

- A: create_agent and local model（`src/stage_a_agent.py`）
- B: streaming and PII（`src/stage_b_streaming_pii.py`）
- C: tool calling and ToolMessage loop（`src/stage_c_tools.py`）

学习说明见 `docs/03-learning-guide.md`。
