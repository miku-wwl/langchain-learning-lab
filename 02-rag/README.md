# 02 — LangChain RAG 本地学习实验

```text
Documents (resources/company_faq.txt)
    ↓
Loader → Document
    ↓
Splitter → Chunks
    ↓
Embedding → Vectors
    ↓
InMemoryVectorStore ← Query → Query Embedding
    ↓                         ↓
    └──── Similarity Search ───┘
                  ↓
              Retriever
                  ↓
          Context + Question
                  ↓
                Prompt
                  ↓
          Foundry Local LLM
                  ↓
          Grounded Answer
```

本章独立运行，不导入 `01-langchain-foundations`。按 A–H 阶段拆开观察 Loader、Splitter、Embedding、相似度搜索、Retriever 和两步 RAG；Redis 是可选延伸。原始教程在 [02 Markdown](../doc/02.LangChain_v1.4_02_RAG_更新版.md)，学习顺序见 [Learning Guide](docs/03-learning-guide.md)。

## 1. 创建环境并安装依赖

在 PowerShell 中，从 `02-rag` 目录执行：

```powershell
cd D:\workshop\sep\langchain-learning-lab\02-rag
python -m venv .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
```

若没有 `uv`，可用 `.venv\Scripts\python.exe -m pip install -r requirements.txt`。本次实测环境是 Python 3.13.9、LangChain 1.4.2。Embedding 使用本机 FastEmbed/ONNX 的 `BAAI/bge-small-en-v1.5`，首次运行需下载约 64 MB 到本章 `.model_cache/`，之后在本机推理。该目录已被 Git 忽略。FAQ 是英文，因此选择英文小模型。

## 2. 检查本地聊天模型

默认使用已缓存的 Foundry Local `qwen3-4b`。请先确认 Foundry CLI 与模型：

```powershell
foundry --version
foundry server status
foundry model list --cached
foundry model list --loaded
foundry model load qwen3-4b
```

`src/model_factory.py` 会从 Foundry CLI 读取当前本地端口和已加载模型 ID。若使用另一个本地 OpenAI 兼容服务，可设置 `LOCAL_OPENAI_BASE_URL`（含 `/v1`）与 `LOCAL_CHAT_MODEL`；示意见 [.env.example](.env.example)。不需要云 API Key 或运行 01 阶段。`LANGSMITH_TRACING` 在统一验证脚本中关闭。

Qwen3-4b 在当前 Foundry Local 版本下会把 `<think>...</think>` 内容放进回复文本。阅读 G/H 阶段输出时，以标签后的最终回答为准；本章保留原始输出以便观察模型行为。

## 3. 逐层运行

在 `02-rag` 目录执行下表命令。A–H 分别打印输入、关键中间值和局部通过标记。

| 阶段 | 观察对象 | 命令 |
| --- | --- | --- |
| A | 无知识库的本地 LLM 回答 | `.venv\Scripts\python.exe src\stage_a_baseline.py` |
| B | File → Document、正文与 metadata | `.venv\Scripts\python.exe src\stage_b_loader.py` |
| C | Document → Chunks、长度和 overlap | `.venv\Scripts\python.exe src\stage_c_splitter.py` |
| D | 真正的向量与语义相似度排序 | `.venv\Scripts\python.exe src\stage_d_embedding.py` |
| E | 内存向量库与 Top-K/score | `.venv\Scripts\python.exe src\stage_e_vectorstore.py` |
| F | Retriever 与直接搜索比较 | `.venv\Scripts\python.exe src\stage_f_retriever.py` |
| G | 检索 → context → prompt → 本地 LLM | `.venv\Scripts\python.exe src\stage_g_rag.py` |
| H | 已知、同义、未知三类问题 | `.venv\Scripts\python.exe src\stage_h_grounding.py` |

完整 RAG 从 G 开始看，三类问题一起看 H。已知退款问题的正确证据在本次 Top-2；Top-1 是另一个退款规则。请同时观察检索结果与答案，不能只凭模型最后一句判断检索质量。

## 4. 测试与整体验证

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -u scripts\verify_all.py
```

测试覆盖 Loader、Chunk、Embedding 维度及相似度排序、向量库、Retriever、已知和同义问题的检索，以及未知问题的证据边界。统一脚本重新执行 A–H，包括真实本地聊天模型调用；全部核心阶段成功才打印 `02_RAG_PASS_LOCAL`。它会把 Redis 标为 `OPTIONAL / NOT RUN`。

## 5. 从哪里开始学习

1. [Syllabus Analysis](docs/01-syllabus-analysis.md)：对照原教程看每个知识点落在哪一阶段。
2. [E2E Design](docs/02-e2e-design.md)：了解各阶段输入、输出和通过标准。
3. [Learning Guide](docs/03-learning-guide.md)：按 Concept → Architecture → Code → Run → Result → Why，从 A 学到 H。
4. [Verification Report](docs/04-verification-report.md)：核对本次实际命令、版本、结果和限制。

本章只实现基础两步 RAG。代码使用内存向量库和一份虚构 FAQ，适合逐层学习，不涉及 Agent、MCP 或部署。
