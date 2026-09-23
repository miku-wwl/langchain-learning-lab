# LangChain 01 本地 E2E 设计

## 运行边界

- 使用 Python 3.13 和 LangChain 1.4.2，在本阶段目录建立独立虚拟环境。
- 通过 `src/model_factory.py` 把 LangChain `ChatOpenAI` 指向本机 Foundry Local OpenAI-compatible `/v1` 接口。运行时探测端口与已加载模型，不写死动态端口。
- Tool、StateGraph 与模板结构采用确定性断言；模型回复只检查结构和行为，不断言完整措辞。
- 教程涉及 LangGraph 和 MCP，因此只做一个最小预览实例；完整学习留在对应后续阶段。
- LangSmith 是可选观测平台，本地 E2E 不需要账号或 API key。

| Stage | 学什么与前置 | 最小输入 → 预期输出 | E2E 标准 |
| --- | --- | --- | --- |
| A Model | 模型抽象；无前置 | 用户文本 → 非空 AI 回复；`init_chat_model`、`ainvoke` 与 stream 也返回内容 | 四种调用实际触达本地模型 |
| B Prompt | 模板与消息；A | `language`、`text` → System/Human 消息和模型回复 | 模板变量正确展开，模型返回非空内容 |
| C Tools | `@tool`、schema、`bind_tools`；A | “计算 17+25” → `add` tool call | 工具直接得到 42，模型产生可解析的 `add` 调用 |
| D Manual loop | `ToolMessage` 和手工循环；C | “计算 17+25” → 工具执行、最终 AI 回复 | AI tool call → Python add → ToolMessage → AI；结果含 42 |
| E Agent | `create_agent` harness；D | 同一算术请求 → Agent 输出 | 返回消息中能找到实际工具调用与 ToolMessage |
| F Memory | 消息状态、checkpointer、thread；E | 同线程 Alice 两轮、另线程询问名字 | 同线程回答 Alice；隔离线程不读取 Alice；检查保存消息状态 |
| G Extensions | Middleware、Structured Output；E | 注入规则、请求结构化结果 | 中间件触发；结构化对象通过 schema 校验；若本地模型不兼容则如实报告 |
| H Graph | State、Node、Edge；无模型 | 初始数值 → 节点更新 → END | `compile().invoke()` 经过两节点且结果可断言 |
| I MCP | FastMCP、MCPAdapter；E | 算术请求 → 本地 MCP `add` | Adapter 发现工具；Agent 产生调用；server 执行并回传 ToolMessage |
| J LangSmith | tracing/eval 平台定位；无前置 | 阅读与配置说明 | 标记 OPTIONAL；不影响本地 E2E |

## 验证入口

每个 `src/stage_*.py` 可单独运行。`python scripts/verify_all.py` 依次运行全部关键 Stage，输出每项 PASS/PARTIAL/BLOCKED 以及最终 `LOCAL_E2E_PASS` 或 `PARTIAL`。`python -m pytest -q` 覆盖 Tool、Prompt、Tool dispatch、Memory state/thread isolation、Graph 的确定性行为。

只有 A–I 的必要本地链路真实执行成功，才输出 `LOCAL_E2E_PASS`。J 的状态为 `OPTIONAL / NOT REQUIRED FOR LOCAL E2E`。
