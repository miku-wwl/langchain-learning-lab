# 04 — LangChain MCP 本地学习实验

按照当前 04 教程逐步建立独立、可运行的 MCP 学习路径。

## 运行

```powershell
cd D:\workshop\sep\langchain-learning-lab\04-mcp
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -u scripts\verify_all.py
```

## 已实现学习点

- 01: Direct Tool baseline
- 02: MCP Server primitives
- 03: Raw Client discovery and call
- 04: STDIO transport
- 05: Streamable HTTP transport
- 06: LangChain MCPAdapter
- 07: Local Agent and integration comparison
- 08: Failures and security boundary

详细解释见 `docs/03-learning-guide.md`。
