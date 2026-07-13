# 多法域数字人法律 Agent 总体规划

更新时间：2026-07-13
规划对象：YYS-Law 全局数字人“法小助”  
规划性质：长期目标架构与分阶段实施基线
当前决策：采用方案 B“可信基础优先、平衡演进”，阶段 0～3.4 的工程实现已完成，官方法源自动同步闭环已通过端到端验证；生产级验收仍需真实脱敏材料、并发和长期运行验证。

## 1. 最终目标

法小助最终建设为一个以 2D 数字形象呈现、支持文字/语音/文件交互、具备持续任务执行能力的多法域法律服务 Agent。

它不只是回答问题或跳转页面，而应能够：

1. 理解用户真正要解决的法律目标。
2. 识别国家、地区、适用法律、语言和风险级别。
3. 主动追问缺失事实，读取用户授权的材料并提取证据。
4. 生成可调整的任务计划，调用受控工具完成法律任务。
5. 对工具结果执行结构、事实、来源和风险校验。
6. 在敏感数据、高风险结论或外部动作前暂停并请求用户确认。
7. 形成带依据、假设、不确定性和执行记录的交付物。
8. 支持任务暂停、恢复、重试、修改、导出、归档和人工接管。
9. 通过法域包扩展不同国家和地区，不把中国法律写死在 Agent 核心层。

最终产品由两个同等重要的部分组成：

- **数字人交互能力**：2D 形象、语音、字幕、口型、表情、打断、状态反馈和无障碍体验。
- **法律 Agent 能力**：目标理解、案件状态、动态规划、工具调用、验证、审批、恢复和审计。

## 2. 当前基线与主要差距

当前法小助已经从“LLM 问答 + 意图分类”推进到首个可恢复的法律任务闭环。现有实现包括：数字人会话、Matter 工作区、显式中国法域确认、材料分片与事实定位、劳动事实建议、LangGraph Runtime、工具白名单、ToolCall 审计、审批暂停恢复、结构/事实/来源/风险四类验证、步骤与工具预算，以及中国劳动纠纷草稿闭环。

当前闭环仍属于工程验证版本，尚未达到生产级法律服务标准。最主要的阻断项是：法律来源缺少可信写入边界和官方来源适配器；劳动规则仍是简化规则；计划固定为三步；数据库没有迁移基线；评测样本不足。

| 能力 | 当前状态 | 目标状态 |
|---|---|---|
| 数字形象 | 8 张状态图与 CSS 动效 | 2D 骨骼/序列动画、口型、语音状态同步 |
| 对话 | 文本请求-响应，闲聊 LLM 与任务工作台仍分离 | 实时文字/语音、可打断、流式事件 |
| 任务理解 | 已有劳动任务入口和缺失事实追问 | 通用目标、任务类型、法域、风险和完整度识别 |
| 记忆 | 会话、Matter、Run、Step 和审批可恢复 | 用户偏好、事实版本、计划版本和运行状态分层存储 |
| 行动 | 可调用材料、证据清单、劳动分析和草稿工具 | 调用检索、计算、合同、纠纷、文书和平台工具 |
| 计划 | 固定三步劳动计划 | 版本化动态 Plan-and-Execute，支持重新规划 |
| 执行 | LangGraph + 白名单工具，但声明策略未统一执行 | Policy ToolExecutor + 受限 ReAct 单步执行 |
| 验证 | 已有结构、事实、来源、风险四类确定性验证 | 领域规则扩展、证据引用闭环和评测门禁 |
| 安全 | 已有审批、过期、步骤/工具预算和审计 | 可信来源、幂等、并发、时长/费用预算和人工接管 |
| 法域 | 数据结构显式，当前业务只支持中国劳动纠纷 | 多国家、多地区、多语言、跨境冲突识别 |

## 3. 核心架构原则

### 3.1 C 是最终目标，Agent 化是必经阶段

最终目标是“可互动数字人 + 可执行法律 Agent”。实施时先建立可验证的 Agent 闭环，再接入实时语音和更完整的 2D 表现，避免同时放大业务与音视频风险。

### 3.2 2D 是正式路线，不以 3D 为前提

数字人的真实感主要来自低延迟、能听会说、允许打断、状态同步和持续记忆。2D 可逐步从状态图升级为 Live2D/Spine/序列动画和音素口型，不要求改成 3D。

### 3.3 状态图控制流程，模型不能控制安全边界

- LangGraph 状态图作为 Agent Runtime 骨架。
- 动态 Plan-and-Execute 管理任务步骤。
- 受限 ReAct 仅在当前步骤内选择工具。
- 代码规则控制工具权限、调用次数、确认、退出和错误恢复。

### 3.4 单总控 Agent 优先

第一阶段使用一个法小助总控 Agent 和一组结构化工具。只有当专业领域具有独立上下文、评测和权限边界时，才拆分合同、纠纷、检索、文书等专业 Agent。

### 3.5 多法域从数据结构开始

中国法律作为第一个落地法域，但核心状态、工具、检索和引用均显式接收 `jurisdiction_context`，禁止依赖全局默认法域完成高风险法律判断。

### 3.6 证据优先于自然语言结论

法律事实必须尽可能关联材料页码、文本位置或用户确认；法律结论必须关联法律来源、有效状态、适用日期和法域。

### 3.7 可信基础先于自主性扩张

- 先建立评测、数据库迁移、可信法律来源和完整规则，再提高 Planner/LLM 自主性。
- 小型权威语料优先使用结构化过滤与全文检索，不为技术展示提前引入向量数据库。
- 第二业务领域用于验证通用架构，但必须在当前领域的来源、规则和评测稳定后接入。
- 事件模型先于 SSE/WS 传输实现；慢工具真实出现后再引入异步任务队列。

## 4. 总体分层架构

当前实现与目标架构均已生成可维护图件：

- [当前 Agent 架构图](./当前Agent架构图.svg)（[Mermaid 源](./当前Agent架构图.mmd)、[可编辑 Excalidraw](./当前Agent架构图.excalidraw)）
- [目标 Agent 架构图](./目标Agent架构图.svg)（[Mermaid 源](./目标Agent架构图.mmd)、[可编辑 Excalidraw](./目标Agent架构图.excalidraw)）

```text
2D 数字人表现层
语音、字幕、口型、表情、打断、无障碍
        ↓
交互与事件层
WebSocket/SSE、流式事件、轮次、取消、重连
        ↓
法小助总控 Agent
目标理解、追问、解释、计划、用户沟通
        ↓
Agent Runtime
状态图、执行、验证、审批、重试、恢复、预算
        ↓
统一工具层
材料、检索、合同、纠纷、计算、文书、平台操作
        ↓
法域与法律知识层
法域包、法律来源、有效性、版本、冲突规则、语言
        ↓
案件数据与审计层
事实、证据、计划、步骤、工具调用、审批、交付物
```

推荐将新体系统一收敛到 `flask_app/legal_agent_system/` 总包中，避免 Agent 相关模块继续平铺在 `flask_app` 根目录。该总包是法律 Agent 的内部领域边界，现有 Flask Router 通过公开门面调用它，不直接引用内部节点或具体工具。

推荐后端目录边界：

```text
flask_app/
└── legal_agent_system/
    ├── __init__.py                 # 仅导出稳定公共接口
    ├── facade.py                   # Router/现有业务调用的统一门面
    ├── runtime/
    │   ├── graph.py
    │   ├── state.py
    │   ├── planner.py
    │   ├── executor.py
    │   ├── verifier.py
    │   ├── policies.py
    │   └── checkpoints.py
    ├── tools/
    │   ├── base.py
    │   ├── registry.py
    │   ├── documents/
    │   ├── legal_research/
    │   ├── calculators/
    │   ├── disputes/
    │   ├── contracts/
    │   └── drafting/
    ├── jurisdictions/
    │   ├── base.py
    │   ├── registry.py
    │   ├── cn/
    │   └── future/
    ├── matters/
    │   ├── service.py
    │   ├── repository.py
    │   └── schemas.py
    └── digital_human/
        ├── conversation_service.py
        ├── event_service.py
        └── presentation_mapper.py
```

边界约束：

- `routers/` 只能调用 `legal_agent_system.facade` 暴露的公共用例，不直接调用 `runtime/`、具体工具或法域实现。
- `runtime/` 依赖抽象工具协议和案件状态，不依赖 Flask、Router 或前端结构。
- `tools/` 可以适配现有 Service，但工具之间不得互相直接调用；组合关系由 Runtime 管理。
- `jurisdictions/` 只提供法域规则、能力声明和来源适配，不持有会话状态。
- `matters/` 是案件事实和工作区的权威访问层，不包含 LLM 规划逻辑。
- `digital_human/` 负责会话和表现事件映射，不参与法律判断和工具权限决策。
- 跨子包共享的数据契约集中定义，禁止通过循环导入共享实现细节。
- 现有 `services/digital_human_service.py` 在迁移期作为兼容入口，逐步委托给总包门面，不进行一次性重写。
- 阶段 1 只创建实际使用的最小目录和文件，不预先生成无实现的空模块。

## 5. 多法域核心模型

### 5.1 法域上下文

```python
class JurisdictionContext:
    country_code: str               # ISO 3166-1，例如 CN、US、GB
    subdivision_code: str | None    # 省/州/地区，例如 CN-BJ、US-CA
    legal_system: str               # civil_law/common_law/mixed/other
    governing_law: str | None       # 合同选择的准据法
    forum: str | None               # 法院、仲裁机构或行政机关
    language: str                   # BCP 47，例如 zh-CN、en-US
    effective_at: date              # 查询适用法律的时间点
    confidence: float
    confirmed_by_user: bool
```

法域识别顺序：

1. 用户明确声明。
2. 合同准据法、争议解决条款或材料内容。
3. 事件发生地、主体所在地、法院/仲裁机构。
4. 用户账户偏好，只能作为低置信度候选。
5. 无法确定时必须追问，不允许静默使用中国法。

### 5.2 跨境案件

单个案件允许存在多个候选法域：

```python
class JurisdictionCandidate:
    context: JurisdictionContext
    basis: list[str]
    confidence: float
    status: str  # candidate/confirmed/rejected/conflict
```

如果出现合同准据法、履行地、主体所在地和法院地不一致，Agent 进入 `jurisdiction_conflict` 状态，调用冲突法分析工具或转人工，不直接输出确定结论。

### 5.3 法律来源

```python
class LegalAuthority:
    authority_id: str
    jurisdiction: JurisdictionContext
    authority_type: str       # statute/regulation/case/treaty/guidance
    title: str
    provision: str | None
    text: str
    source_url: str
    issuing_body: str
    published_at: date | None
    effective_from: date | None
    effective_to: date | None
    status: str               # effective/repealed/amended/unknown
    retrieved_at: datetime
    content_hash: str
    provider: str                 # 来源提供者标识
    external_id: str             # 提供者侧稳定 ID
    canonical_url: str           # 权威规范地址
    trust_level: str             # trusted/reviewed/untrusted/test
    version: str
    supersedes_id: str | None
    last_verified_at: datetime
    retrieval_status: str
```

任何法律引用必须可追溯到 `authority_id`。来源状态为 `unknown` 时不得包装成确定法律依据。

## 6. Agent 核心状态

```python
class AgentState:
    run_id: str
    session_id: str
    matter_id: str
    user_id: str

    user_goal: str
    task_type: str
    risk_level: str
    jurisdiction: JurisdictionContext | None

    facts: list[LegalFactRef]
    missing_facts: list[MissingFact]
    document_ids: list[str]

    plan_id: str | None
    plan_version: int
    current_step_id: str | None

    tool_result_ids: list[str]
    pending_approval_id: str | None
    status: str
    final_artifact_ids: list[str]
    error_code: str | None
```

状态中只保存必要字段和引用 ID；材料全文、完整对话、工具原始结果、法律文本和审计日志分别持久化，避免状态无限膨胀。

建议状态枚举：

```text
understanding
awaiting_jurisdiction
awaiting_information
planning
executing
verifying
awaiting_approval
replanning
completed
failed
cancelled
human_handoff
```

## 7. Agent 主流程

```text
用户文字 / 语音 / 文件输入
        ↓
恢复或创建案件工作区
        ↓
识别目标、任务类型、风险和候选法域
        ├─ 普通闲聊 → 直接回答
        ├─ 法律问答 → 检索 → 生成 → 验证 → 回答
        ├─ 紧急高风险 → 提示 → 人工接管
        └─ 法律任务
                ↓
        提取事实与材料信息
                ↓
        法域或信息是否完整
          ├─ 否 → 暂停并追问用户
          └─ 是
                ↓
        生成或更新执行计划
                ↓
        执行当前步骤
                ↓
        受限 ReAct 选择工具
                ↓
        结构、事实、来源、风险验证
          ├─ 失败 → 重试 / 换工具 / 重新规划
          ├─ 需确认 → 暂停并请求确认
          └─ 通过 → 下一步骤
                ↓
        生成最终交付物
                ↓
        用户审阅、修改、导出或转人工
                ↓
        保存案件状态与审计记录
```

硬限制：

- 单次运行最大步骤数、工具调用数、模型费用和总时长可配置。
- 同一工具和等价参数连续失败两次后禁止盲目重试。
- 高风险动作执行前必须有未过期的用户审批。
- 任务可在任意等待用户的节点持久化并恢复。
- 不向用户展示模型内部思维链，只展示任务目标、当前步骤、依据、假设和等待事项。

## 8. 工具协议

### 8.1 工具定义

```python
class ToolDefinition:
    name: str
    version: str
    description: str
    input_schema: type
    output_schema: type
    supported_jurisdictions: list[str]
    risk_level: str
    requires_confirmation: bool
    timeout_seconds: int
```

### 8.2 统一结果

```python
class ToolResult:
    tool_call_id: str
    success: bool
    data: dict | None
    evidence_refs: list[str]
    authority_refs: list[str]
    assumptions: list[str]
    warnings: list[str]
    error_code: str | None
    retryable: bool
```

工具不得只返回不可解析的大段文本。LLM 型工具也必须经过输出 Schema 校验。

### 8.3 首批工具

| 工具 | 职责 | 实现优先级 |
|---|---|---:|
| `parse_document` | 解析 PDF/DOCX/TXT/图片并记录位置 | P0 |
| `extract_legal_facts` | 提取带材料出处的事实 | P0 |
| `build_case_timeline` | 建立事件时间线并发现冲突 | P0 |
| `calculate_legal_deadline` | 按法域和日期规则计算期限 | P0 |
| `search_legal_authorities` | 按法域、时间和主题检索法律来源 | P0 |
| `verify_legal_citation` | 核对引用真实性、有效性和适用性 | P0 |
| `generate_evidence_checklist` | 生成已有/缺失证据清单 | P0 |
| `draft_legal_document` | 基于已确认事实生成草稿 | P1 |
| `review_contract` | 调用合同审查能力并返回结构化风险 | P1 |
| `organize_dispute` | 调用纠纷整理能力 | P1 |
| `export_artifact` | 导出文书或报告 | P1 |
| `handoff_to_human` | 生成结构化人工接管摘要 | P1 |

## 9. 风险和审批模型

| 级别 | 场景 | 策略 |
|---|---|---|
| L0 | 查询、读取已授权材料 | 可自动执行 |
| L1 | 分析、提取、计算、检索 | 自动执行，展示依据和假设 |
| L2 | 生成合同修改稿、申请书草稿 | 可生成，必须标记草稿 |
| L3 | 覆盖文件、发送材料、创建正式委托 | 执行前明确确认 |
| L4 | 代替用户接受协议、放弃权利或作最终法律决定 | 禁止自动执行 |

额外高风险触发条件：

- 人身安全、刑事风险、即将到期的法定期限。
- 未成年人、老人或认知能力可能受限的用户。
- 身份证件、健康、财务、家庭等敏感信息。
- 法域不明确或多个法域冲突。
- 法律来源无法验证或已经失效。
- 模型结论与确定性工具结果冲突。

## 10. 数字人交互设计

### 10.1 2D 状态

建议从现有表情扩展为运行状态映射：

```text
idle
listening
thinking
speaking
reading_document
running_tool
waiting_information
waiting_approval
warning
success
error
human_handoff
```

表现层只消费 Agent 事件，不参与法律判断。

### 10.2 实时事件

```json
{
  "event": "agent.step.updated",
  "run_id": "run_xxx",
  "status": "running_tool",
  "user_message": "正在核对劳动合同中的工资和解除条款",
  "progress": {"completed": 3, "total": 6}
}
```

前端展示目标、已完成步骤、当前动作、待补充信息、待确认动作和交付物；不展示原始推理过程。

### 10.3 语音路线

1. 流式 STT、字幕和语音活动检测。
2. 流式 TTS、播放状态和取消。
3. 用户插话时立即停止播报和口型。
4. 音素或音量驱动 2D 口型。
5. 弱网或权限失败时自动降级到文字。
6. 支持语言、语速和字幕偏好；法域与界面语言分别管理。

## 11. 第一个垂直闭环

首个闭环选择“中国劳动纠纷初步处理”，但所有协议必须使用通用法域字段。

用户旅程：

```text
描述欠薪/解除问题
→ 法小助识别目标与中国法域候选
→ 用户确认地区和关键日期
→ 上传劳动合同、解除通知等材料
→ 解析材料并提取带出处事实
→ 建立时间线并核对冲突
→ 计算关键期限
→ 检索并验证法律依据
→ 生成证据缺口和行动建议
→ 用户确认后生成仲裁申请书草稿
→ 用户修改、导出或转人工
```

首个闭环暂不包含自动提交仲裁、对外发送材料或替用户作最终法律选择。

## 12. 分阶段实施计划

状态说明：`已完成` 表示当前源码已具备该阶段的主要闭环；`执行中` 表示已确认并开始实施；所有阶段仍需持续回归和加固。

### 阶段 0：稳定现有数字人基线（已完成）

目标：保证当前会话、身份和接口可以承载后续 Agent。

- 完成数字人会话归属隔离和历史恢复。
- 统一前后端权威状态与错误码。
- 增加请求取消、超时、幂等和结构化输出校验。
- 建立现有意图识别与路由回归测试。

验收：刷新和服务重启后可恢复本人会话；不同用户不可读取对方会话；重复请求不会生成重复轮次。

### 阶段 1：Agent 基础协议与 Runtime（已完成）

目标：不接具体复杂业务，先跑通持久化状态机。

- 引入 LangGraph。
- 定义 `AgentState`、`AgentTool`、`ToolResult`、审批和错误协议。
- 建立工具注册中心、步骤限制、重试、暂停和恢复。
- 建立 Matter、AgentRun、AgentStep、ToolCall、Approval 基础数据模型。
- 前端显示任务步骤和等待状态。

验收：一个模拟任务可经历规划、工具执行、暂停确认、恢复、失败重试和完成，全流程可审计。

### 阶段 2：材料与法律来源基础（已完成工程基线）

目标：让 Agent 的事实与依据可追溯。

- 包装文档解析、事实提取、时间线和证据清单工具。
- 建立法律来源模型、版本、有效期和引用校验。
- 建立中国法域包和法域注册机制。
- 对材料内容实施访问控制和最小化传递。

验收：每个关键事实可定位到材料；每个法律引用可定位到有效来源；无法验证时明确降级。

### 阶段 3：中国劳动纠纷闭环（阶段 3.0～3.3 已完成）

目标：交付第一个真正可用的法律任务 Agent。

- 实现劳动纠纷事实 Schema 和动态追问。
- 包装期限计算、法律检索、证据清单和文书工具。
- 实现动态计划、结果验证和用户确认。
- 建立劳动纠纷离线评测集和端到端测试。

验收：从用户描述到仲裁申请书草稿可完整运行；缺失事实会暂停追问；高风险或不确定法域会阻止确定结论。

### 阶段 3.4：可信法律闭环与生产级加固（已完成，方案 B）

阶段 3.4 不急于扩领域、语音或开放式 ReAct，先把现有劳动闭环从“能运行”提升到“依据可信、规则可验证、变更可回归”。

#### 3.4A：保护现有基线（已完成）

- 封堵匿名法律来源登记接口，不允许普通客户端写入 `effective/trusted` 来源。
- 测试来源仅通过 fixture 或显式内部测试入口写入，并标记 `test` 信任等级。
- 引入 Alembic，以当前数据库结构建立迁移基线，停止继续依赖 `create_all` 演进正式结构。
- 建立 `evals/labor_disputes/` 评测框架，首批覆盖 30 个虚构案件及机器可读预期。
- 增加来源伪造、迁移、重复审批、重复运行和并发边界测试。

验收：外部客户端无法创建可信来源；迁移可重复执行；现有集成测试通过；评测框架可输出稳定指标。

#### 3.4B：可信法律来源内核（已完成）

- 建立 `AuthorityProvider` 协议、受控导入器、Repository、检索器和验证器。
- 来源增加 provider、external_id、canonical_url、trust_level、version、替代关系和最后验证时间。
- 第一批只导入劳动纠纷闭环必需的权威条款，不一次性建设通用爬虫或导入无边界语料。
- 小型权威语料先采用法域、日期、类型、主题过滤和 PostgreSQL 全文检索；暂不引入 pgvector。

验收：任何确定性结论都只引用可信 provider 的有效版本；失效、过期、未知或同步过旧来源必须降级或阻断。

#### 3.4C：事实、规则和交付物版本化（已完成）

- 建立确认事实断言模型，保存字段值、材料位置、用户确认和版本。
- 将劳动时效、解除、补偿/赔偿规则拆入独立规则模块。
- 规则结果必须返回使用的事实、法律来源、假设、警告和人工复核要求。
- 交付物使用“事实版本 + 来源版本 + 规则版本 + 文书类型”作为输入指纹。

验收：修改事实或来源后旧分析和旧草稿失效；核心请求可追溯到事实、材料和法条；相同输入幂等复用。

#### 3.4D：动态 Plan-and-Execute 与统一工具执行器（已完成）

- 建立 `AgentPlan` 和计划版本；Planner 第一版使用确定性任务模板。
- 至少区分欠薪、违法解除、补偿/赔偿三类劳动计划。
- `PolicyToolExecutor` 统一执行 Schema、法域、审批、超时、重试、预算和 ToolCall 审计。
- 建立运行操作幂等记录和事件 Outbox；需要慢工具时再接 SSE/WS 与异步队列。
- 工具失败只允许明确重试、换策略、重新规划或人工接管，不允许无限循环。

验收：不同争议类型生成不同计划；事实变化产生新计划版本；重复继续/审批不重复执行；工具声明真正生效。

#### 3.4E：受控引入 LLM（已完成）

- LLM 仅用于事实候选抽取、摘要、争议类型候选和检索关键词扩展。
- 输出必须通过严格 Schema；事实 quote 和 offset 必须能在原文精确匹配。
- LLM 事实只进入待确认区，不直接成为确认事实或法律结论。
- 增加 token、费用和总时长预算，并纳入评测门禁。

验收：复杂自然语言事实召回率提升，错误引用不会入库，模型或提示词变更不会突破固定安全阈值。

### 阶段 4：实时 2D 数字人

目标：把成熟的 Agent 闭环接入自然语音互动。

- 流式 STT/TTS、字幕、轮次检测和打断。
- 2D listening/thinking/tool-running/approval/speaking 状态。
- 口型同步、弱网重连和文字降级。
- 老年模式、键盘操作和屏幕阅读器适配。

验收：用户能用语音完成阶段 3 主流程；插话能终止播报；网络异常不丢失案件状态。

### 阶段 5：扩展中国法律工具与专业领域

目标：逐步覆盖合同、一般民事纠纷、文书和费用时效工具。

- 将现有业务 Service 逐步包装为统一工具。
- 不直接让 Agent 调用大型 Router 文件中的混杂逻辑；先下沉 Service。
- 每新增一个领域必须同时增加法域声明、Schema、评测和风险规则。
- 第二领域优先选择“只读合同审查”：上传合同、提取条款、识别风险、关联依据、给出修改建议；暂不自动改写或发送合同。

### 阶段 6：第二法域试点

目标：证明架构真正支持国际扩展，而不是翻译中国逻辑。

- 根据真实用户和数据来源选择第二法域。
- 新增对应法域包、法律来源适配器、日期/货币/法院体系和专业术语。
- 对比同一类任务在两个法域下的计划、工具和交付物差异。
- 支持多语言输入，但法律输出语言与适用法域分别配置。

验收：同一核心 Runtime 在不修改核心状态机的情况下加载第二法域；法域不支持的工具会明确拒绝，不静默回退到中国规则。

### 阶段 7：跨境与专业 Agent 协作

目标：处理多法域候选、准据法冲突和专业能力委派。

- 增加法域冲突识别和人工接管流程。
- 在必要时拆分检索、合同、纠纷、文书等专业 Agent。
- 总控 Agent 始终保持用户目标、审批和最终状态所有权。

## 13. 依赖顺序

```text
阶段0～3.3 已完成基线
   ↓
阶段3.4A 安全边界 + Alembic + 评测
   ↓
阶段3.4B 可信来源
   ↓
阶段3.4C 事实/规则/交付物版本
   ↓
阶段3.4D 动态 Planner + ToolExecutor + Event Outbox
   ↓
阶段3.4E 受控 LLM
   ├────────→ 阶段4 实时 2D 数字人
   └────────→ 阶段5 第二业务领域
                      ↓
                阶段6 第二法域
                      ↓
                阶段7 跨境与多 Agent
```

阶段 4 可在阶段 3 稳定后与阶段 5 并行；第二法域必须建立在法域协议和来源验证稳定之后。

## 14. 数据与审计要求

建议核心实体：

- `users` / `anonymous_identities`
- `digital_human_sessions`
- `matters`
- `matter_jurisdictions`
- `matter_facts`
- `documents`
- `evidence_references`
- `legal_authorities`
- `authority_versions` / `authority_sync_runs`
- `agent_runs`
- `agent_plans`
- `agent_steps`
- `agent_run_actions`
- `agent_event_outbox`
- `tool_calls`
- `approval_requests`
- `artifacts`
- `audit_events`

要求：

- 消息、案件、运行和工具日志分开存储。
- 敏感材料只向当前工具提供最小必要片段。
- 审计日志记录发生了什么，不记录模型隐藏思维链。
- 删除和导出必须覆盖案件、材料、运行记录和衍生交付物的关联关系。
- 法律来源保留检索时间、有效期和内容哈希。
- 正式数据结构必须通过 Alembic 版本化迁移，`create_all` 仅可用于受控测试或首次空库辅助。

## 15. 评测体系

| 指标 | 目标含义 |
|---|---|
| 法域识别准确率 | 是否选择正确国家/地区和适用时间 |
| 必要事实召回率 | 是否发现完成任务所需的关键缺失事实 |
| 事实出处覆盖率 | 关键事实中有材料或用户确认依据的比例 |
| 工具选择准确率 | 是否在正确步骤调用正确工具 |
| 工具参数正确率 | 传给工具的法域、日期、金额等是否正确 |
| 法律引用可验证率 | 引用是否真实、有效并支持结论 |
| 高风险拦截率 | 应暂停确认或转人工的场景是否被拦截 |
| 任务完成率 | 用户能否得到目标交付物 |
| 恢复成功率 | 中断后能否从正确步骤继续 |
| 语音首响应延迟 | 数字人开始反馈的时间 |
| 打断响应时间 | 用户插话到停止播报的时间 |
| 单任务成本 | 模型、检索、语音和存储成本 |

每次更换模型、提示词、法域包、检索源或工具版本都必须运行固定评测集。

## 16. 明确不做

- 不以 3D 作为数字人成熟度标准。
- 不让模型直接访问数据库表或任意内部接口。
- 不使用一个超大 Agent Service 承载规划、工具、数据库和 UI 状态。
- 不让多个 Agent 无约束自由讨论。
- 不把用户所在地直接等同于适用法律。
- 不在法域不明时静默使用默认中国法。
- 不自动执行影响用户权利的外部动作。
- 不把未经验证的模型回答包装成确定法律意见。

## 17. 总体完成标准

满足以下条件时，可认为最终目标基本实现：

1. 用户可通过文字、语音和文件与 2D 法小助自然互动，并可随时打断。
2. 法小助可创建并持续维护独立案件工作区。
3. Agent 可动态追问、规划、调用工具、验证、暂停确认、恢复和重新规划。
4. 关键事实和法律结论均具有可展示的来源、适用法域、时间和不确定性。
5. 高风险动作受规则和人工审批控制，完整过程可审计。
6. 至少两个法域在同一 Runtime 下完成真实任务闭环，核心层没有中国法硬编码。
7. 新增法域主要通过法域包、来源适配器、工具实现和评测集完成，而不是复制整套 Agent。
8. 用户能得到可审阅、修改、导出或转人工的实际交付物，而非只有聊天回复。

## 18. 下一步执行入口

阶段 3.4A～3.4E 已全部落地。下一步执行入口：

1. 在受控环境运行官方法源同步，并建立定期复核任务。
2. 扩充时效中断、中止、劳动关系存续期间欠薪等评测案例。
3. 用真实脱敏材料验证受控 LLM 候选召回率；未配置模型时继续使用确定性提取器。
4. 完成并发压测、Outbox 消费器和生产监控后，再进入阶段 4 实时数字人。
