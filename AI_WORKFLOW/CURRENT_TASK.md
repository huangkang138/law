# 当前任务

- 阶段/任务名称：阶段 3.7D——Conversation Foundation（统一会话基础）。
- 当前状态：`COMPLETED`。用户已确认进行3.7D收尾；REVIEW三个P1、专项验证、阶段回归和完整测试均已关闭。
- 目标：在不重写 `CapabilityRuntimeGraph` 的前提下，为普通聊天与案件陪伴建立唯一会话入口，补齐 Raw Messages、Token Budget Recent Window、Structured Memory、ContextBuilder、Rolling Summary、Router 和 Conversation Orchestrator。
- 当前问题/背景：后端 `DigitalHumanService` 同时承担历史读取、Prompt、LLM、意图和持久化，且固定只取最近6条消息；前端 `DigitalHumanChat` 在 `sendMessage` 后再用 `isLaborQuestion` 触发 `useLaborTriage.start`，普通回复、Matter创建、分流和Agent启动存在两个决策入口。
- 已确认决策：3.7D按新版拆分只建设 Conversation Foundation；Streaming/统一取消属于3.7F，STT/TTS属于3.7G，Trace/Guardrails/Evaluation属于3.7H。会话记忆不等于 Matter 正式事实；Assistant 内容不得成为案件事实来源；LLM只能建议路由，`labor_triage`业务副作用必须由当前用户输入的服务端确定性规则授权。会话 advisory lock 只覆盖短数据库临界区；request 通过租约和动作检查点恢复 Matter/Triage/Run。
- 允许修改范围：新增独立 Conversation 服务包、会话记忆与消息预算所需模型及Alembic迁移、`digital_human.py`/`digital_human_service.py`兼容入口、数字人API契约、前端单入口收口、对应测试和项目文档。
- 禁止范围：不得修改或复制 Runtime Graph、劳动 Domain Package、Plan、Tool、Verifier 和审批协议；不得让聊天记忆覆盖 Matter 已确认事实；不得因劳动关键词自动创建空 Matter；不得提前实现流式文字、实时取消、语音、数字人动画或3.7E工作台模式重构；不得放松法源、法域、高风险、审批、人工复核和审计边界。
- 推荐设计：`services/conversation/` 分为 `schemas`、`token_budget`、`memory`、`context_builder`、`router`、`orchestrator`、`actions` 和 `repository`；`DigitalHumanService` 降为兼容 Facade。新增每会话一行的版本化 Memory 快照，Rolling Summary同时保存可读 `summary_text` 和带类型、来源、状态及替代关系的 `summary_items`，不通过切割摘要字符串处理冲突；消息保存保留来源与幂等关联；ContextBuilder按固定优先级组装上下文；Router输出封闭决策，Orchestrator经现有 Matter/Triage/Agent Facade执行动作。
- 验收描述：30～50轮后目标识别正确且输入Token趋于稳定；Rolling Summary重要事实可按类型和来源定位，用户修正旧陈述后旧摘要条目失效并重建可读文本，且不覆盖正式事实；Assistant推测进入正式案件事实数量为0；同一输入只经过一个Router/Orchestrator主流程；普通咨询不创建Matter；高风险、法源不足和审批继续失败关闭；现有聊天历史、请求幂等和3.7C劳动闭环回归通过。
- 下一动作：无。等待用户明确指定下一阶段；不得自动进入3.7E。
- 关联基线：`raw/多法域数字人法律Agent总体规划.md`、`newModify/latest-project-analysis.md`、`flask_app/services/digital_human_service.py`、`frontend/src/components/DigitalHuman/DigitalHumanChat.tsx`、`frontend/src/components/DigitalHuman/useLaborTriage.ts`。
