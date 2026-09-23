# 02 RAG 本地验证报告

日期：2026-09-23。最终状态：**PASS_LOCAL**。结论仅针对本次虚构 FAQ、模型、问题与本机环境；Redis 为可选项，未运行。

## 环境与组件

| 项目 | 实测值 |
| --- | --- |
| OS / Shell | Windows / PowerShell |
| Python | 3.13.9，`02-rag/.venv` |
| LangChain | `langchain==1.4.2`，`langchain-core==1.6.4` |
| 相关集成 | `langchain-community==0.4.2`，`langchain-text-splitters==1.1.2`，`langchain-openai==1.6.4` |
| LangGraph | `1.2.12`，依赖安装但本章未使用 |
| Embedding 包 | `fastembed==0.8.1`，`onnxruntime==1.30.0` |
| 聊天模型 | Foundry Local `qwen3-4b-generic-gpu:2`；Foundry CLI `0.10.3`；本地 OpenAI 兼容端点，本次为 `http://127.0.0.1:53494/v1` |
| GPU | AMD Radeon 780M；Foundry Local 聊天模型使用 GPU 变体 |
| Embedding 模型 | `BAAI/bge-small-en-v1.5`，FastEmbed/ONNX，本机推理；384 维；缓存约 64 MB |
| 数据与向量库 | `resources/company_faq.txt`；`InMemoryVectorStore`，8 个 Chunk，`k=3` |

Foundry Local 端口由运行时发现，重启后可能变化。Embedding 首次下载模型文件，之后可以离线从 `.model_cache/` 载入。没有使用收费云模型、外部向量数据库或 01 目录代码。

## 执行命令

以下命令均在 `02-rag` 目录的 PowerShell 中执行。Stage A–H 是依次运行和检查的，最后另用统一入口复跑。

```powershell
python --version
foundry --version
foundry server status
foundry model list --cached
foundry model list --loaded
foundry model load qwen3-4b
python -m venv .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt --quiet
.venv\Scripts\python.exe src\stage_a_baseline.py
.venv\Scripts\python.exe src\stage_b_loader.py
.venv\Scripts\python.exe src\stage_c_splitter.py
.venv\Scripts\python.exe src\stage_d_embedding.py
.venv\Scripts\python.exe src\stage_e_vectorstore.py
.venv\Scripts\python.exe src\stage_f_retriever.py
.venv\Scripts\python.exe src\stage_g_rag.py
.venv\Scripts\python.exe src\stage_h_grounding.py
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -u scripts\verify_all.py
```

另在模型缓存建立后，以 `HF_HUB_OFFLINE=1` 重跑 Stage D，结果仍为 PASS，证明该次 Embedding 推理不依赖在线 API。单机首次准备依赖及下载缓存仍需要网络。

## 逐阶段实际结果

| Stage | 状态 | 实际观察与通过依据 |
| --- | --- | --- |
| A Baseline | PASS_LOCAL | 本地 Qwen3-4b 返回回答，说明无访问 Northstar Shop 内部政策，打印 `BASELINE_LOCAL_MODEL=PASS`。没有把“必须幻觉”作为通过条件。 |
| B Loader | PASS_LOCAL | `TextLoader` 从 TXT 加载 1 个 `Document`，打印完整 `page_content` 与带绝对来源路径的 metadata；`DOCUMENT_LOADER=PASS`。 |
| C Splitter | PASS_LOCAL | `RecursiveCharacterTextSplitter(chunk_size=180, chunk_overlap=25, add_start_index=True)` 产生 8 个 Chunk，打印各自内容、长度及 metadata；退款到账证据位于 `start_index=327`。另用控制文本观察到真实的 15 字符重叠；`TEXT_SPLITTER=PASS`。 |
| D Embedding | PASS_LOCAL | 真实生成 384 维向量并打印前 8 维；退款/退款余弦相似度约 `0.8687`，退款/天气约 `0.4193`，前者更高；`LOCAL_EMBEDDING_SEMANTIC_SIMILARITY=PASS`。离线重跑通过。 |
| E Vector Store + Similarity Search | PASS_LOCAL | 8 个 Chunk 进入 `InMemoryVectorStore`。退款到账问题的 Top-1 是 7 天申请期限（约 `0.8250`），Top-2 才是审批后 3–5 个工作日到账（约 `0.8055`），Top-3 为其他退款信息；打印 score、内容与 metadata；`INMEMORY_VECTORSTORE_SIMILARITY_SEARCH=PASS`。 |
| F Retriever | PASS_LOCAL | `retriever.invoke(question)` 的 Top-3 与直接 `similarity_search(question,k=3)` 内容、顺序一致；`RETRIEVER_MATCHES_DIRECT_SEARCH=PASS`。 |
| G 2-Step RAG | PASS_LOCAL | 先检索并展示原文和来源，再显式填充 `context`、`question` 后调用本地 Qwen3-4b。最终回答是原支付方式 3–5 个工作日到账；`TWO_STEP_RAG=PASS`。 |
| H Known | PASS_LOCAL | Top-K 含到账证据；回答 3–5 个工作日；`KNOWN_GROUNDING=PASS`。 |
| H Paraphrase | PASS_LOCAL | 同义问法仍检出到账证据；回答 3–5 个工作日；`PARAPHRASE_GROUNDING=PASS`。 |
| H Unknown | PASS_LOCAL | CEO 不在 FAQ；检索虽然返回其他片段，但模型答 `I cannot answer from the provided knowledge base.`；`UNKNOWN_GROUNDING=PASS`。 |
| I Redis | OPTIONAL / NOT RUN | 原教程将其作为可选 Vector Store 替换。本次完整核心链路已由内存向量库验证，无 Redis 依赖。 |

这组结果展示了检索与生成需要分开看：正确证据出现在 Top-2，模型仍在这次调用中选对了到账规则；Top-1 排名并不理想。未知问题仍会获得相似片段，因此拒答规则和实际回答都要检查。单次通过不等于对所有问题都可靠。

## 测试与 E2E

`python -m pytest -q` 的默认 Qwen3 配置复跑结果为 **8 passed, 1 warning in 3.61s**。测试覆盖 Loader、Chunk、Embedding 维度和相似度顺序、Vector Store、Retriever、已知与同义问法的证据检索、未知问题的 Prompt 约束和知识库缺失。测试对 LLM 的精确措辞没有断言。

`python -u scripts/verify_all.py` 依次启动 A–H 的真实进程，检查返回码和阶段通过标记。它实际调用 Foundry Local 模型与本地 Embedding，并输出 `Environment ... PASS`、各核心阶段 `PASS`、`Redis Vector Store ... OPTIONAL / NOT RUN` 和最终 **`02_RAG_PASS_LOCAL`**。这是本章 E2E 结果；它不代表 Redis、云服务或生产质量通过。

聊天模型原先是已缓存的 Phi-4-mini，完整 E2E 曾通过。本次用已缓存 Qwen3-4b 重新执行三类问答及统一 A–H 入口，均通过，因此改为默认聊天模型。当前 Foundry Local 将 Qwen3 的 `<think>...</think>` 与最终回答一起放在文本中；验证保留原始响应，学习时应分辨思考段和最终回答。这个输出形式和较长的生成时间是当前模型选择的限制。

## 原教程适配、修复与限制

| 原教程或准备阶段情况 | 本次处理与验证 |
| --- | --- |
| 手动填写动态 Foundry 端口和聊天模型 ID 容易失效 | `model_factory.py` 从当前 Foundry CLI 状态查找本地地址与已加载的 Qwen3-4b 模型；A、G、H 与统一脚本实测通过。 |
| 示例使用 `HuggingFaceEmbeddings` 和中文 `BAAI/bge-small-zh-v1.5` | 本章 FAQ 为英文，改用较小的 `BAAI/bge-small-en-v1.5` 和 `FastEmbedEmbeddings`；D–H 实测通过。这个变化是本地模型和语料的选择，不改变 Embeddings 接口的教学目标。 |
| 原文认为 `langchain-community` 不应简单视为落后 | 本次导入 `TextLoader`/`FastEmbedEmbeddings` 出现该包 sunset 的 `DeprecationWarning`；[官方维护公告](https://github.com/langchain-ai/langchain-community/issues/674)也说明迁移方向。目前固定 `0.4.2` 完成本教程；该集成将来需要复核迁移路径。该警告不导致运行失败。 |
| Hugging Face 首次下载在 Windows 上尝试创建符号链接遇到 `WinError 1314` | 下载器退回普通文件缓存后成功；模型文件下载完成，D 阶段及离线重跑通过。无需管理员权限。 |
| `TextLoader`、Splitter、`InMemoryVectorStore`、Retriever 的示例调用 | 在本次固定版本中实际运行成功，没有为了版本变化改写这些核心 API。 |
| 检索排序的质量限制 | Top-1 与问题相关但不是所问的到账时间；保留 Top-3 和可见分数，确保答案证据进入 Prompt，并如实记录。未将其包装成 Top-1 命中。 |

**Blockers：无。** `langchain-community` 的 sunset 警告和 Top-1 排序限制已记录；它们未阻断本次基础两步 RAG。最终状态 **PASS_LOCAL**。
