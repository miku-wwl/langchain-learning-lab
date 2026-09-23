# 06 本地 E2E 设计

运行环境：独立 `.venv`；Foundry Local 当前服务地址从 `foundry server status --output json` 动态发现；模型 ID 从 `foundry model list --loaded --output json` 发现。先试已缓存 GPU `qwen3-4b`，其最终结果误报 `NO_DATA`；改用同样已缓存且支持 Tool Calling 的 GPU `phi-4-mini`。工具只读 `resources/` 下的合成 JSON。无真实患者、诊断、治疗、云 API 或 01–05 代码依赖。

| Stage | 输入 | 执行链与关键证据 | 核心通过条件 |
| --- | --- | --- | --- |
| A Worker | 三条单领域任务 | `create_agent` → 内部 ToolMessage → 最终 AIMessage | 每个 worker 工具确实被调用 |
| B Router | record/guide/doctor/other | 纯 Python 关键词分类 | 四类准确 |
| C Graph | 四条同上 | StateGraph 条件边 → 对应 worker/refuse | 恰好正确 worker；final state |
| D Aggregate | 单个 worker_result | 独立 node 格式化 final_answer | 确定性汇总，不额外用 LLM |
| E Subagent Tools | 三类 task | ask_* → Worker Agent → 内部 Tool | schema 仅高层工具；实际执行 |
| F Supervisor | 三条单领域请求 | Supervisor AI tool_call → ToolMessage → final | 正确高层/底层工具均调用 |
| G Multi-delegate | 记录 + 目录 | 一个 Supervisor 调两个不同 ask_* | 两个结果进入最终答复；并行可选 |
| H Context | 主请求含无关信息 | 捕获 worker 实际 task；检查工具输出 | task 无无关历史；只回最终字符串 |
| I Failure | 模拟 Doctor 异常 + Record 成功 | wrapper 转结构化错误，Supervisor 保留部分成功 | NO_DATA 和 EXECUTION_ERROR 区分 |
| J Compare | 单域与跨域各一次 | 同一请求分别跑 Router/ Supervisor | 记录 worker 数、调用证据和适用边界 |

每段脚本自己断言并打印 PASS。确定性测试覆盖工具、路由、Graph、schema、上下文和错误边界；模型输出只检查 `tool_calls`、消息类型、实际工具执行和结果证据，不断言自然语言逐字相同。`scripts/verify_all.py` 运行各 Stage 并检查标记，全部核心阶段通过才输出 `06_MULTI_AGENT_PASS_LOCAL`。并行 delegation 只作为增强项。
