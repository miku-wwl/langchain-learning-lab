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

## Stage C — Document → Chunks

**Concept**：太长的 Document 往往把不相关信息混在一起。`RecursiveCharacterTextSplitter` 优先按段落、换行、空格等自然边界切分，生成较短的 Chunk。`chunk_size` 是目标上限，`chunk_overlap` 是相邻块可共享的目标长度。

**Architecture**：`Document(完整 FAQ) → RecursiveCharacterTextSplitter → 8 个 Chunk`。

**Code**（[完整代码](../src/stage_c_splitter.py)）：

```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=180, chunk_overlap=25, add_start_index=True
)
chunks = splitter.split_documents(documents)
```

**Run**：`.venv\Scripts\python.exe src\stage_c_splitter.py`

**Result**：1 个 Document 被切成 8 个 Chunk；每块保留 `source`，并新增 `start_index`。退款到账证据位于 `start_index=327` 的 Chunk。自然段落边界下不保证每对相邻 Chunk 都有 25 字符重叠；另一个固定长度示例实际打印出相同的 15 字符尾部/头部。

**Why**：Document 是加载后的完整资料，Chunk 是用于索引与检索的片段。Chunk 太大增加噪声，太小会切断语义，overlap 只能缓解一部分边界问题。[官方 splitter 指南](https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter)也说明其递归分隔符顺序和 overlap 是目标值。

## Stage D — Text → Embedding Vector

**Concept**：Embedding 模型把文本映射到固定长度的数值向量。向量不是摘要或答案；向量之间的距离可帮助找到语义相近的文本。LLM 负责生成回答，Embedding 模型负责表示文本以供搜索。

**Architecture**：`refund question / refund policy / weather sentence → local FastEmbed → 384D vectors → cosine similarity`。

**Code**（[工厂](../src/embedding_factory.py)、[完整 Stage](../src/stage_d_embedding.py)）：

```python
embeddings = create_local_embeddings()
query = embeddings.embed_query("How can I get a refund?")
refund, weather = embeddings.embed_documents([
    "What is the refund policy?",
    "The weather is sunny today.",
])
related = cosine_similarity(query, refund)
unrelated = cosine_similarity(query, weather)
```

**Run**：`.venv\Scripts\python.exe src\stage_d_embedding.py`

**Result**：本地 `BAAI/bge-small-en-v1.5` 产生 384 维向量；本次运行 `similarity(refund, refund)=0.8687`，`similarity(refund, weather)=0.4193`。首次获取的模型缓存约 64 MB；关闭 Hugging Face 网络访问后重跑仍成功。

**Why**：这证明程序使用真实语义向量，且相关文本比无关文本接近。具体分数随模型而变，只应测试排序与检索行为。索引和查询必须用兼容的 Embedding 空间。

## Stage E — Chunks → Vector Store → Similarity Search

**Concept**：Embedding 模型执行 `Text → Vector`；Vector Store 保存向量、Chunk 原文与 metadata，并用 Query 向量搜索相近条目。两者不是同一个组件。

**Architecture**：`8 Chunks → Embedding → InMemoryVectorStore`；随后 `Query → Query Embedding → Top-K Documents`。

**Code**（[完整代码](../src/stage_e_vectorstore.py)）：

```python
store = InMemoryVectorStore(embeddings)
store.add_documents(chunks)
results = store.similarity_search_with_score(question, k=3)
```

**Run**：`.venv\Scripts\python.exe src\stage_e_vectorstore.py`

**Result**：8 个 Chunk 被索引；退款到账问题的 Top-1 是“签收后 7 天可申请退款”（score `0.8250`），真正的到账时间证据排在 Top-2（score `0.8055`），Top-3 是退款例外与审核时间。

**Why**：这正好展示检索排序问题。只看“有一个相关文档”还不够；应观察排名和 Top-K 内容。这里 k=3 让正确证据进入上下文。普通关键词匹配关注字面词，语义检索则比较向量，能处理一部分措辞变化，但也可能把同主题的不同规则排在前面。

## Stage F — Vector Store → Retriever

**Concept**：Vector Store 提供保存、搜索等能力；Retriever 提供统一的 `Query → list[Document]` 接口。Retriever 本身没有改变这个示例的搜索算法。

**Architecture**：`InMemoryVectorStore.as_retriever(k=3) → retriever.invoke(question) → Top-3 Documents`。

**Code**（[完整代码](../src/stage_f_retriever.py)）：

```python
retriever = store.as_retriever(search_kwargs={"k": 3})
retrieved = retriever.invoke(question)
direct = store.similarity_search(question, k=3)
```

**Run**：`.venv\Scripts\python.exe src\stage_f_retriever.py`

**Result**：Retriever 返回同样的 Top-3，顺序与直接 `similarity_search` 一致；Top-2 含“3 to 5 business days”。

**Why**：把后续 RAG 写在 Retriever 接口之上，可以在未来换检索实现时少改上层代码；本章不继续引入混合检索或 reranker。
