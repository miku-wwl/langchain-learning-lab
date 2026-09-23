# 06 教程知识点盘点

唯一 syllabus：[06 更新版原文](../../doc/06.LangChain_v1.4_LangGraph_v1.2_多智能体_更新版.md)。本章仅用合成医疗领域数据观察协调行为，不作医学判断。单次分类节点称 Router；Supervisor 是可反复调用子 Agent 的 `create_agent`。

| ID | Markdown 章节 | 知识点 | LLM | Tool | Graph | Multi-Agent | E2E 验证 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | 一 | Single Agent 何时足够 | 是 | 是 | 否 | 否 | 指南解释成本与取舍 |
| 02 | 一、五 | Worker Agent 独立职责 | 是 | 是 | 否 | 是 | A：三个 Agent 各自真实调用工具 |
| 03 | 二 | Router 是单次分类分发 | 否 | 否 | 否 | 是 | B：四类确定性输入 |
| 04 | 二、七 | Supervisor 是完整 Agent | 是 | 是 | 隐式 | 是 | F：工具调用、结果回传、最终答复 |
| 05 | 二 | Handoff 是控制权转移 | 可选 | 可选 | 可选 | 是 | 指南解释边界，不进入 07 |
| 06 | 二、六 | Custom Workflow | 否 | 是 | 是 | 是 | C/D：显式 StateGraph 路由、汇总 |
| 07 | 三 | 合成记录/指南/目录与拒绝 | 是 | 是 | 是 | 是 | A/C：真实本地调用；无关请求拒绝 |
| 08 | 五 | Record/Guideline/Doctor Agent | 是 | 是 | 否 | 是 | A：各自 Prompt、工具、结果 |
| 09 | 六 | Conditional Routing | 否 | 否 | 是 | 是 | C：只激活对应 worker |
| 10 | 六、十二 | Aggregate Node | 否 | 否 | 是 | 是 | D：worker_result → final_answer |
| 11 | 七 | Subagent-as-Tool | 是 | 是 | 隐式 | 是 | E：三个高层工具封装 worker |
| 12 | 七、八 | Tool Namespace Isolation | 是 | 是 | 否 | 是 | E：Supervisor 仅见 ask_* |
| 13 | 九 | Subagent specs | 是 | 是 | 否 | 是 | E：明确工具名和描述 |
| 14 | 九 | Subagent inputs | 是 | 是 | 否 | 是 | H：捕获 worker 输入仅为 task |
| 15 | 九 | Subagent outputs | 是 | 是 | 否 | 是 | H：只返回最终答复 |
| 16 | 九 | Context Isolation | 是 | 是 | 否 | 是 | H：无关主上下文不传播 |
| 17 | 十 | Multiple Subagent Calls | 是 | 是 | 隐式 | 是 | G：跨域调用两个不同子 Agent |
| 18 | 十 | Parallel Delegation | 是 | 是 | 隐式 | 是 | G：记录是否同轮多调用；可选 |
| 19 | 十三 | Failure Isolation | 是 | 是 | 否 | 是 | I：Doctor 失败、Record 成功 |
| 20 | 十三 | NO_DATA 与 EXECUTION_ERROR | 是 | 是 | 否 | 是 | I：区分工具无结果与异常 |
| 21 | 十一 | Router vs Supervisor | 是 | 是 | 是 | 是 | J：同一单域/跨域输入对比 |
| 22 | 十四 | 持久化/HITL/Time Travel | 否 | 否 | 否 | 否 | 明确留给 07，本章不实现 |

工作顺序是 Worker → Router → Router Graph → Aggregate → Subagent-as-Tool → Supervisor → 多委派 → 上下文/输出边界 → 故障边界 → 对比。`langgraph-supervisor` helper 不作为依赖。
