# YYS-Law 最新项目解析

更新时间：2026-07-12 20:22:45 +08:00

本文件是后续项目解析和项目修改前需要优先阅读的最新汇总。它基于 `D:\项目\law\raw\项目解析报告.md` 与当前仓库只读检查生成。后续远程仓库更新或用户要求重新解析时，覆盖更新本文件，不再生成多个解析副本。

## 解析来源

- `D:\项目\law\raw\项目解析报告.md`
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
- 新增材料、事实、时间线、证据清单、法域确认、来源登记和来源验证 API；相关能力已包装进统一工具注册中心。
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
- 点击顶栏展开按钮或“打开工作台”后，桌面端扩展为约 920px 的左右双栏：左侧保留聊天，右侧独立显示案件、法域、材料、事实、时间线和工具；工作台拥有单一滚动区域，消除原先聊天和材料卡双重滚动。
- 移动端展开后使用接近全屏的上下布局，并隐藏大头像以给聊天和案件操作留出空间。
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

- 新增 `runtime/labor_graph.py` 与 `runtime/labor_runtime.py`，现有阶段 1 模拟 `AgentGraph` 保持兼容；劳动纠纷任务使用独立 `task_type=cn_labor_dispute`，但共享统一 Repository、ToolRegistry 和审计模型。
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

## 当前重要风险点

1. `requirements.txt` 标题和部分依赖仍偏 FastAPI，但当前主入口是 Flask。依赖清单需要与真实后端同步。
2. `flask_app/core/database.py` 存在硬编码数据库连接信息。后续文档和提交不要泄露具体密码，应迁移到环境变量。
3. 多个业务模块复用 `/document/...` 路径，合同审查、纠纷文书、文书起草之间存在命名混淆风险。
4. `document.py`、`analysis.py`、`dispute.py`、`legal_tools.py` 文件较大，业务逻辑、LLM 调用、数据库操作混在 router 中，后续维护可以逐步下沉到 service 层。
5. 数字人后端会话已经以 PostgreSQL 为权威上下文来源，但前端仍通过浏览器 localStorage 保存当前消息；后续增加历史读取接口时，需要明确前端与数据库的同步策略。
6. `raw` 中旧报告提到当前目录不是 Git 仓库，但现在 `D:\项目\law` 已识别为 Git 仓库，当前分支为 `master`。后续应以当前 Git 状态为准。
7. 数字人阶段 0 的代码能力已补齐浏览器级匿名隔离、历史恢复、删除、请求幂等、超时和前端取消；清除浏览器数据后会被视为新匿名用户。
8. 数字人阶段 0 已通过真实 PostgreSQL 专用集成测试，覆盖匿名隔离、历史读取、请求幂等和删除清理。完整 Flask 应用导入仍受其他旧模块环境影响：图像处理依赖与 NumPy 版本冲突，且模拟法庭 WebSocket 依赖 FastAPI；该问题不属于数字人链路。

## 后续解析和修改规则

- 每次项目解析或修改前，先读 `D:\项目\law\raw`，再读本文件。
- 每次远程仓库更新后，覆盖刷新本文件。
- 每次修改后，追加更新 `D:\项目\law\newModify\modification-log.md`。
- 涉及后端时，优先从 `flask_app/app.py` 和 `flask_app/routers` 进入，再追踪到 `services`、`models`、`core` 和 `sql`。
