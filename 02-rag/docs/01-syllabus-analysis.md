# 02 教程知识点盘点

原文：[02.LangChain_v1.4_02_RAG_更新版.md](../../doc/02.LangChain_v1.4_02_RAG_更新版.md)。原文为本章 syllabus，保持不变；本 Lab 的范围是最基础的两步 RAG。

| ID | 原文章节 | 知识点 | 有代码 | 需 LLM | 需 Embedding | 需 Vector Store | E2E 验证 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | 一.1 | RAG 解决外部知识缺失；与 Fine-tuning 的区别 | 否 | 否 | 否 | 否 | 学习指南解释；Stage A 留下无知识库基线 |
| 02 | 一.2 | Indexing：原始文件到向量索引 | 图 | 否 | 是 | 是 | B–E 逐层运行并输出中间结果 |
| 03 | 一.2 | Retrieval + Generation：问题到有依据的回答 | 图 | 是 | 是 | 是 | F–H 真实检索、拼接上下文、生成答案 |
| 04 | 一.3 | 无 RAG 的本地模型基线 | 是 | 是 | 否 | 否 | Stage A 记录模型原始回答，不要求幻觉 |
| 05 | 二.1 | LangChain 1.4.2、集成包与本地依赖 | 命令 | 否 | 否 | 否 | 独立虚拟环境安装与版本记录 |
| 06 | 二.2 | 小型企业知识文件 | 数据 | 否 | 否 | 否 | 本地 `resources/company_faq.txt` 覆盖退款、配送、会员、支持 |
| 07 | 二.3、三.1 | `TextLoader`、`Document.page_content`、metadata | 是 | 否 | 否 | 否 | Stage B 输出 Document 数量、正文与来源 |
| 08 | 三.1 | 其他 Loader / `UnstructuredLoader` 的定位 | 示例 | 否 | 否 | 否 | 解释适用范围；PDF/Office 不在本地样本范围 |
| 09 | 二.4、三.2 | `RecursiveCharacterTextSplitter`、Chunk、`chunk_size`、`chunk_overlap`、`start_index` | 是 | 否 | 否 | 否 | Stage C 输出各 Chunk 和 metadata，验证数量、大小、重叠配置 |
| 10 | 二.5、三.3 | Embedding 接口、向量维度、余弦相似度、索引/查询模型一致 | 是 | 否 | 是 | 否 | Stage D 真实向量与相关/无关文本相似度排序 |
| 11 | 二.6、三.4 | `InMemoryVectorStore` 保存 Chunk/向量/metadata；与 Embedding 的区别 | 是 | 否 | 是 | 是 | Stage E 构建索引并检查条目 |
| 12 | 二.7 | `similarity_search`、`similarity_search_with_score`、Top-K | 是 | 否 | 是 | 是 | Stage E 已知退款问题取回相关 Chunk，显示分数和来源 |
| 13 | 二.8、三.5 | `as_retriever`、`retriever.invoke`；与直接 Vector Store 搜索的区别 | 是 | 否 | 是 | 是 | Stage F 输出 Top-1/Top-2 并比对直接搜索 |
| 14 | 二.9 | Prompt 的 `context` 和 `question`、grounding 规则 | 是 | 否 | 否 | 否 | Stage G 检查模板变量并显示实际上下文 |
| 15 | 二.10 | 显式 `retrieve → format_docs → prompt → llm` 两步 RAG | 是 | 是 | 是 | 是 | Stage G 真实完整调用，答案由检索证据支持 |
| 16 | 二.11、四.2 | Known、Paraphrase、Unknown 三类问题 | 是 | 是 | 是 | 是 | Stage H 分别检查检索证据、答案与拒答 |
| 17 | 四.1、四.3 | 先测 Retrieval 再测 Generation；Hit@K 等指标的基本认识 | 概念 | 否 | 是 | 是 | 验证报告分别记录检索与生成结果；高级评测仅解释 |
| 18 | 五 | Redis Vector Store 是可选替换 | 安装示意 | 否 | 是 | 可选 | 本次标记 OPTIONAL / NOT RUN，不影响主链路 |
| 19 | 六至八 | 推荐学习顺序、抽象职责、版本迁移 | 图/文字 | 否 | 否 | 否 | 学习指南、README 与验证报告逐项映射 |

## 本地化与版本处理

| 原文示例 | 本 Lab 处理 |
| --- | --- |
| 手动设置动态 Foundry 端口、聊天模型 ID | 独立 `model_factory.py` 读取当前 Foundry CLI 状态；不依赖 01 代码。 |
| `HuggingFaceEmbeddings("BAAI/bge-small-zh-v1.5")` | 本机无已缓存 Embedding 模型；先选择体积较小的本地 ONNX FastEmbed 英文模型和英文小型 FAQ，仍通过 LangChain Embeddings 接口验证真实语义向量。模型、包与版本在报告记录。 |
| Redis 作为可选存储 | 主路径使用 `InMemoryVectorStore`；本次不为 Redis 增加服务依赖。 |
| `UnstructuredLoader` 用于 PDF/Office | 本章只有 TXT 样本，说明该集成的定位，不安装与运行无关的 PDF 依赖。 |
| 原文称 `langchain-community` 不应简单视为落后 | 当前安装的 0.4.2 实际发出 sunset `DeprecationWarning`，官方仓库已归档；本 Lab 固定版本以复现 `TextLoader` 与 `FastEmbedEmbeddings` 示例，并在验证报告记录这一版本变化。 |

原文中的 API 示例先按实际安装的 LangChain 1.4.2 环境验证；若发现行为差异或失败，记录原写法、原因、修改与重跑证据到 `04-verification-report.md`。
