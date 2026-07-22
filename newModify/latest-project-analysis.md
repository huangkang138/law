# YYS-Law 最新项目解析

更新时间：2026-07-22 +08:00

本文件是当前完整项目状态的权威汇总；以当前源码为准。后续远程仓库更新或用户要求重新解析时，覆盖更新本文件，不再生成多个解析副本。

## 解析来源

- 当前源码与相关有效规划；`raw/archive/项目解析报告-20260610.md` 仅作历史对照。
- `D:\项目\law\flask_app\app.py`
- `D:\项目\law\flask_app\routers\__init__.py`
- `D:\项目\law\flask_app\core\config.py`
- `D:\项目\law\flask_app\core\database.py`
- `D:\项目\law\requirements.txt`
- `flask_app/routers`、`flask_app/services`、`flask_app/models` 的结构扫描

## 当前项目定位

本项目是一个智能法务服务平台，主要包含法律咨询、合同审查、模拟法庭、案情分析、相似案例/文书、纠纷处理、法律文书起草、法律工具计算、知识图谱和智能体管理等功能。

当前技术栈概览：

- 前端：Next.js、React、TypeScript、Tailwind CSS、Zustand。
- 后端：Flask、Flask-CORS、Flask-Sock、SQLAlchemy、Loguru、LangChain、OpenAI-compatible Chat API。
- 数据库：PostgreSQL。
- AI：通过 OpenAI-compatible 接口调用 DeepSeek 类模型。
- 实时能力：合同审查使用 SSE，模拟法庭/语音庭审使用 WebSocket。

## 产品聚焦与下一阶段规划（2026-07-21，文档决策）

当前确认的产品方向是“劳动用工法律服务”，以大学生实习、兼职和毕业初期青年劳动者作为第一批用户入口。青年就业是产品切入场景，不是新的技术 Domain；底层继续使用通用 Runtime 和 `cn_labor` 劳动领域能力包，未来可扩展普通劳动者、灵活就业者、平台用工和工伤等场景。

数字人和 Agent 的定位调整为：

- Agent 负责案件分流、材料和事实、证据、计划、工具、法源、计算、文书、审批和审计。
- 数字人负责通俗问答、逐个追问、材料上传引导、任务状态解释、语音和表现反馈。
- 两者在架构上解耦，在用户入口上逐步融合。通用普通聊天不会无条件启动任意法律 Agent；但已支持的劳动场景会创建/绑定 Matter、执行 Triage、校验 `recommended_task_type`、启动对应劳动 Agent Run，并同步 Workspace。非劳动领域的通用自动分流仍未实现。

LangGraph 与 Plan 的后续边界已经明确：

- 保持一套固定 `CapabilityRuntimeGraph`，不为欠薪、辞退、补偿等问题复制 Graph。
- 不同问题通过 Plan 组合能力：先分流任务和争议标签，再选择已审核的主 PlanTemplate，启用允许的可选步骤，处理依赖和公共步骤去重，最后生成不可变 Plan revision。
- 劳动关系判断、欠薪、解除和补偿应作为同一劳动 Domain Package 内的模板、规则和工具演进，不拆成多个顶级能力包或多个 Agent。
- 复合劳动案件由一个 Run 和一份版本化 Plan 管理；新增事实导致计划变化时创建新 revision，不覆盖旧计划。
- LLM 只允许提出分类、标签和步骤候选，不能自由创建工具或绕过模板、审批和验证策略。

下一阶段按以下顺序实施：

1. 3.7C已完成实现并进入用户验收：七类劳动材料适配、证据矩阵、实体规则、法源门禁与五类25条青年就业旗舰评测已落地；数字人工作台已打通材料建议、动态事实补录、缺失事实续跑、规则结果、审批和仲裁草稿。4个官方法源按用户指示以开发测试标识批准，健康状态 `ready`；正式环境仍须重新同步并完成真实法律专业复核。
2. 下一候选阶段是深化已打通的劳动数字人入口：一次一问、通俗状态/审批/法源阻断解释、运行进度、流式文字、取消和基础语音（3.7D），当前未启动。
3. 3.5 生产可信化暂缓但仍是未来必补项；复杂口型、Live2D 和新法律领域后置。

比赛版本只突出“青年就业劳动权益”旗舰闭环；合同、模拟法庭、知识图谱和其他旧页面保留为扩展能力，不与主线并列宣传。

### 阶段 3.7A：劳动案件分流与劳动关系初筛（2026-07-21）

- 后端已新增五类确定性分流：简单劳动咨询、劳动关系判断、正式劳动纠纷、非劳动纠纷和高风险人工处理。
- `LaborCaseTriageService` 使用独立 `labor_case_triages` 保存分流事实、结果和版本；关键输入同时写入版本化事实断言。Alembic 已升级到 `20260721_0008`。
- 新增 `labor_relationship_assessment` 模板和 `assess_labor_relationship` 工具；劳动 Domain Package 现有四个真实模板，继续共享同一通用 Runtime Graph。
- 初筛基于主体资格、有偿劳动、劳动管理、业务组成和就业目的，覆盖学校安排实习、勤工助学、自主实习、兼职、毕业就业和普通用工。学生身份、协议名称或欠薪关键词均不能单独触发仲裁流程。
- 分流结果保存争议标签、判断依据、缺失事实、问题、风险等级、推荐任务、下一步和人工复核标记，并固定声明不是最终法律结论。
- 新增 `GET/POST /api/digital-human/agent/matters/{matter_id}/labor/triage`。
- 阶段 3.7A.1 已打通聊天会话、Matter、分流、Agent Run 与右侧工作台：Matter 持久绑定 `session_id`；前端共享当前 Matter/Triage/Run；分流完成后校验并消费 `recommended_task_type`，分别启动劳动咨询、劳动关系判断或劳动案件分析模板；缺失事实、高风险和非劳动场景保持失败关闭。
- 完整数字人 Agent 测试 45/45、前端类型检查和隔离生产构建通过；同步修复阶段 3.4 测试 Provider 使用固定历史抓取时间导致七天后自然失效的问题。

### 阶段 3.7B：劳动争议组合式 Plan（2026-07-21）

- 当前仍只有一套 `CapabilityRuntimeGraph`。劳动案件按交付目的使用 `labor_case_analysis` 或 `labor_arbitration_application` 主模板，欠薪、解除、经济补偿由 `dispute_tags` 启用模板内白名单步骤，不创建独立 Graph、Domain Package 或无共享状态 Agent。
- 新增 `wage_arrears`、`termination`、`economic_compensation` 稳定标签和中文请求归一化；未知标签失败关闭。公共证据、统一期限/法源分析、审批和文书步骤在每份 Plan 中均只出现一次。
- 未启用问题步骤持久化为 `skipped` 并保存 `skip_reason`；Plan JSON 同时保存争议标签、组合契约版本和步骤触发标签，运行快照已同步这些字段。
- Capability Registry 新增定制后校验，禁止 Adapter 插步、删步、换工具、改依赖或削弱审批。用户补充事实使标签变化时，同一 Run 创建新的不可变 revision，并保留父 Plan 和原因。
- 三个问题工具只生成初步、需人工复核的结构化结果；最终期限和法源仍走公共劳动分析，经济补偿沿用项目既有估算公式。更完整的解除、工资、补偿实体规则属于 3.7C，本阶段没有提前实施。
- 新增阶段 3.7B 组合、安全与 revision 测试；完整数字人 Agent 回归 49/49、Python compileall 和前端 `tsc --noEmit` 通过。未新增表或列，无需数据库迁移。
- 验收中发现的解除日期/原因材料回填缺口和步骤状态歧义已修复；专项测试与完整回归通过，用户确认阶段无问题。3.7B 已正式完成。

### 阶段 3.7C：事实、证据、法源和实体规则（2026-07-22）

- 执行与签字基线见：[阶段3.7C合规测试与验收文档](./阶段3.7C合规测试与验收文档.md)。
- 劳动材料新增实习协议、劳动合同、Offer、解除通知、考勤、工资记录和聊天记录七类领域适配器；候选事实带文档类型、片段、偏移和原文，仍须用户确认。
- 新增证据矩阵，关联规则字段、已确认事实、材料支持、冲突和缺口，复用现有表，无数据库迁移。
- 欠薪、试用期、解除、经济补偿/违法解除赔偿、加班费拆为小型版本化领域规则；加班费按标准工时制区分工作日、休息日和法定节假日倍率，非标准工时制失败关闭；劳动关系工具同步返回事实、证据和法源引用。
- `LaborRuleDecision` 统一返回规则版本、判断、计算、事实/证据/法源引用、假设、警告和人工复核要求；缺关键事实或有效法源时失败关闭。
- `probation` 加入稳定争议标签和主模板白名单可选步骤；Runtime Graph仍只有一套。
- 五类青年就业旗舰评测共25条，明确区分合成金标与官方公开案例改写；评测强制全部经过关系分流 Runtime，5条复合争议继续经过材料、证据、实体规则与法源链路，覆盖七类材料。
- 数字人案件工作台已新增按争议类型展开的欠薪、试用期、解除、补偿/赔偿、加班费事实表单；材料候选可采用或编辑，缺失字段可续跑，5项实体规则计算、引用、警告和人工复核要求可直接查看；历史运行中的内部字段名也会转为中文，审批后生成仲裁申请书草稿。
- 聊天会话和案件工作台使用独立导航：聊天区保留历史会话与原有“+”入口，只通过标题栏“案件工作台”进入工作台，不再渲染底部重复摘要卡；工作台在任意步骤均可查看历史案件或新建案件。用户界面不再展示 Matter ID、内部模板名、Agent Run 或原始 JSON，只保留案件标题与中文处理状态。材料入口当前测试范围为 TXT 上传或粘贴真实材料原文，不再预置测试文件名，正式用户流程仍需补齐 Word、PDF 和图片 OCR；已审批生成的仲裁申请书草稿可在浏览器导出 Word 或 PDF，导出件继续标识为待复核草稿。
- 事实表单现在按争议类型标识必填项并实时列出尚缺信息；欠薪统一要求填写“欠薪总金额”和“欠薪开始日期”，其余辅助日期、月数明确标为选填，加班时数用段落说明至少填写一种，避免“二选一/至少一项”重复贴在字段上。基础事实独占整行，其余争议事实使用两列业务卡片并在窄屏转为单列。缺项时提交按钮直接显示缺项数量且不创建或续跑任务。复杂仲裁与案件分析模板将有界工具预算声明为24次，支持多轮事实补充，同时保留通用Runtime预算拦截和显式低预算测试覆盖。
- 阶段专项9/9、完整数字人Agent回归57/57、前端TypeScript检查通过；真实浏览器已完成加班费“创建案件→确认法域→上传材料→采用建议→补事实→规则分析”回归，8700元月工资、10/8/4小时三类加班、已付500元得到应付2150元和待付1650元，展示《劳动法》第四十四条，资源请求与控制台无错误。法源版本改按提取出的法律身份与正文计算，官网动态页面外壳不再制造伪更新。当前开发测试数据库法源4/4为 `ready`；批准记录为 `dev_test_approval`，不代表正式环境法律专业复核。

## 后端怎么看

后端入口是 `flask_app/app.py`，不是 FastAPI 入口。阅读后端建议按以下顺序：

1. `flask_app/app.py`
   - 创建 Flask app。
   - 配置 CORS。
   - 初始化 Flask-Sock。
   - 调用 `Base.metadata.create_all(bind=engine)` 检查/创建数据库表。
   - 注册各业务 Blueprint。
   - 注册 `/api/courtroom/ws/<session_id>` WebSocket。
   - 默认监听 `0.0.0.0:8001`。

2. `flask_app/routers/__init__.py`
   - 汇总导出 `analysis_bp`、`case_bp`、`dispute_bp`、`document_bp`、`document_drafting_bp`、`health_bp`、`knowledge_graph_bp`、`legal_bp`、`legal_tools_bp`、`favorites_bp`、`agent_bp`。

3. `flask_app/routers`
   - `health.py`：健康检查。
   - `legal.py`：法律咨询、会话查询、删除、重命名。
   - `document.py`：合同上传、合同审查、合同历史、SSE 流式审查。
   - `analysis.py`：模拟法庭、案情分析、相似文书、历史记录。
   - `dispute.py`：纠纷整理、取证、维权路径、文书生成、预测、提醒、风险预警。
   - `case.py`：相似案例搜索和历史。
   - `knowledge_graph.py`：知识图谱、节点、关系、结构、搜索和构建。
   - `document_drafting.py`：法律文书、合同、法律意见起草记录。
   - `legal_tools.py`：利息、劳动、交通事故、诉讼费、工伤、律师费、日历、时效、违约金、保全费、执行费、遗嘱、公证/公告、鉴定、仲裁、UML 等工具。
   - `favorites.py`：收藏。
   - `agent.py`：智能体 CRUD、聊天、使用统计、预设初始化。

4. `flask_app/services`
   - `legal_agent.py`：普法问答、会话上下文、LLM 调用、文书草拟。
   - `llm_factory.py`：LangChain ChatOpenAI 实例创建和 LLM 配置读取。
   - `courtroom_engine.py`：模拟法庭核心流程。
   - `courtroom_websocket_service.py`：WebSocket 庭审实时流程。
   - `case_service.py`：案例搜索、历史和详情。
   - `web_search_service.py`：当前更像内置模拟案例服务，不应直接理解为真实联网搜索。
   - `rag_service.py`：当前更像内存检索示例，不是真正落地的向量数据库检索。
   - `document_parser.py`、`contract_reviewer.py`、`debate_agent.py`：部分是简化或早期实现。

5. `flask_app/models`
   - `db_models.py`：主要 SQLAlchemy 表模型。
   - `knowledge_graph.py`：知识图谱相关模型和枚举。
   - `request.py`、`response.py`：Pydantic 请求和响应模型。

6. `flask_app/core`
   - `config.py`：从 `.env` 读取应用、LLM、CORS、日志配置。
   - `database.py`：创建 SQLAlchemy engine 和 session。
   - `logger.py`：Loguru 日志配置。

7. `sql/public.sql`
   - 用于核对 PostgreSQL 表结构、外键、索引和样例数据。

## 运行方式推断

后端：

```powershell
python flask_app/app.py
```

默认端口：`8001`

前端：

```powershell
cd frontend
npm run dev
```

默认端口：`3000`

前端 `next.config.js` 中存在 `/api/:path*` 到 `http://localhost:8001/api/:path*` 的 rewrite，但项目里仍可能存在直接写死 `localhost:8001` 的请求。

## 数字人智能助手现状

项目已新增全局数字人智能助手“法小助”的第一版前后端闭环，定位为全局导航、简单问答和专业功能分流，不属于复杂的工具调用型 Agent。

后端：

- `flask_app/routers/digital_human.py`：提供 `POST /api/digital-human/chat` 与 `POST /api/digital-human/reset`。
- `flask_app/services/digital_human_service.py`：复用 `LLMFactory` 调用 DeepSeek，拼接系统提示词、最近 6 条历史和当前问题，聚合流式输出并解析 `reply`、`intent`、`emotion`、`confidence`。
- 意图只允许从后端白名单中选择；后端根据意图补充 `route` 与 `route_label`，置信度低于 0.6 时不返回跳转地址。
- `flask_app/routers/__init__.py` 和 `flask_app/app.py` 已导出并注册数字人 Blueprint。
- `flask_app/models/db_models.py` 中已有 `DigitalHumanSession` 与 `DigitalHumanMessage` 模型，并补充了 `Float` 类型供 `confidence` 字段使用。
- `DigitalHumanService` 已接入 PostgreSQL：聊天前读取最近 6 条上下文；成功后以事务保存完整一轮；重置、会话列表、历史查询和删除接口均已提供。
- 阶段 0 已补充浏览器匿名 `client_id` 隔离：聊天、重置、列表、历史和删除接口均按客户端标识校验归属，未引入登录系统。
- 新增 `digital_human_requests` 幂等记录表；前端每轮生成 `request_id`，已完成请求可复用原响应，处理中请求返回冲突，失败请求清理占位。
- 已提供会话列表、历史消息读取和删除接口；前端从 PostgreSQL 恢复消息，localStorage 只保留当前会话 ID 和匿名客户端标识，并支持切换、删除、超时和取消等待。

前端：

- `frontend/src/components/DigitalHuman/`：包含悬浮入口、聊天面板和状态头像组件。
- `frontend/src/store/digitalHumanStore.ts`：使用 Zustand 持久化当前 `session_id` 与消息。
- `frontend/src/services/digitalHumanApi.ts`：封装数字人聊天和重置请求。
- `frontend/src/app/layout.tsx`：全局挂载数字人悬浮组件。
- `frontend/public/digital-human/first-gen/`：存放 8 张数字人状态图；当前通过状态图切换、呼吸、浮动、淡入和思考脉冲形成动态效果，不是逐帧或骨骼动画。

本地联调注意：Windows 环境可能将 `localhost` 优先解析为 IPv6 回环地址 `::1`，而 Flask 当前监听 `0.0.0.0:8001`（IPv4）。如果 Next.js 代理出现 `ECONNREFUSED ::1:8001`，应让代理明确使用 `127.0.0.1:8001`，并重启前端开发服务器。

## 数字人 Agent 阶段 1 Runtime

阶段 1 已实现最小可执行闭环，并与原数字人问答链路保持解耦：

- 新体系统一位于 `flask_app/legal_agent_system/`，由 `facade.py` 对 Router 暴露稳定门面；内部按 `runtime`、`tools` 分层，未提前创建后续法域和真实业务空模块。
- Runtime 使用 LangGraph 驱动规划、工具执行、审批暂停和完成节点；数据库中的 `state_json` 是跨进程恢复来源，安全限制、重试和审批有效性由确定性代码控制。
- 已定义 `AgentState`、`AgentTool`、`ToolResult`、运行/步骤状态和统一错误码；工具只能从 `ToolRegistry` 获取。
- 新增 `matters`、`agent_runs`、`agent_steps`、`tool_calls`、`approval_requests`、`agent_audit_events` 六张表，分别存储工作区、运行、步骤、工具调用、审批和审计事件。
- 模拟工具 `mock_case_summary` 首次调用产生可重试临时错误，第二次成功后进入审批暂停；用户确认可从 PostgreSQL 状态恢复并完成，拒绝或取消则进入取消状态。
- 新增 `/api/digital-human/agent/runs` 及运行查询、恢复、取消、审计接口；所有接口继续校验浏览器匿名 `client_id`。
- 数字人面板新增最小 Agent 任务卡片，可启动模拟任务、查看步骤、确认/拒绝审批、取消任务及查看完成摘要。
- 阶段 0 与阶段 1 PostgreSQL 集成测试共同通过；阶段 1 覆盖失败重试、审批暂停、跨 Facade 实例恢复、匿名隔离、完成和审计事件。

当前阶段仍只使用模拟工具，不接法律检索、材料解析、合同、纠纷、文书等真实法律能力；也尚未实现多步骤动态重新规划、工具预算和正式法域上下文。

## 数字人 Agent 阶段 2 材料与法律来源基础

阶段 2 已进入实施并完成第一批可追溯基础能力：

- 新增 `legal_agent_system/matters/`，以 Matter 和浏览器匿名 `client_id` 为边界保存授权材料；材料按字符偏移切成独立片段，工具只返回必要引用，不向下游传递无关全文。
- 新增 `agent_documents`、`document_fragments`、`legal_facts`、`matter_jurisdictions`、`legal_authorities` 表，分别保存材料、位置片段、带出处事实、法域确认和法律来源版本信息。
- `extract_legal_facts` 输出事实文本、置信度、材料 ID、片段 ID、字符起止位置和引用原文；`build_case_timeline` 只从已定位事实建立时间线；`generate_evidence_checklist` 明确区分已有材料和缺口。
- 新增中国 `CN` 法域包和法域注册中心；未注册法域会明确拒绝，不会静默回退到中国法。Matter 法域必须由用户显式确认后保存。
- 法律来源保存来源类型、法域、标题、条款、发布机构、来源 URL、生效区间、状态、检索时间和正文 SHA-256；引用校验同时检查法域、状态、日期和内容哈希。
- 来源状态为 `unknown`、已废止、已修改、日期不适用、法域不一致或哈希不一致时，校验结果为无效并返回明确警告，不包装成确定法律依据。
- 新增材料、事实、时间线、证据清单、法域确认和来源验证 API。原公开来源登记 API 已在阶段 3.4A 移除；Agent Runtime 也不再注册来源写入工具。
- 数字人面板已移除阶段 1 的模拟任务卡，新增独立的阶段 2 材料工作区：用户可创建案件、确认中国法域及省市、选择 TXT 或粘贴文字、解析材料，并展开查看每条事实的文件名、字符位置和原文引用；同时展示时间线、材料数量和证据提示。
- 材料工作区明确显示当前法律来源数量为 0，并提示尚未连接权威来源检索，不会伪造或自动生成法律条文。
- 阶段 0、1、2 真实 PostgreSQL 集成测试共 3 项通过；阶段 2 覆盖材料位置追溯、跨客户端隔离、时间线、证据清单、用户确认法域、未知来源降级和不支持法域拒绝。

当前材料入口先支持已经提取出的文本和 `text/plain` 闭环；前端文件选择器当前只接受 TXT。PDF、DOCX、图片/OCR 适配器、真实权威法律来源检索连接器和 LLM 事实抽取仍需在阶段 2 后续迭代补齐。当前确定性事实提取只识别日期、金额和显式“事实：”标记，用于验证引用结构，不等同于完整法律事实理解。

## 数字人 Agent 阶段 2.5 收口与首个真实工具

- Matter 已提供按 `client_id` 隔离的列表和删除接口；数字人材料工作区可展示已有案件、继续处理或删除，解决关闭面板后无法恢复入口的问题。
- 材料按 `matter_id + client_id + content_hash` 去重；相同内容不会重复创建材料和片段。事实提取重复调用会复用已有事实，不再生成重复记录。
- 原 `legal_tools.py` 中劳动补偿参数解析、公式和数据库写入已下沉到 `services/labor_compensation_service.py`，原法律计算器 Router 和 Agent 工具共用同一 Service，不复制公式。
- 新增真实工具 `calculate_labor_compensation`，通过统一工具注册中心执行，返回输入、公式、计算过程、估算结果、假设和风险警告。
- 劳动补偿工具只声明支持 `CN`，且执行前必须读取用户明确确认的 Matter 法域；未确认法域时拒绝执行。
- 数字人材料分析结果页增加劳动补偿估算表单，可输入月工资、工作年数和额外月份并调用项目现有能力。
- 阶段 0、1、2、2.5 PostgreSQL 集成测试共 4 项通过；2.5 测试验证案件恢复/删除、材料与事实去重、Agent 与原计算器 Service 公式一致。

当前劳动补偿仍沿用项目原有的简化公式，只作为初步估算，尚未根据解除原因、工资封顶、六个月折算等完整法律条件进行规则建模；前端和工具结果均明确展示该限制。

## 数字人案件工作台双模式

- 数字人普通模式保持原 384px 聊天窗口，只显示对话、头像和案件工作台摘要入口，不再把完整材料表单塞入小窗口。
- 点击顶部“案件工作台”或摘要卡“打开工作台”后，桌面端扩展为约920px，聊天与历史栏让位，案件、法域、材料、事实、时间线和工具独占整个内容区；顶部固定显示“返回对话”，可随时切回聊天。
- 移动端工作台使用接近全屏的单列布局，同样隐藏聊天和历史栏，工作区横向、纵向均铺满标题栏以下的可用空间。
- 新增 Matter 详情接口，恢复已有案件时会读取已确认法域；已确认案件直接显示绿色法域状态并进入材料步骤，未确认案件才显示一次性确认流程。
- 法域文案明确说明劳动补偿当前只支持中国法域，省市可选，用户只需确认一次“中国法域并继续”。
- PostgreSQL 阶段 0-2.5 回归测试共 4 项通过，新增断言验证恢复 Matter 时返回已确认的 `CN` 法域。

## 数字人 Agent 阶段 3：中国劳动纠纷闭环

- 新增 `legal_agent_system/labor_disputes/` 领域层，劳动纠纷事实使用独立 Pydantic Schema；关键事实不完整时返回缺失字段、自然语言追问和动态计划，状态保持 `awaiting_information`。
- 新增 `labor_dispute_profiles` 保存事实、缺失项、计划和审批状态，新增 `agent_artifacts` 保存带证据/来源引用的交付草稿；Router 仍只依赖 Facade，不直接编排业务。
- 劳动纠纷分析执行已确认 `CN` 法域、必要事实、材料证据清单和法律来源验证。未找到内容明确包含“仲裁时效”和“一年”的当前有效来源时，状态降级为 `blocked_authority`，不生成确定结论或文书。
- 期限工具根据用户确认的权利受损知悉日期作一年初步推算，同时明确中止、中断等情形必须人工复核，不把推算结果包装成最终法律意见。
- 只有用户显式审批后才能生成“劳动仲裁申请书（草稿）”；草稿保存为 `AgentArtifact`，包含法律来源 ID 和现有材料事实 ID，不执行提交、发送或代替用户作最终选择。
- 数字人案件工作台增加劳动纠纷事实表单、动态追问、来源拦截、期限提示、审批按钮和草稿预览；继续复用阶段 2 的 Matter/法域/材料能力和阶段 2.5 的劳动补偿工具。
- 阶段 1/2/2.5/3 PostgreSQL 集成测试共 4 项通过。阶段 3 覆盖缺失事实暂停、无权威来源阻断、有效测试来源验证、期限推算、拒绝隐式审批和草稿持久化。

当前法律来源仍来自已登记的结构化来源，尚未连接真实权威法律数据库；阶段 3 因此具备可验证的闭环协议和安全降级，但生产环境必须接入可信来源适配器后才能输出有依据的草稿。数据库仍使用 `create_all`，正式迁移框架尚待补齐。

### 阶段 3.1：劳动纠纷 Runtime 融合

- 历史阶段曾新增 `runtime/labor_graph.py` 与 `runtime/labor_runtime.py`；这两份旧内核已在阶段 3.6 删除，当前以唯一 `CapabilityRuntimeGraph` 为准。
- `AgentState` 已增加任务类型、风险级别、计划版本、当前步骤序号、缺失事实、用户问题、阻断原因和最终交付物 ID；运行状态增加等待法域、等待信息、验证、来源阻断、重新规划和人工接管。
- LangGraph 现会确定性执行法域检查、事实完整性检查、动态计划落库、证据清单工具、劳动纠纷分析工具、来源阻断、用户审批和草稿工具；三步计划真实写入 `AgentStep`，每次工具执行写入 `ToolCall`。
- 新增劳动纠纷统一继续动作：`confirm_jurisdiction`、`provide_information`、`retry_authority`、`approve`。等待节点和来源阻断均从 PostgreSQL 恢复，不依赖进程内 Graph 实例。
- 新增 `POST /api/digital-human/agent/matters/{matter_id}/labor-dispute/run` 和 `POST /api/digital-human/agent/runs/{run_id}/continue`；旧阶段 3 直接 Service API 暂时保留用于兼容和领域测试，当前前端主流程已经切换到 Runtime API。
- 数字人案件工作台现在显示权威 Agent 状态、真实步骤状态、动态追问、来源阻断、期限提示和审批内容；审批完成后从 Runtime 最终输出读取持久化草稿。
- 阶段 1/2/2.5/3/3.1 PostgreSQL 集成测试共 5 个模块、6 个用例通过。3.1 测试覆盖等待法域、等待事实、计划落库、真实 ToolCall、来源阻断与重试、跨 Facade 恢复、审批通过、审批拒绝和完成。

阶段 3.1 解决了劳动纠纷业务绕过 LangGraph 的主要架构缺口。

### 阶段 3.2：验证、预算和幂等安全边界

- 新增 `runtime/verifier.py`，对工具结果执行结构、事实、法律来源和风险四类确定性验证；验证失败统一转为 `VERIFICATION_FAILED`，并与原始工具结果一起写入 ToolCall，不记录模型思维链。
- 证据清单必须包含材料、缺口、定位事实数和警告；劳动分析必须进入审批状态、包含起算日/预计期限并关联已验证来源；草稿必须有 Artifact、`draft` 状态、来源引用和“未正式提交”声明。
- `AgentState` 增加最大步骤数、最大工具调用数和已调用计数；Graph 在生成计划和每次工具调用前检查预算，超过后以 `BUDGET_EXCEEDED` 停止并记录审计事件。
- 劳动仲裁草稿按案件、客户端、交付物类型和草稿状态幂等复用；重复请求返回原 Artifact 并标记 `deduplicated=true`，不会生成重复草稿。
- 新增阶段 3.2 安全测试，覆盖审批过期、零工具预算、草稿幂等和不可追溯分析验证失败。阶段 1/2/2.5/3/3.1/3.2 共 6 个测试模块、10 个用例通过。

当前统一 Runtime 的真实业务仍仅覆盖中国劳动纠纷；普通数字人可问答和导航到合同、模拟法庭、文书及其他旧模块，但这些模块尚未具备统一 Agent 的规划、工具审计、暂停恢复和验证闭环。后续仍需真实权威来源连接器、复杂劳动规则、独立计划版本表、总时长/费用预算、正式数据库迁移和更完整离线评测。

### 阶段 3.3：材料候选事实与用户确认

- 新增 `labor_disputes/suggestions.py`，从当前客户端已授权 TXT 材料和已定位事实生成劳动纠纷表单候选值；支持申请人、用人单位、入职日期、权利受损知悉日期、月工资、工作地点、争议类型和仲裁请求。
- 每个候选字段返回置信度、材料 ID、可选 fact ID 和来源原文；建议接口只读，不会自动写入 `LaborDisputeProfile`，用户明确采用或编辑后才作为确认事实提交 Runtime。
- 新增 `GET /api/digital-human/agent/matters/{matter_id}/labor-dispute/suggestions`。材料分析完成后前端自动读取建议并展示核对卡，用户可“采用材料建议”或“暂不采用，我自己填写”；采用后字段仍可修改。
- 阶段 3.3 测试验证字段提取、来源原文、匿名隔离和“读取建议不落确认事实”。阶段 1-3.3 共 7 个测试模块、11 个用例通过。

### 阶段 3.4A：来源信任边界、迁移基线与评测保护网

- 已确认采用方案 B“可信基础优先、平衡演进”；当前与目标架构图已保存到 `raw/`，每张图同时提供 Mermaid、SVG、PNG 和可编辑 Excalidraw。
- 总体规划已按当前源码刷新：阶段 0～3.3 标记为已完成基线，阶段 3.4 拆为安全/迁移/评测、可信来源、事实规则版本化、动态 Planner/ToolExecutor、受控 LLM 五个连续子阶段。
- 删除 `POST /api/digital-human/agent/legal-authorities`，普通客户端不再能够写入任意 `effective` 来源。
- `ToolRegistry` 不再注册 `register_legal_authority`，Agent 只能调用引用验证工具，不能自行制造法律来源。
- 测试来源改由 `LegalAuthorityService.register_test` 和 `Facade.register_test_authority` 注入，只接受 IANA 保留的 `.invalid` 域名；该方法不暴露为 HTTP 或 Agent 工具。
- 新增 `flask_app/alembic.ini` 与 `flask_app/migrations/`。首个 revision `20260713_0001` 是现有 PostgreSQL 的非破坏性接管基线；现有库使用 `stamp`，不重复创建或删除历史表。
- 当前启动流程仍保留 `Base.metadata.create_all` 兼容空库。后续新增结构必须写 Alembic revision；待形成完整初始迁移后再移除启动时自动建表。
- 新增 `flask_app/evals/labor_disputes/`，包含 Pydantic 评测 Schema、Runner 和 30 个完全虚构的 JSONL 案例，覆盖完整案件、八类单字段缺失和多字段缺失组合。
- 新增阶段 3.4A 基础测试，验证公开来源写入口被移除、测试来源拒绝真实域名、Agent 不具备来源登记工具、迁移基线存在及 30 个评测案例全部通过。
- 阶段 1～3.4A 共 8 个测试模块、15 个用例通过；Alembic `heads`、`history` 与离线 `upgrade head --sql` 验证通过。

### 阶段 3.4B～3.4E：可信闭环完成

- 建立 `AuthorityProvider`、官方劳动法源 Provider 和受控导入器；生产来源按 provider、external_id、版本幂等写入，并记录可信等级、规范 URL、验证时间和同步状态。普通 HTTP 与 Agent 仍不能登记来源。
- 新增 `20260713_0002` 非破坏迁移。迁移会检查已有表和字段，只补缺失结构；本地现有库已从基线接管并升级到 head。
- 确认事实改为版本化断言；劳动时效规则独立返回事实引用、法源引用、假设、警告和人工复核要求。草稿按事实、来源、规则和文书类型指纹幂等，相同输入复用，变化输入产生新版本。
- 动态 Planner 根据欠薪、违法解除等争议生成计划；计划版本独立持久化。统一执行器落实 Schema、法域、审批、超时和重试；继续操作支持幂等键，审计事件与 Outbox 在同一事务写入。
- 新增受控 LLM 候选抽取接口：只接受严格 Schema 且 quote/offset 与授权原文完全一致的候选，超出 token 预算直接拒绝；候选仍需用户确认。外部模型未配置时保持确定性提取，不会因模型不可用破坏现有闭环。
- 阶段 1～3.4 共 9 个相关测试模块、19 个用例通过；Python compileall、Alembic 实库升级与 head 检查通过。

下一步不是继续增加 Agent 自主权，而是扩充规则评测、运行官方法源同步、完成并发压测和 Outbox 消费监控，再评估阶段 4。

### 数字人数据库与前后端同步复核（2026-07-13）

- 数据库中不只有截图所示的 3 张 `digital_human_*` 表；这 3 张只保存聊天会话、消息和请求幂等。当前实库共有 20 张直接相关表，还包括 Matter、材料、事实、法域、法源、劳动档案、Run、Step、Plan、ToolCall、审批、草稿、审计、操作幂等和 Event Outbox。
- 已修复官方法源 Provider 只存在于测试、生产路径从不调用的问题。HTTP 使用的共享 Facade 默认开启官方劳动法源幂等同步；劳动任务启动前会准备来源，来源重试会先同步再重新规划。
- 已修复前端显示写死“0 法律来源”、继续提示“尚未连接”、重试按钮重复启动原流程的问题。现在展示实际验证来源、条款、发布机关和版本，并调用真正的 `retry_authority`。
- 已同步前端 Agent 预算字段和新版期限契约；期限支持空截止日期、假设、警告和人工复核标记。继续动作发送 `Idempotency-Key`，Flask CORS 已允许该请求头。
- 当前本地数据库已幂等导入 2 条官方劳动争议时效来源，均为 `trusted`；全链路回归共 20 个用例通过。
- 前端新增独立法源库状态：无需等到 Agent 分析成功，即可看到当前可用来源数量、法条、发布机关、版本和官方链接。界面明确说明当前是“官方白名单条款入库后结构化筛选”，不是临时联网搜索。
- 原“劳动补偿估算”和“劳动纠纷完整闭环”已改为两个有明确用途的功能：功能一只计算参考补偿金额；功能二检查证据、期限和法源，审批后生成仲裁申请书。原始英文状态和预算错误已转换为用户可理解的中文提示。
- 实际截图中的 `failed` 根因不是当前法源无效，而是旧 Run 连续重跑 4 轮、累计达到 8 次工具调用上限。界面现在阻止在来源阻断状态重复点击主流程，并引导使用来源重试；预算耗尽后明确创建新 Run。

### 阶段 3.5：生产可信化第一批（2026-07-13）

- `OfficialCnLaborProvider` 已从内置两条摘要改为真实官方来源适配器：使用白名单 HTTPS、限制响应大小和媒体类型，支持 HTML/PDF 原文解析；全国人大/人社主站连接异常时只允许切换到同属政府体系的明确备用来源，不允许回退到内置文本或模型生成文本。
- 新增 `authority_sync_runs` 与 `authority_source_snapshots`，记录同步状态、数量、错误、原始响应字节、内容哈希、媒体类型、ETag/Last-Modified 和验证方法；新增 Alembic `20260713_0003`。
- 法源首次官方抓取可进入 verified；相同正文只刷新核验时间；正文变化生成新版本并将新版本标记 `review_required`、旧版本标记 `superseded`。七天后未重新核验的来源自动失效，检索与 Verifier 均不能把它作为确定依据。
- 自动同步只在缓存不新鲜时访问官网；用户显式“重新验证”强制同步。同步失败写入批次，任务保持 `blocked_authority` 并返回 `AUTHORITY_SYNC_FAILED`，不会抛弃安全边界继续执行。
- 新增 PostgreSQL advisory lock：同一 Matter/任务的活动 Run 创建在事务锁内去重；同一 Run 的完整 Graph 执行持有 session lock，防止不同幂等键并发执行同一步工具。
- 工具超时改为 `TOOL_TIMEOUT_UNCERTAIN` 且禁止自动重试，因为 Python 工作线程超时后不能保证已经停止。
- 数据库连接只读取 `DATABASE_URL`；生产默认 `AUTO_CREATE_DB_TABLES=false`，启动不再静默演进结构。本地运行账号已按最小权限补齐，实库已非破坏性升级到 `20260713_0003`；迁移继续使用独立管理权限执行，不把 DDL 权限扩给运行账号。
- 劳动仲裁时效从固定 `+365天` 改为自然年推进；2月29日下一年落到2月28日。劳动关系存续欠薪返回开放期限类型而非伪造截止日期，并强制人工复核。
- 无数据库专项测试 6/6 通过，覆盖官方条文精确抽取、原始快照、缺条失败关闭、HTTPS/域名限制、自然年日期和超时不重试；真实官网连接在本机代理/TLS环境中存在间歇失败，失败关闭路径符合预期。

### 阶段 3.5：法源治理闭环第二批（2026-07-16）

- 新增内部法源 CLI：`authority sync/health/pending/review`。同步和严格健康检查在未全部就绪时返回非零退出码，可交给 Windows 任务计划程序、容器 CronJob 或监控系统；普通 HTTP 与 Agent 仍不能批准、驳回或写入法源。
- 新增 `authority_source_reviews` 表；法源正文变化必须由法律专业人员填写对照依据后批准或驳回，记录复核人、决定、说明、原始快照和时间。Alembic 已升级到 `20260716_0007`。
- 同步批次新增触发来源、执行者和失败来源数。Provider 改为逐来源失败关闭：单站失败不再让整批零进展，但失败来源仍不可用，健康状态只有全部必需来源新鲜且已验证时才为 `ready`。
- 修复实库历史快照唯一约束与“每批保存原始响应”冲突的问题；批次内仍按来源唯一，跨批次允许保存相同官网响应用于审计。
- 修复官网目录与正文重复条号、正文内引用其他条款导致的错误截断，改为优先识别行首条文标题并选择最长候选正文。
- 官方来源从两组仲裁时效条款扩展为四组，新增《劳动合同法》欠薪、解除、经济补偿、违法解除条款和《劳动法》第四十四条、第五十条、第九十一条；新增域名仅包含市场监管总局和国家税务总局法规库官方站点。
- 本地真实同步已抓取四组来源；截至3.7C加班费返修收尾，四组当前版本已按用户测试阶段授权以 `dev_test_approval` 批准，健康状态 `ready`（4/4）。正式环境仍须清库重同步并由法律专业人员逐条复核。
- 新增法源治理专项测试；数字人 Agent 全量 39 项测试通过，前端 TypeScript、Python compileall、迁移 head 与差异检查通过。

### 数字人数据库故障恢复与错误可见性（2026-07-14）

- 截图中的历史会话和案件记录没有被删除。当前浏览器匿名客户端在 PostgreSQL 中仍有 4 条会话、20 条消息和 7 条案件记录；此前“记录消失”是数据库运行账号不存在导致列表接口整体失败。
- 已创建专用非超级用户运行账号并授予现有业务表、序列和后续对象的运行权限；未修改或输出本地 `.env` 凭据。Alembic 实库版本已升级到 `20260713_0003`。
- 数字人聊天与 Agent Router 现在将数据库/驱动异常统一映射为 `503 DATABASE_UNAVAILABLE`，不再被 `ValueError` 误报成“请求参数格式错误”，也不再把底层编解码异常返回给前端。
- 历史会话与案件工作台不再静默吞掉加载失败：失败状态与“确实没有记录”分开显示，并提供原位重试；原左右双栏和窗口尺寸未调整。
- Loguru 关闭 `diagnose` 局部变量展开，保留回溯但避免数据库连接信息进入后续异常日志。

### 方案 C 最终 Agent 架构决策（2026-07-16，文档规划）

- 已确认长期目标采用“一套全局 Runtime Graph + Capability Registry + 多领域 Domain Package + 声明式 PlanTemplate + 每次运行独立 Plan revision”。本次只更新规划和架构文档，尚未修改 Runtime、数据库或 API。
- 当前源码事实保持不变：真实业务仍由中国劳动纠纷专用 `LaborDisputeGraph` 执行；`LaborPlanBuilder` 生成三步劳动模板，前两步由 `execute` 节点执行，审批后第三步由 `draft` 节点执行。该实现将作为首个迁移样板，不再被描述为通用 Planner。
- 目标 Runtime Graph 只负责上下文、任务路由、规划、单 Step 执行、Observation、分层验证、决策、审批、恢复、预算和审计，不包含仲裁申请书、合同审查等固定业务节点。
- `Domain Package` 通过 Capability Registry 注册路由规则、PlanTemplate、工具、验证策略和必要的可选 Subgraph，但不得控制全局 Run 状态。只有独立生命周期、多轮循环、中断恢复或独立审批的复杂能力才允许使用 Subgraph。
- `PlanTemplate` 是经审核的业务策略；`Plan` 是本次 Run 的版本化执行快照。重规划必须创建新 revision，不能覆盖旧计划；可选步骤必须记录跳过原因。
- 工具结果处理明确拆为 `execute_step → observe_step → verify_step → decide_step`。Verifier 分为 Global/Domain/Task 三层，只返回结构化报告；Decision Router 才能决定 next、retry、need_context、replan、approval、reject、handoff 或 finish。
- 迁移采取并行兼容方式：先完成方案 C 的注册和运行契约，再把现有劳动三步下沉为 `labor_arbitration_application` 模板，并补充劳动咨询、劳动案件分析；随后按法律咨询、合同审查、案件/纠纷、文书和其他工具逐个接入现有功能。
- 目标架构源文件已更新为 `raw/目标Agent架构图.mmd`；完整设计同步写入 `raw/多法域数字人法律Agent总体规划.md` 和 `flask_app/legal_agent_system/analyse-agents.md`。

### 阶段 3.6：方案 C Runtime 首批落地（2026-07-16）

- 新增 `capabilities/` 与 `domains/labor/`：Capability Registry 统一注册领域包、任务路由、三类 PlanTemplate、工具声明和验证策略；注册时校验模板工具白名单，拒绝重复或不完整能力。
- 新增 `CapabilityRuntimeGraph`，真实劳动入口现统一执行 `select → execute → observe → verify → decide` 单 Step 内核。业务工具和仲裁草稿不再是 Graph 节点，旧专用 Graph 已删除。
- 入口职责已进一步收口：Router 统一调用 `Facade.start_task/continue_task`；`CapabilityRuntime` 每次请求只调用一次 `CapabilityRegistry.resolve` 并把领域/模板绑定到 Run；Graph 已移除重复的 `route_task` 节点，只负责上下文、计划和单 Step 循环。旧劳动命名方法保留为兼容包装。
- 劳动能力包提供 `labor_arbitration_application`、`labor_consultation`、`labor_case_analysis`；旧 `cn_labor_dispute` 作为仲裁模板别名，原 Router、Facade 和前端页面保持兼容。只读咨询与案件分析不会进入文书审批或生成 Artifact。
- Verifier 拆为 Global/Domain/Task 报告，Decision Router 独立路由；步骤持久化 Observation、Verification、Decision、验证策略版本和可选步骤跳过原因。
- `agent_plans` 现在按行保存不可覆盖 revision、模板版本、父计划、重规划原因和触发者；Alembic `20260716_0004` 已应用到本地 PostgreSQL。
- API 新增能力查询，原劳动启动 API 新增可选 `task_type`；前端运行快照契约已同步模板、revision 和步骤审计字段。
- 阶段 3.1/3.2/3.6 相关 10 个用例通过，`npx tsc --noEmit` 和 `git diff --check` 通过。全量 30 个用例中另有 2 个既有环境/fixture 问题：Loguru 多进程管道被沙箱拒绝、官方来源残留快照撞唯一键；与本次 Runtime 改动无关。

### 阶段 3.6：领域解耦与旧架构清理（2026-07-16）

- 新增 `DomainRuntimeAdapter` 契约；`CapabilityRegistry` 必须成对注册领域声明和运行适配器。
- 劳动上下文判断、事实更新、法域、计划定制、工具参数和劳动校验已迁入 `domains/labor/adapter.py` 与 `verifier.py`；通用 Graph、Planner、Verifier 不再包含劳动规则。
- 阶段 1 模拟摘要已成为 `domains/mock/` 能力包。`Facade.start_run/resume_run` 保持 HTTP 兼容，但内部与劳动任务使用同一个 `CapabilityRuntimeGraph`。
- 已删除 `AgentRuntime/AgentGraph`、`LaborDisputeRuntime/LaborDisputeGraph` 和 `LaborPlanBuilder` 五个旧实现文件；当前仅保留一套 Agent 执行内核。
- 新增架构边界测试，持续禁止旧内核文件和 Runtime→领域 Service 直接依赖；README 文件索引与可编辑架构图已同步更新。

### 数字人启动恢复与模块导航（2026-07-16）

- 前端历史会话与案件记录同时报“数字人服务暂时不可用”的直接原因是 `127.0.0.1:8001` 未监听，不是记录被删除，也不是前端状态组件渲染失败。
- 后端启动先被受限 Windows 环境禁止创建 Loguru 多进程队列阻断；日志初始化现优先异步队列，遇 `PermissionError` 自动降级为同步输出。
- 启动链路还导入了未被 Flask 使用的 `routers/courtroom_websocket.py`，从而要求未安装的 FastAPI。主入口已移除该冗余导入；实际模拟法庭 WebSocket 继续由 Flask-Sock 服务注册。
- 数字人健康、历史会话和案件列表接口已恢复 HTTP 200。可选 OCR 栈仍有 NumPy/pyarrow 二进制兼容警告，但该导入异常被业务模块隔离，不再阻断数字人基础服务。
- `flask_app/legal_agent_system/README.md` 已建立当前目录导航，明确阶段 3.6 主链路、兼容旧链路、全部文件职责、扩展位置、数据库/测试入口和排错方式。

## 当前重要风险点

1. `requirements.txt` 标题和部分依赖仍偏 FastAPI，但当前主入口是 Flask。依赖清单需要与真实后端同步。
2. 数据库连接只从 `DATABASE_URL` 读取，源码不保存凭据；本机专用运行账号已可用。生产部署仍应分离运行账号与迁移账号，并定期轮换数据库凭据。
3. 多个业务模块复用 `/document/...` 路径，合同审查、纠纷文书、文书起草之间存在命名混淆风险。
4. `document.py`、`analysis.py`、`dispute.py`、`legal_tools.py` 文件较大，业务逻辑、LLM 调用、数据库操作混在 router 中，后续维护可以逐步下沉到 service 层。
5. 数字人后端会话以 PostgreSQL 为权威来源，前端 localStorage 只保存当前匿名客户端和界面状态；清除浏览器数据会生成新的匿名客户端，因此旧记录不会自动归到新客户端名下。
6. `raw` 中旧报告提到当前目录不是 Git 仓库，但现在 `D:\项目\law` 已识别为 Git 仓库，当前分支为 `master`。后续应以当前 Git 状态为准。
7. 数字人阶段 0 的代码能力已补齐浏览器级匿名隔离、历史恢复、删除、请求幂等、超时和前端取消；清除浏览器数据后会被视为新匿名用户。
8. 数字人阶段 0 已通过真实 PostgreSQL 专用集成测试，覆盖匿名隔离、历史读取、请求幂等和删除清理。完整 Flask 应用导入仍受其他旧模块环境影响：图像处理依赖与 NumPy 版本冲突，且模拟法庭 WebSocket 依赖 FastAPI；该问题不属于数字人链路。
9. 方案 C 的通用 Runtime、Capability Registry 和劳动三模板已首批实现，但跨领域与第二法域尚未接入；只能宣称“劳动领域已验证通用内核”，不能宣称完整多法域能力已完成。

## 后续解析和修改规则

- 每次项目解析或修改前，先读 `D:\项目\law\raw`，再读本文件。
- 每次远程仓库更新后，覆盖刷新本文件。
- 每次修改后，追加更新 `D:\项目\law\newModify\modification-log.md`。
- 涉及后端时，优先从 `flask_app/app.py` 和 `flask_app/routers` 进入，再追踪到 `services`、`models`、`core` 和 `sql`。
