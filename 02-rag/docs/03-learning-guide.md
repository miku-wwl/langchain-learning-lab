# LangChain 02：一步步看清两步 RAG

先读 [原始 02 教程](../../doc/02.LangChain_v1.4_02_RAG_更新版.md) 了解概念，再按本页 Stage A–H 顺序运行。具体安装命令在 [README](../README.md)，知识点边界在 [syllabus analysis](01-syllabus-analysis.md)。本实验只用一份虚构公司 FAQ、本地聊天模型、本地 Embedding 和内存向量库。

## 先看完整路线

```text
INDEXING（知识变化时）                    QUERY TIME（每次提问）
TXT → Loader → Document → Splitter       Question → Retriever
                   ↓                                      ↓
                Chunks → Embedding → InMemoryVectorStore  ↓
                                             ↑             ↓
                                             └── 相似度搜索 ┘
                                                    ↓
                                                  Context
                                                    ↓
                                         Prompt(context, question)
                                                    ↓
                                              Local LLM → Answer
```

Indexing 把知识变成可搜索的向量及原文；查询时先检索，再把取回的原文交给模型生成。这个流程由 Python 显式控制，模型不决定是否检索，所以基础两步 RAG 不需要 Agent。

## Stage A — 没有 RAG 的 Baseline

**Concept**：先直接问模型一个虚构公司的内部政策。这个阶段只观察模型在没有内部资料时怎样回答，不要求它一定产生幻觉。

**Architecture**：`Question → Foundry Local Qwen3-4b → Answer`。

**Code**（[完整代码](../src/stage_a_baseline.py)）：

```python
response = create_local_chat_model().invoke(
    "What is Northstar Shop's exact refund deadline after delivery?"
)
```

**Run**：`.venv\Scripts\python.exe src\stage_a_baseline.py`

**Result**：模型回答它无法访问 Northstar Shop 的内部政策。Stage A 确认聊天端真实运行，但不把这个回答视作退款规则证据。

**Why**：内部政策不在模型当前输入中。RAG 的目的，是在推理时提供可核查的外部知识；Fine-tuning 则主要调整模型行为、格式或领域适应，两者可同时使用。

## Stage B — File → Document

**Concept**：普通 TXT 文件只是磁盘上的字节。`TextLoader` 将它转换为 LangChain `Document`，把正文放在 `page_content`，把来源放在 `metadata`。

**Architecture**：`resources/company_faq.txt → TextLoader → list[Document]`。

**Code**（[完整代码](../src/stage_b_loader.py)）：

```python
documents = TextLoader(str(FAQ_PATH), encoding="utf-8").load()
print(documents[0].page_content)
print(documents[0].metadata)
```

**Run**：`.venv\Scripts\python.exe src\stage_b_loader.py`

**Result**：得到 1 个 `Document`；正文包含 refund、delivery、membership、support，metadata 的 `source` 指向 FAQ 文件。

**Why**：后面的 Splitter、Vector Store 和 Retriever 都传递 `Document`，这样正文与来源可以一起流动。当前 `langchain-community` 0.4.2 的 `TextLoader` 能运行，但包会发出 sunset 警告；本 Lab 固定版本，并在报告里解释。
