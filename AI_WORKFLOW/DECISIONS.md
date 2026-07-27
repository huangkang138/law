# 关键决策

| ID | 决策 | 状态 | 原因 | 当前影响 |
| --- | --- | --- | --- | --- |
| D001 | 一套固定 Runtime Graph + 可插拔 Domain Package + 版本化 Plan | ACTIVE | 避免按案件复制状态机。 | 新领域注册能力包与 Adapter，不复制 Graph。 |
| D002 | 劳动用工是首个领域，青年就业是产品入口 | ACTIVE | 聚焦首个可信闭环。 | 核心不写死为校园系统。 |
| D003 | 法律结论失败关闭 | ACTIVE | 法源、法域、关键事实不完整不能确定输出。 | 补信息、阻断或人工接管。 |
| D004 | Chat ↔ Matter ↔ Triage ↔ Run 是劳动入口主线 | ACTIVE | 分流必须决定 Runtime 行为。 | 会话当前 Matter/Run 映射与工作台同步。 |
| D005 | 复合争议采用主模板 + `dispute_tags` + 白名单步骤 | ACTIVE | 共享证据、法源、审批和审计。 | 公共步骤按 `step_id` 去重，计划变化新增 revision。 |
| D006 | 用户目标高于 CURRENT_TASK，任务需显式晋级 | ACTIVE | 防止旧任务截断新目标或文档初始化误报完成。 | Promote 后进入模式；REVIEW 核验真实目标、代码与验收。 |
| D007 | 劳动材料、证据和实体规则在 Domain 内模块化，优先复用既有事实与引用表 | ACTIVE | 保持 Runtime 通用并避免为单一领域扩张数据库。 | 文档适配、证据矩阵和规则版本均由 `cn_labor` 管理；通用 Graph 不感知劳动法细节。 |
| D008 | 3.7D只建设统一会话基础，Router决策与Orchestrator执行分离 | ACTIVE | 避免前端关键词分流、普通聊天和Agent入口继续分叉，也避免会话层污染正式案件事实。 | Conversation Memory只保存用户陈述/候选信息；单一Orchestrator通过现有Matter、Triage和Agent Facade执行受控动作；流式、语音与工作台模式按3.7E～3.7H后置。 |
| D009 | Rolling Summary采用可读文本与结构化条目双层表示 | ACTIVE | 单一大字符串无法可靠处理用户修正和正式事实冲突。 | `summary_text`仅作可读投影；`summary_items`保存类型、来源、状态与替代关系，ContextBuilder按条目排除冲突并重建文本。 |
