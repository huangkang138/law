# 律知项目架构与流程｜GPT 交接材料

> 整理日期：2026-09-20。项目目录：`D:\项目\law`。本文件供未接触过项目的 GPT 快速建立**全项目**上下文，内容依据当前仓库源码核对。它描述代码已接入的结构和流程，不代表本次已启动服务、验证全部页面或确认线上环境状态。

## 0. 给接手 GPT 的使用说明

先把本文件作为项目地图使用，再针对具体任务打开文中列出的源码。**源码和用户本轮要求优先于本文**；不要把规划文档当成已上线能力，不要把劳动 Agent 的约束套到所有旧业务模块上。遇到需求时先确认目标页面、Router、Service、数据表和真实调用链，并保留工作区已有改动。本文不包含环境变量、密钥或真实用户数据。

## 1. 项目定位与当前范围

律知是一个综合智能法律服务平台。全站功能包含法小助咨询、合同审查、案情分析、相似文书与案例参考、纠纷整理与纠纷中心、通用文书起草、模拟法庭、法律图谱、法律计算工具、历史记录、收藏和智能体管理。各功能共享前端、Flask API 和 PostgreSQL，但并非共享一条业务流水线。

其中，**青年就业劳动权益**是当前最深入的业务主线：对话中识别明确办案意图；围绕 Matter（案件）做劳动关系和争议分流；进入工作台整理材料、确认事实与证据；由受控 Agent 执行规则、法源、计算与审批；最终形成待人工复核的草稿。实习、兼职、毕业就业是切入场景，底层属于同一个中国劳动领域能力包。非劳动法域的自动办案闭环尚不能从当前代码确认。

平台定位是法律事务辅助。生成的回答、计算、分析及文书需要核对事实和法律依据；工作台生成的仲裁申请书是草稿，不会自动向机构提交。

## 2. 一张图看全局

```text
浏览器
├─ Next.js App Router：页面、组件、Zustand 状态、Rive 数字人
│  ├─ 独立功能页面：合同、分析、纠纷、文书、法庭、图谱、工具等
│  └─ 法小助咨询 + 案件工作台：共享会话/当前案件上下文
│
├─ HTTP /api；数字人和合同等流式输出使用 SSE；模拟庭审有 WebSocket
↓
Flask app.py 注册业务 Blueprint
├─ 旧业务 Router/Service：咨询、合同、分析、纠纷、文书、图谱、计算等
├─ Conversation：消息、记忆、上下文、分流、受控动作、语音事件
└─ Legal Agent：Facade → Capability Registry → 通用 Runtime Graph
                  → 劳动领域 Adapter → 白名单 Tool → 规则/业务 Service
                  → 验证、决策、审批、持久化
↓
PostgreSQL（SQLAlchemy ORM，Alembic 迁移）
├─ 各旧业务的独立记录
└─ Session / Workspace / Matter / Material / Fact / Run / Plan / Authority / Artifact

其他依赖：上传文件卷、外部模型接口、语音服务、官方法源同步服务。
Docker Compose 部署：Nginx → Next.js / Flask；PostgreSQL 为后端数据层。
```

**重要边界**：数字人负责交互与解释；Conversation 决定回答、追问或经授权的办案动作；Agent Runtime 才负责正式案件任务。合同审查、旧纠纷中心和模拟法庭有自己的 Router/Service，不会默认进入该 Runtime。

## 3. 技术栈与部署链路

| 层 | 当前代码中的技术 | 职责 |
| --- | --- | --- |
| 前端 | Next.js 14、React 18、TypeScript、Tailwind CSS、Zustand | 路由页面、交互、共享状态；`@rive-app/react-webgl2` 播放数字人资源 |
| 后端 | Python、Flask、Flask-CORS、Flask-Sock、SQLAlchemy | HTTP API、SSE、模拟法庭 WebSocket、业务服务和持久化 |
| AI | LangChain / LangGraph、OpenAI-compatible 模型接口 | 自然语言理解与回复；Agent 图的受控执行由服务端代码约束 |
| 数据 | PostgreSQL、Alembic | 业务记录、会话、案件、Agent 过程、法源和审计 |
| 部署 | Docker Compose、Nginx、前后端 Dockerfile | `nginx` 对外；`/` 到 Next.js，`/api/` 到 Flask |

本地开发中 [next.config.js](../frontend/next.config.js) 把 `/api/:path*` 转到后端；Compose 部署中 [nginx.conf](../deploy/nginx.conf) 把 `/api/` 转到 `backend:8001`，其他请求转到 `frontend:3000`。Flask 入口是 [app.py](../flask_app/app.py)，默认监听 8001。数据库连接由后端配置读取；正式结构由 Alembic 管理，`AUTO_CREATE_DB_TABLES` 只是在显式开启时兼容本地空库。部署配置存在不等于目标环境已完成迁移、法源审核或模型连通性验证。

## 4. 目录地图与代码职责

```text
frontend/
  src/app/                 Next.js 页面与根布局
  src/components/          首页、顶栏、数字人和工作台组件
  src/store/               Zustand 状态（不同业务 Store）
  src/services/            数字人/Agent 请求封装
  src/lib/                 前端辅助能力、语音播放器、导出等
  public/                  Logo、Rive 等公开资源
flask_app/
  app.py                   Flask 装配、Blueprint 注册、庭审 WebSocket
  routers/                 各 HTTP 业务入口
  services/                旧业务 Service、Conversation、Voice、材料处理
  legal_agent_system/      Matter、劳动领域、法源、Runtime、Tool
  models/                  SQLAlchemy 旧业务与部分 Agent 模型
  migrations/versions/     Alembic revision
  tests/                   后端专项和回归测试
deploy/nginx.conf          部署反向代理
docker-compose.yml         PostgreSQL、后端、前端、Nginx 服务编排
AI_WORKFLOW/               项目协作规则与当前任务记录
newModify/                 项目分析与修改记录
法律AI/模块地图/             已整理的重点模块调用地图
raw/                       架构规划与历史资料；规划不等于实现
```

前端根布局 [layout.tsx](../frontend/src/app/layout.tsx) 挂载全站顶栏和 `DigitalHumanFloat`。`/chat` 页面由 [chat/page.tsx](../frontend/src/app/chat/page.tsx) 指向 `DailyConversationPage`；案件工作台由顶栏动作打开，而不是独立 `/case-workspace` 页面。首页四个主入口由 [page.tsx](../frontend/src/app/page.tsx) 定义。后端所有 Blueprint 由 [app.py](../flask_app/app.py) 注册；`routers/__init__.py` 汇总导出。

## 5. 全站功能地图：页面、接口、职责

下表列的是**主要入口**，不是每个 Router 的完整端点列表。API 路径以 `app.py` 注册后的实际 `/api` 前缀为准；`agent.py` 和 `favorites.py` 自带 `/api` 前缀。

| 功能 | 前端页面或组件 | 后端主入口 | 处理和数据特点 |
| --- | --- | --- | --- |
| 首页和导航 | `/`、`TopNavbar.tsx` | 无固定首页业务 API | 四张功能卡进入现有路由；顶栏展开其他功能；工作台入口执行 Store 动作 |
| 法小助咨询 | `/chat`、`DigitalHumanFloat` | `digital_human.py`，如 `/api/digital-human/chat/stream`、`/sessions` | 多轮消息、会话历史、Workspace 上下文、语音/Rive 状态；受控劳动分流 |
| 劳动案件工作台 | `CaseWorkspaceShell`、四个 Stage | `digital_human_agent.py`，`/api/digital-human/agent/...` | Matter、材料、事实、法域、Run、审批、草稿、法源 |
| 合同审查 | `/contract`、`contractStore.ts` | `document.py`，`/api/document/upload`、`/review`、`/review/stream` | 上传合同、提取文本、审查风险、历史和详情；独立于劳动 Agent |
| 法律案情推断 | `/case-analysis` | `analysis.py`，`/api/analysis/case-analysis` | 案情分析与历史 |
| 相似法律文书 | `/similar-documents` | `analysis.py`，`/api/analysis/similar-documents` | 相似文书参考与搜索历史 |
| 相似案件解释 | `/case-explanation` | `case.py`，`/api/case/search` | 案例检索和解释参考 |
| 纠纷整理 | `/dispute-organize` | `dispute.py`，`/api/dispute/...` | 从叙述整理信息；与工作台的正式事实不是同一数据对象 |
| 纠纷中心 | `/dispute-center` | `dispute.py`，`/api/evidence`、`/protection`、`/prediction`、`/reminder`、`/warning` 等 | 取证、维权路径、文书、预测、提醒、风险等旧业务子功能 |
| 通用文件起草 | `/document-drafting` 及其文书/合同/法律意见子页 | `document_drafting.py`，`/api/document/draft`、`/list` | 通用起草与历史；区别于案件工作台经审批的仲裁草稿 |
| 模拟法庭 | `/debate`、`VoiceCourtroom` | `analysis.py` 及 `app.py` 的 `/api/courtroom/ws/<session_id>` | 多角色庭审模拟；页面还有 EventSource 流式过程与后端 WebSocket 能力 |
| 知识图谱 | `/knowledge-graphs`、`/knowledge-graph` | `knowledge_graph.py`，`/api/knowledge-graphs`、`/knowledge-graph/...` | 图谱、节点和关系的浏览/维护；不代表法源审核 |
| 辅助工具 | `/legal-calculator` 和各费用、期限页面 | `legal_tools.py`，`/api/legal-tools/...` | 利息、劳动补偿、诉讼费、工伤、律师费、日历、期限、各类费用等参考测算 |
| 其他 | `/history`、`/favorites`、`/agents`、`/settings` | `favorites.py`、`agent.py` 和各业务历史接口 | 历史/收藏/智能体配置分属不同对象；没有全站统一的一张“历史表” |

`legal.py` 还保留 `/api/legal/chat` 旧普法问答接口；当前 `/chat` 页面主线使用数字人 Conversation。不要仅因两个接口都叫“聊天”就认为它们共用同一个会话表或处理链。

### 5.1 旧业务模块怎样调用

典型模式是：**页面状态或 Store → `fetch`/请求封装 → Flask Router → Service 或 Router 内业务处理 → SQLAlchemy 模型 → JSON/SSE 返回页面**。例如合同审查的上传和风险审查走 `document.py`；纠纷中心各步骤走 `dispute.py`；图谱走 `knowledge_graph.py`。这些 Router 中有一些文件很大，部分业务逻辑仍留在 Router 内，不能假定项目所有业务都已严格做到薄 Router + Service 分层。

### 5.2 各独立模块的实际处理流程

**合同审查。** `/contract` 使用 `contractStore.ts` 管理前端会话视图。上传请求进入 `document.py`，后端校验扩展名、保存文件、提取 PDF/Word/TXT 文本，并写入 `contracts`；审查请求读取合同正文或传入文本，调用模型分析风险并保存 `contract_risks`。流式入口先创建审查会话并在后台处理，前端再读取事件。这里的合同会话不是数字人 Session，审查结果也不是劳动 Agent 的 Artifact。实际上传端点当前只允许 `.pdf/.doc/.docx/.txt`；页面文案若称支持图片，应以具体请求和后端校验为准。

**案情推断、相似文书、案件解释。** `/case-analysis` 请求 `analysis.py` 的 `case-analysis` 接口，提交案情描述，由后端调用模型并保存 `case_analyses`。`/similar-documents` 的查询也进入 `analysis.py`，保存相似文书搜索记录；`/case-explanation` 调用 `case.py` 的案例搜索。它们产出分析或参考材料，不会自动替用户创建 Matter、确认事实或加入劳动 Agent Plan。模型回答中出现的法律条款需另行核实，不能直接视作 Agent 法源表中的已验证引用。

**纠纷整理与纠纷中心。** `/dispute-organize` 负责把叙述或上传内容整理成结构化争议信息；`dispute.py` 的 `/dispute/organize` 能处理文本及部分文件输入，记录到 `dispute_infos`。`/dispute-center` 将整理、证据收集、维权路径、纠纷文书、预测、提醒和风险警示作为分项调用，各自有历史记录。它与案件工作台的 Matter、正式事实、Run、审批是两套业务对象。注意：当前 `/dispute-organize` 页面出现 `/api/dispute/organize-with-files` 请求，而 Router 静态路由列表中未见同名端点；接手者在声称“文件整理已联通”前应运行该页面并核对实际响应。

**通用文书起草。** 文书、合同和法律意见子页把输入、类型及详情发给 `document_drafting.py` 的 `/api/document/draft`。Router 调用 `LegalAgentService.draft_document` 生成内容，随后写 `document_drafts`，再按类型写详情表；列表、详情、更新、删除和置顶也由该 Router 提供。这里的 `LegalAgentService` 是旧业务服务名称，**不是** `legal_agent_system` 的 `LegalAgentFacade`；不能因名字相近就推断它经过 Runtime、法源门禁或审批。

**模拟法庭。** `/debate` 使用 `analysis.py` 的庭审启动、过程、用户输入、状态与历史接口；页面存在 EventSource 过程流。`app.py` 还注册 `/api/courtroom/ws/<session_id>`，由 `courtroom_websocket_service.py` 支撑双向语音/庭审交互。两种实时通信是不同路径。结果用于模拟训练，不是法院系统中的真实诉讼记录。

**法律图谱。** `/knowledge-graphs` 使用 `knowledge_graph.py` 管理图谱列表和创建/编辑/删除；同一 Router 提供节点、关系、结构、搜索、文件上传与构建接口。`knowledge_graph.py` 的 `KnowledgeGraph/KnowledgeNode/KnowledgeRelationship` 模型保存可视化结构。图谱节点关联不等同于具体劳动案件中的已验证官方法源。

**法律工具、历史与智能体管理。** 各计算器页面调用 `legal_tools.py` 对应端点，典型做法是按输入参数计算并提供各自的历史查询/删除；劳动补偿工具复用 `labor_compensation_service.py`。`/history` 聚合部分业务历史，数据仍在各领域自己的表中。`/agents` 调用 `agent.py` 中智能体配置、聊天和使用量接口；这与劳动 Agent Runtime 同样不能混为一谈。`/favorites` 使用独立收藏 Router。

## 6. 法小助咨询的真实请求链

```text
DailyConversationPage / DigitalHumanChat / ConversationComposer
→ digitalHumanStore.sendMessage(question)
→ digitalHumanApi.sendDigitalHumanMessageStream(..., request_id)
→ POST /api/digital-human/chat/stream
→ DigitalHumanService.chat_stream / ConversationOrchestrator
→ 请求幂等领取、会话与 Workspace 上下文、记忆、Router 判断
→ ConversationActions（仅对授权意图执行建案/分流/启动等动作）
→ 生成回复并保存消息/请求状态
→ SSE accepted/thinking/delta/completed（语音开启时另有 voice 事件）
→ Zustand 增量消息、最终消息、Workspace、Rive/语音状态更新
```

前端在 [digitalHumanStore.ts](../frontend/src/store/digitalHumanStore.ts) 生成 `dhr_...` 请求 ID，追加用户消息并请求 SSE；`digitalHumanApi.ts` 负责协议解析。后端 [digital_human.py](../flask_app/routers/digital_human.py) 校验请求和匿名客户端身份；[orchestrator.py](../flask_app/services/conversation/orchestrator.py) 处理幂等请求、上下文、记忆、分流与持久化；[router.py](../flask_app/services/conversation/router.py) 先应用确定性规则，再用受约束的模型结果补充判断。普通问题回复即可；劳动咨询也不会因关键词自动建案。只有明确办案意图满足服务端授权条件时，[actions.py](../flask_app/services/conversation/actions.py) 才通过现有 Facade 创建 Matter、做分流或启动任务。高风险、事实冲突、审批等待等状态会停止自动推进或引导用户进入工作台。

会话历史、记忆和当前 Workspace 由服务端保存。前端 Store 保存当前视图与临时状态，不能把本地缓存当作正式案件事实。匿名客户端身份可通过 HttpOnly Cookie 继续，旧请求头兼容；这属于匿名身份连续性，不是完整账号权限体系。停止回复有前端请求取消和服务端取消接口；重复 `request_id` 由请求记录控制恢复及副作用。

### 6.1 数字人视觉和语音

`DigitalHumanAvatar.tsx` → `RiveDigitalHuman.tsx` → 本地 `.riv` 资源构成视觉链；状态来自对话、加载、朗读等业务信号。浏览器语音输入与语音朗读是独立交互能力。回复朗读可从后端 voice 事件进入 `StreamingAudioPlayer`；浏览器能力或服务不可用时有回退/提示。Rive 动画不负责法律判断、审批或案件数据写入。

## 7. 案件工作台的用户流程与前端组织

工作台入口在 [TopNavbar.tsx](../frontend/src/components/TopNavbar.tsx)：选择“案件工作台”调用 `openWorkspace()`；对话内也可按上下文“转入办理”。外壳 [CaseWorkspaceShell.tsx](../frontend/src/components/DigitalHuman/CaseWorkspaceShell.tsx) 使用 `useMatterWorkspace()` **挂载一次**，保存跨阶段动作与状态；[CaseStageContent.tsx](../frontend/src/components/DigitalHuman/CaseStageContent.tsx) 只渲染当前阶段。左侧为会话/案件导航，中间四阶段，右侧为可收起的数字人助手。聊天与工作台共享会话、Matter 和 Run 上下文，但 UI 入口与展示职责不同。

| 阶段 | 用户主要动作 | 系统主要动作 | 关键边界 |
| --- | --- | --- | --- |
| 1. 目标与法域 | 新建/恢复 Matter，填写目标并确认法域 | 保存 Matter 和明确法域 | 法域不能由模型猜测代替用户确认 |
| 2. 材料整理 | 粘贴文字或上传支持的 Word/PDF、图片、音视频 | 组织可编辑文本、材料、时间线和候选事实 | 识别稿和候选事实不是正式事实 |
| 3. 事实与证据 | 审阅、采用或修改候选；填写各争议类型必填项 | 关联证据支持/冲突/缺口；检查缺失；启动或续跑 | 缺关键字段时不得伪装成完整分析 |
| 4. 分析与文书 | 查看规则、风险、法源、金额；补信息、重试或审批；导出草稿 | 展示 Run 步骤和验证结果；审批后生成/复用 Artifact | 法源不足应阻断；草稿待人工复核，不代表正式提交 |

与旧纠纷整理不同，工作台是持续的 Matter；切换案件或刷新会按服务端 Workspace 版本与当前指针恢复。普通会话文字、材料候选、用户确认事实、Agent 运行结果是不同可信层级。

## 8. 劳动 Agent 的后端执行链

```text
HTTP Router：digital_human_agent.py
→ LegalAgentFacade.start_task / continue_task
→ CapabilityRuntime.start_task / continue_task
→ CapabilityRegistry.resolve(task_type) + Domain Adapter
→ AgentRepository 创建/恢复 Run，绑定领域与模板
→ CapabilityRuntimeGraph：上下文 → 建 Plan → 选 Step → 执行 → 观察 → 验证 → 决策
→ PolicyToolExecutor 经 ToolRegistry 白名单执行 Tool
→ labor_disputes / matters / jurisdictions 中的确定性业务服务与规则
→ AgentRepository 保存 Run、Plan revision、Step、ToolCall、审批、审计、Artifact
→ 返回可恢复的运行快照，前端阶段四展示
```

后端入口 [digital_human_agent.py](../flask_app/routers/digital_human_agent.py) 处理 HTTP、匿名归属和错误映射；[facade.py](../flask_app/legal_agent_system/facade.py) 组装与提供稳定业务入口；[capability_runtime.py](../flask_app/legal_agent_system/runtime/capability_runtime.py) 负责用例、能力解析和 Run 恢复；[capability_graph.py](../flask_app/legal_agent_system/runtime/capability_graph.py) 是通用 LangGraph 执行图。劳动领域的模板、参数和验证放在 `domains/labor/`；具体劳动事实、证据和规则放在 `labor_disputes/`。`tools/` 是 Runtime 可调用动作的白名单，`runtime/executor.py` 负责执行前的策略检查，`runtime/verifier.py` 与领域验证器处理结果验证。

### 8.1 为什么一套 Graph 能处理复合争议

Graph 表达通用执行状态，不按“欠薪”“解除”“加班”分别复制。能力注册表选择 `cn_labor` 领域和已声明模板；争议标签只启用模板允许的步骤，公共的证据、期限、法源与审批步骤去重。一案通常是一条 Run 和一份当前 Plan；事实变化导致重规划时保存新的 Plan revision，不覆盖历史。模型不能自由添加 Tool、跳过审批或把缺失法源当作有效来源。当前代码还包含模拟能力包，用于兼容旧阶段演示；它不代表第二个完整的真实法律领域。

### 8.2 运行会在哪里暂停或失败

| 状态/情况 | 含义 | 用户或系统后续动作 |
| --- | --- | --- |
| `awaiting_jurisdiction` | 法域尚未确认 | 用户明确确认后继续 |
| `awaiting_information` | 关键事实不足 | 用户补充或修正事实，再规划/续跑 |
| `blocked_authority` | 相关法律来源不可用或验证不足 | 法源同步/复核后走受控重试；不能直接出有依据的草稿 |
| `awaiting_approval` | 高风险草稿步骤等待人工决定 | 用户批准或拒绝；拒绝不执行该步骤 |
| `completed` / `cancelled` / `human_handoff` | 完成、取消或转人工 | 按状态展示结果和下一步，不统一包装为“成功” |

`continue_task` 只接受状态允许的显式动作，例如补事实、确认法域、审批或重试法源；Run 锁、动作幂等和持久化检查点用于防重复执行及恢复。详细图与函数顺序可见 [Agent README](../flask_app/legal_agent_system/README.md) 和 [实际 Agent 架构](../flask_app/legal_agent_system/实际Agent架构与运行流程.md)。

## 9. 关键数据对象与“谁是真相”

| 对象 | 主要表 | 作用和可信度 |
| --- | --- | --- |
| Session / Message | `digital_human_sessions`、`digital_human_messages` | 用户原话和助手回复；帮助续接，不自动变成案件确认事实 |
| Request / Memory | `digital_human_requests`、`conversation_memories` | 请求幂等、恢复点、结构化记忆与摘要；记忆仍需处理冲突 |
| Workspace State | `conversation_workspace_states` | 每会话当前 Matter 指针与版本，供页面恢复和并发切换 |
| Matter / Jurisdiction | `matters`、`matter_jurisdictions` | 案件归属与已确认法域 |
| Material / Candidate | `agent_documents`、`document_fragments`、`legal_facts` | 授权材料、片段及带出处的候选事实；候选须用户确认 |
| Confirmed Facts / Triage | `matter_fact_assertions`、`labor_case_triages`、`labor_dispute_profiles` | 版本化确认事实、劳动初筛与劳动案件档案 |
| Execution | `agent_runs`、`agent_plans`、`agent_steps`、`tool_calls` | 任务状态、不可覆盖计划、步骤和工具调用记录 |
| Approval / Audit | `approval_requests`、`agent_run_actions`、`agent_audit_events`、`agent_event_outbox` | 人工决策、继续动作幂等、审计与事件 |
| Authority / Artifact | `legal_authorities` 及同步/快照/复核表、`agent_artifacts` | 法源版本和治理记录；草稿等交付物及引用 |

旧平台还各有合同、案例、庭审、纠纷、文书、图谱、计算器和收藏等表。不要把所有页面的历史记录归到 `digital_human_sessions`。ORM 定义位于 [db_models.py](../flask_app/models/db_models.py)、[knowledge_graph.py](../flask_app/models/knowledge_graph.py) 和 [Agent models.py](../flask_app/legal_agent_system/models.py)。更细的数据域地图见 [DATABASE_MAP.md](../flask_app/legal_agent_system/DATABASE_MAP.md)；其中的**实库表数量是该文档成文时的快照**，本次未连接数据库重新统计。

## 10. 三个具体端到端例子

### 10.1 普通法律问题

用户在 `/chat` 输入问题 → Store 提交流式请求 → Conversation 读取当前会话和记忆 → Router 判断为普通聊天或劳动咨询 → 生成可读回复 → 消息与请求状态保存 → 页面逐步显示。若回答给出其他功能入口，用户点击后才打开对应页面；这一步不自动把聊天文字同步到合同审查、文书起草或旧纠纷中心。

### 10.2 合同审查

用户进入 `/contract` → 前端上传合同 → `document.py` 接收和解析 → 请求审查（可使用流式接口）→ 审查结果形成风险项并保存合同与风险记录 → 页面展示、可查看历史。该链路没有 `Matter → CapabilityRuntimeGraph`；审查建议须结合完整合同和签署背景核对。

### 10.3 复合劳动争议

用户说明欠薪、加班与解除相关事实 → 明确办案意图后服务端可创建/关联 Matter 并进行劳动分流 → 工作台确认法域、材料与正式事实 → 后端在已注册劳动模板中生成包含对应争议步骤的 Plan → Tool 读取确认事实、证据与法源并执行规则/计算 → Verifier 对来源和结果把关 → 缺事实或法源时暂停/阻断 → 需要生成仲裁草稿时等待人工审批 → 通过后保存 Artifact，用户在工作台查看并导出**待复核草稿**。审批不等于法院或仲裁机构受理。

## 11. 已实现、规划与无法直接确认的边界

- **源码可确认已接入**：全站上述主要页面和 Router；数字人会话与工作台；劳动领域能力包、通用 Agent Runtime、材料候选、规则分析、法源校验、审批、草稿；PostgreSQL ORM 与 Alembic；SSE/语音相关代码和部署配置。
- **设计规划，不能当作当前实现**：多真实法律领域统一自动办案、完整账号与跨设备权限、长期生产保障等在 `raw/` 和项目记录中有规划，不能据此宣称已经落地。
- **本次未现场验证**：当前部署是否启动、目标环境数据库迁移版本、模型/语音/官方法源连通性、每个页面的浏览器交互、真实法律专业复核。需要这些结论时分别运行环境检查和人工验收。
- **法源尤其注意**：开发测试库的审核状态不能推出正式环境同样有效；具体劳动结论要以运行时实际验证的来源、版本及案件事实为准。
- **代码组织现状**：新 Agent 子系统分层较清楚；部分旧业务 Router 文件很大且混有业务处理。评估重构时应先看真实调用与测试，不能假定所有模块已有统一 Service/Repository 层。

## 12. 接手项目时的最短阅读顺序

1. **先理解全站**：[首页](../frontend/src/app/page.tsx) → [顶栏](../frontend/src/components/TopNavbar.tsx) → [Flask 入口](../flask_app/app.py) → `routers/` 目录。
2. **若任务涉及法小助**：[聊天页面](../frontend/src/components/DigitalHuman/DailyConversationPage.tsx) → [Store](../frontend/src/store/digitalHumanStore.ts) → [API 封装](../frontend/src/services/digitalHumanApi.ts) → [Conversation Router](../flask_app/services/conversation/router.py) → [Orchestrator](../flask_app/services/conversation/orchestrator.py)。
3. **若任务涉及劳动案件**：[工作台逻辑](../frontend/src/components/DigitalHuman/useMatterWorkspace.ts) → [阶段分发](../frontend/src/components/DigitalHuman/CaseStageContent.tsx) → [Agent HTTP](../flask_app/routers/digital_human_agent.py) → [Facade](../flask_app/legal_agent_system/facade.py) → [Runtime](../flask_app/legal_agent_system/runtime/capability_runtime.py) → `domains/labor/` 和 `labor_disputes/`。
4. **若任务涉及旧功能**：从对应 `frontend/src/app/<route>/page.tsx` 搜索实际请求地址，再读对应 `flask_app/routers/` 和被调用的 Service；不要先套劳动 Agent 架构。
5. **若任务涉及数据/部署**：[数据库地图](../flask_app/legal_agent_system/DATABASE_MAP.md)、[迁移目录](../flask_app/migrations/versions/)、[Compose](../docker-compose.yml)、[Nginx](../deploy/nginx.conf)。

## 13. 交给 GPT 时可直接附上的任务约束

> 你接手的是 `D:\项目\law` 律知项目。先阅读本文件，再核对当前源码、`AGENTS.md`、`AI_WORKFLOW/WORKFLOW.md` 和 `AI_WORKFLOW/CURRENT_TASK.md`。把用户最新要求放在旧任务记录之前；区分已实现、文档规划和本次现场验证。修改前确认目标模块、调用链、数据来源和 Git 未提交改动；只改本次任务范围。法律事实候选须用户确认，正式 Agent 动作不得绕过法域、法源、ToolRegistry、Verifier 与审批。不要读取或输出 `.env`、密钥或真实用户数据。完成后说明真实修改、测试证据和未验证部分。

## 14. 本文件的证据入口

- 全站与部署：[前端依赖](../frontend/package.json)、[Flask 装配](../flask_app/app.py)、[Compose](../docker-compose.yml)、[Nginx](../deploy/nginx.conf)。
- 功能入口：[页面目录](../frontend/src/app/)、[Router 目录](../flask_app/routers/)、[业务服务目录](../flask_app/services/)。
- 重点主线：[数字人 Store](../frontend/src/store/digitalHumanStore.ts)、[Conversation](../flask_app/services/conversation/)、[Agent README](../flask_app/legal_agent_system/README.md)、[工作台](../frontend/src/components/DigitalHuman/CaseWorkspaceShell.tsx)。
- 已有补充材料：[面向体验者的项目说明](./律知项目完整说明.md)、[体验案例](./项目讲解与案例演示.md)、[Agent 完整流程导读](../flask_app/legal_agent_system/数字人Agent目录与完整流程导读.md)。这些文档是辅助入口；与当前源码冲突时，以源码为准。
