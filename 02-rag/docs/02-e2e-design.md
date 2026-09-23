# 02 RAG 本地 E2E 设计

## 边界与输入

- 02 只依赖自身的虚拟环境、模型工厂、Embedding 工厂、样本数据、源码与验证入口；不导入 01。
- 聊天端使用本机 Foundry Local 已缓存模型；Embedding 端使用小型本地模型，首次下载后在本机推理，不调用收费云 API。
- 一份小型 FAQ 包含 refund、delivery、membership、support 四类事实；CEO 等未写入的数据用于 unknown 测试。
- Redis 为可选替换项，核心 PASS 只以 `InMemoryVectorStore` 的完整两步 RAG 为准。

| Stage | 学什么 | 输入 | 预期输出 | E2E 通过标准 |
| --- | --- | --- | --- | --- |
| A Baseline | 无知识库模型调用 | 询问内部退款政策 | 原始模型回答 | 本地模型真实返回；只记录，不要求猜错 |
| B Loader | File 与 Document 的区别 | 本地 TXT | `Document[]` 与 metadata | 加载的正文、来源和条目数正确 |
| C Splitter | Document 与 Chunk、大小和重叠 | Stage B Document | 多个 Chunk | `split_documents` 真实执行，保留 `source` 与 `start_index` |
| D Embedding | 文本到向量、语义相似度 | 相近/无关三句 | 维度、向量前几维、余弦分数 | 真实向量非空，退款相关对比天气更相近 |
| E Vector Store | 建索引与直接相似度搜索 | Chunks、已知退款问题 | Top-K Document/score | `InMemoryVectorStore` 检索的 Top-K 包含退款证据 |
| F Retriever | 统一 Query → Document 接口 | 相同问题 | Top-K Document | `retriever.invoke()` 结果和直接搜索可比对 |
| G 2-Step RAG | 检索、上下文、Prompt、LLM | 已知退款问题 | 有依据的回答 | 答案含正确天数，且检索结果先独立通过 |
| H Grounding | Known / Paraphrase / Unknown | 三类问题 | 检索与回答结果 | 前两类找对证据并正确回答；未知问题明确说知识库无信息 |
| I Redis | 向量存储替换的概念 | 可选本地 Redis | 可选 | `OPTIONAL / NOT RUN`，不影响主结果 |

## 数据与可观察性

`TextLoader → RecursiveCharacterTextSplitter → FastEmbedEmbeddings → InMemoryVectorStore` 构成 Indexing。查询时固定执行 `retriever.invoke(question) → format_docs(docs) → ChatPromptTemplate(context, question) → llm.invoke()`，无 Agent。每个 Stage 打印输入、关键中间值和通过条件，避免最终答案掩盖检索问题。

运行 `python -m pytest -q` 验证确定性组件；运行 `python scripts/verify_all.py` 顺序执行 A–H。只有所有核心链路真实成功才输出 `02_RAG_PASS_LOCAL`，否则输出 `PARTIAL` 或 `BLOCKED` 和原因。
