# 多法域数字人法律 Agent 总体规划

更新时间：2026-07-27
规划对象：YYS-Law 全局数字人“法小助”  
规划性质：长期目标架构与分阶段实施基线
当前决策：采用方案 C“统一 Runtime Graph + 可插拔 Domain Package + 声明式 PlanTemplate + 运行时版本化 Plan”。阶段 3.6、3.7A/3.7A.1与3.7B已完成；3.7C代码已实现并等待4个官方法源版本人工复核，状态 `READY_FOR_ACCEPTANCE`。后续已正式规划为 3.7D Conversation Foundation、3.7E Conversation × Workspace、3.7F Digital Human Interaction、3.7G Voice Interaction、3.7H Agent Engineering & Evaluation，但均未开始实施。阶段3.5的生产可信化待办暂缓；通用非劳动聊天自动分流和其他真实法律领域尚未接入。

当前产品聚焦：以“劳动用工法律服务”为首个长期深耕领域，以大学生实习、兼职和毕业初期青年劳动者为第一批用户入口。该定位只约束首批产品场景，不把 Runtime、领域协议或数据结构写死为校园专用系统。

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

### 1.1 当前垂直定位与产品入口

```text
通用法律 Agent Runtime
└─ 劳动用工 Domain Package
   └─ 青年就业场景产品入口
```

- **行业领域**：劳动用工法律服务。
- **第一批用户**：大学生实习、兼职以及毕业初期的年轻劳动者。
- **首批问题**：劳动关系判断、欠薪、试用期、辞退、违约金、经济补偿和仲裁准备。
- **后续扩展**：普通劳动者、灵活就业者、外卖骑手、平台用工和工伤等劳动场景。
- **推广路径**：个人直接使用；学校就业中心、团委、法律援助机构等作为触达和服务渠道。

数字人和 Agent 在架构上解耦、在产品体验上组合：Agent 负责解决法律问题，数字人负责把追问、材料上传、任务状态和法律解释变成普通用户容易理解的交互。

当前不把电商、外贸或宽泛校园纠纷作为并行主线。原因不是这些方向没有价值，而是它们需要新的法源、规则、工具、验证策略和评测集，会削弱首个劳动闭环的可信度和比赛表达。

## 2. 当前基线与主要差距

当前法小助已经从“LLM 问答 + 意图分类”推进到首个可恢复的法律任务闭环。现有实现包括：数字人会话、Matter 工作区、显式中国法域确认、材料分片与事实定位、劳动事实建议、LangGraph Runtime、工具白名单、ToolCall 审计、审批暂停恢复、结构/事实/来源/风险四类验证、步骤与工具预算，以及中国劳动纠纷草稿闭环。

当前闭环仍属于工程验证版本，尚未达到生产级法律服务标准。可信写入边界、迁移基线、模板 Planner 和官方来源适配器已经具备；当前主要阻断项变为：官网可用性与变更人工复核、劳动实体规则覆盖、真实脱敏评测、身份权限、运维监控和长期运行验证。

| 能力 | 当前状态 | 目标状态 |
|---|---|---|
| 数字形象 | 8 张状态图与 CSS 动效 | 2D 骨骼/序列动画、口型、语音状态同步 |
| 对话 | 文本请求-响应，闲聊 LLM 与任务工作台仍分离 | 实时文字/语音、可打断、流式事件 |
| 任务理解 | 已有劳动任务入口和缺失事实追问 | 通用目标、任务类型、法域、风险和完整度识别 |
| 记忆 | 会话、Matter、Run、Step 和审批可恢复 | 用户偏好、事实版本、计划版本和运行状态分层存储 |
| 行动 | 可调用材料、证据清单、劳动分析和草稿工具 | 调用检索、计算、合同、纠纷、文书和平台工具 |
| 计划 | 劳动领域三步模板，按争议类型调整首步重点 | Domain Package 注册模板，Planner 受限选择/裁剪，生成不可静默修改的版本化 Plan |
| 执行 | 劳动专用 Graph 顺序执行两个步骤，审批后由 `draft` 节点执行第三步 | 一套全局 Runtime Graph 按 Step 循环，业务文书只是可审批的普通 Step |
| 验证 | 已有结构、事实、来源、风险四类确定性验证 | Global/Domain/Task 三层 Verifier + Observation + Decision Router |
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

### 3.8 一套全局 Runtime Graph

- Runtime Graph 只管理上下文、规划、单步执行、观察、验证、决策、审批、恢复、预算和审计。
- Runtime Graph 不写入劳动仲裁、合同审查、起诉状等业务步骤，不为每个模板复制一套 Graph。
- 文书生成属于 Plan 中的 `document_drafting` Step；是否出现由模板和本次 Plan 决定，不是全局必经节点。

### 3.9 Domain Package 提供能力，不掌握全局状态

每个领域能力包统一声明：

```text
Domain Package
├─ routing_rules
├─ plan_templates
├─ tools
├─ verification_policies
└─ optional_subgraphs
```

能力包先注册到 `CapabilityRegistry`，Task Router、Planner、ToolExecutor 和 Verifier 只通过注册中心查询能力。领域代码不得直接修改全局 Run 状态、绕过审批或自行推进其他领域步骤。

### 3.10 PlanTemplate 与 Plan 分离

- `PlanTemplate` 是开发者和法律专业人员审核过的任务策略，声明允许步骤、依赖、可选条件、工具范围、审批和验证策略。
- `Plan` 是某次 Run 根据模板、案件事实和用户目标生成的执行快照，必须记录模板版本、计划修订号、参数、跳过原因和触发依据。
- Plan 生成后不可静默原地修改；重规划必须创建新 revision，并保留差异、原因和触发者。

#### 3.10.1 LangGraph 与问题组合策略

LangGraph 不随欠薪、辞退或补偿问题动态拼装。项目长期保持一套固定 Runtime Graph，只负责：上下文、计划、单步执行、观察、验证、决策、审批、恢复、预算和审计。

真正随问题变化的是 Plan：

1. 案件分流器识别领域、任务类型、争议标签和风险等级。
2. Planner 选择一个经过审核的主 PlanTemplate。
3. 根据已确认事实启用模板允许的可选步骤，并填充工具参数。
4. 对共同步骤进行依赖排序和去重，例如证据检查、法源验证只执行一次。
5. 生成本次 Run 的不可变 Plan revision，由固定 Runtime Graph 逐 Step 执行。

劳动领域不为“欠薪、违法解除、经济补偿”等分别复制 Domain Package 或 Graph，而是在同一个 `cn_labor` 能力包中注册任务模板、规则、工具和验证策略。建议的模板演进为：

```text
labor_relationship_assessment
labor_consultation
wage_arrears_resolution
termination_analysis
labor_compensation_analysis
labor_case_analysis
labor_arbitration_application
```

复合案件以“主模板 + 争议标签 + 允许的可选步骤”组合。例如欠薪与违法解除并存时，共用劳动关系判断、材料和证据检查，再分别执行欠薪金额分析与解除合法性分析，最后统一完成法源验证、请求整理和可选文书步骤。

LLM 可以提出任务类型、争议标签或步骤候选，但不能自由创造工具、绕过模板依赖、审批和验证策略。新增事实导致原计划不再适用时，必须创建新 revision，禁止直接覆盖旧 Plan。

### 3.11 Subgraph 只处理特殊控制流程

只有具备独立生命周期、多轮循环、中断恢复或独立审批的能力才允许注册 Subgraph，例如证据真实性多轮核验、合同逐条审查修订循环。普通“检索→分析→生成”继续使用 PlanTemplate，禁止把 Domain Package 演变成隐藏的第二套 Runtime。

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
    │   ├── graph.py              # 唯一全局 Runtime Graph
    │   ├── state.py
    │   ├── task_router.py
    │   ├── planner.py
    │   ├── executor.py
    │   ├── observer.py
    │   ├── verifier.py
    │   ├── decision_router.py
    │   ├── policies.py
    │   └── checkpoints.py
    ├── capabilities/
    │   ├── registry.py           # Domain/模板/工具/策略统一注册入口
    │   ├── domain.py
    │   ├── templates.py
    │   └── plans.py
    ├── domains/
    │   ├── labor/                # 首个迁移领域
    │   ├── consultation/
    │   ├── contracts/
    │   ├── disputes/
    │   └── drafting/
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
- `capabilities/` 只保存注册协议、声明式模板和运行时 Plan 契约，不承载领域业务实现。
- `domains/` 以能力包形式提供模板、工具适配、路由规则和验证策略；不得拥有全局 Run 状态机。
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
    domain_id: str | None
    task_type: str
    risk_level: str
    jurisdiction: JurisdictionContext | None

    facts: list[LegalFactRef]
    missing_facts: list[MissingFact]
    document_ids: list[str]

    plan_id: str | None
    template_id: str | None
    template_version: str | None
    plan_revision: int
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
deciding
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
CapabilityRuntime：启动或恢复 Run
        ↓
Capability Registry：把 task_type 一次解析为领域包和计划模板，并绑定到 Run
        ↓
dispatch：根据 Run 当前状态选择 Graph 入口
        ↓
ensure_context：检查目标、法域、事实、材料和权限
        ├─ 不完整 → 持久化等待并追问用户
        └─ 完整
              ↓
build_plan：选择 PlanTemplate，生成新的 Plan revision
              ↓
select_next_step
              ↓
execute_step：ToolRegistry + PolicyToolExecutor 执行一个 Step
              ↓
observe_step：标准化 ToolResult、状态变化和引用
              ↓
verify_step：Global + Domain + Task 三层验证
              ↓
decide_step
  ├─ next_step        → select_next_step
  ├─ retry_step       → execute_step
  ├─ request_context  → ensure_context
  ├─ replan           → build_plan（创建新 revision）
  ├─ require_approval → 暂停，批准后继续当前/下一 Step
  ├─ reject/handoff   → 阻断或人工接管
  └─ finish           → final_verify → completed
```

`execute_step`、`observe_step`、`verify_step` 和 `decide_step` 均只处理一个 Step。Runtime 不允许一个节点隐式跑完整份 Plan。

硬限制：

- 单次运行最大步骤数、工具调用数、模型费用和总时长可配置。
- 同一工具和等价参数连续失败两次后禁止盲目重试。
- 高风险动作执行前必须有未过期的用户审批。
- 任务可在任意等待用户的节点持久化并恢复。
- 可选步骤被跳过时必须保存 `skip_reason`；工具失败不得被记为跳过。
- 重规划必须保留旧 Plan，新增 revision 并记录差异、原因和触发来源。
- 不向用户展示模型内部思维链，只展示任务目标、当前步骤、依据、假设和等待事项。

### 7.1 Runtime、能力包和计划的关系

```text
Runtime Graph = 通用编排内核
Capability Registry = 领域能力查询入口
Domain Package = 可插拔法律能力
PlanTemplate = 经审核的任务策略
Plan = 本次运行的不可变执行快照
Subgraph = 特殊控制流程扩展
```

### 7.2 Domain Package 契约

```python
class DomainPackage:
    domain_id: str
    version: str
    routing_rules: list
    plan_templates: list
    tools: list
    verification_policies: list
    optional_subgraphs: dict
```

### 7.3 PlanTemplate 最小契约

```python
class PlanTemplate:
    template_id: str
    version: str
    domain_id: str
    task_type: str
    allowed_step_types: list[str]
    steps: list[TemplateStep]
```

模板步骤至少声明：`step_type`、`tool_name`、`depends_on`、`optional`、`requires_approval`、`verification_policy_ids`、`on_failure`。Planner 只能选择注册模板、填充参数、跳过有条件的可选步骤或插入模板显式允许的补充步骤。

### 7.4 运行时 Plan 契约

```json
{
  "plan_id": "plan_xxx",
  "template_id": "labor_arbitration_application",
  "template_version": "1.0.0",
  "plan_revision": 2,
  "replan_reason": "补充了劳动关系解除日期",
  "steps": [
    {
      "step_id": "step_xxx",
      "step_type": "evidence_analysis",
      "tool_name": "generate_evidence_checklist",
      "status": "skipped",
      "skip_reason": "用户已提供且验证通过完整证据清单"
    }
  ]
}
```

### 7.5 分层 Verifier 和决策输出

```text
Global Verifier：结构、工具权限、预算、状态流转
Domain Verifier：法域事实、来源、时效、管辖和领域规则
Task Verifier：交付物字段、请求与事实、证据支撑和前后一致性
```

Verifier 只返回验证报告，不直接修改 Run 状态。`DecisionRouter` 将报告归一为：`pass`、`need_context`、`retry`、`replan`、`require_approval`、`reject` 或 `handoff`。

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
    side_effect: bool
    idempotent: bool
    required_permissions: list[str]
    supported_domains: list[str]
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

#### 3.4D：模板化 Plan-and-Execute 与统一工具执行器（已完成基线）

- 建立 `AgentPlan` 和计划版本；Planner 第一版使用确定性任务模板。
- `LaborPlanBuilder` 根据欠薪、违法解除等争议调整核对重点，但当前工具序列仍为证据清单、劳动分析和审批后草稿三步；它不是通用动态 Planner。
- `PolicyToolExecutor` 统一执行 Schema、法域、审批、超时、重试、预算和 ToolCall 审计。
- 建立运行操作幂等记录和事件 Outbox；需要慢工具时再接 SSE/WS 与异步队列。
- 工具失败只允许明确重试、换策略、重新规划或人工接管，不允许无限循环。

验收：争议类型可以调整模板重点；事实变化产生新计划版本；重复继续/审批不重复执行；工具声明真正生效。多模板选择、条件步骤和 Verifier 驱动重规划转入阶段 3.6。

#### 3.4E：受控引入 LLM（已完成）

- LLM 仅用于事实候选抽取、摘要、争议类型候选和检索关键词扩展。
- 输出必须通过严格 Schema；事实 quote 和 offset 必须能在原文精确匹配。
- LLM 事实只进入待确认区，不直接成为确认事实或法律结论。
- 增加 token、费用和总时长预算，并纳入评测门禁。

验收：复杂自然语言事实召回率提升，错误引用不会入库，模型或提示词变更不会突破固定安全阈值。

### 阶段 3.5：生产可信化与运行保障（执行中）

目标：把“可恢复的确定性模板工作流”推进为可审计、失败关闭、可长期运行的法律服务基线。

已完成第一批：

- 官方 Provider 不再返回代码内置法条；按白名单 HTTPS 主源/官方备用源下载 HTML 或 PDF，并从原文抽取指定条款。
- 保存每次同步批次和官方响应原始字节快照；法条能够追溯到下载 URL、响应哈希、媒体类型和验证方法。
- 相同正文只刷新核验时间；官网正文变化生成新版本、停用旧版本并进入 `review_required`，未经内部人工复核不能支持确定性结论。
- 来源设置七天新鲜度；过期、同步失败、变更待复核和被替代版本均从检索中排除。
- 官网不可达或解析失败时记录失败批次并安全阻断，不回退到人工摘要或模型生成法条。
- 同一 Matter/任务创建 Run 时使用 PostgreSQL 事务 advisory lock；单个 Run 执行时使用 session advisory lock，降低并发双击导致重复工具和草稿的风险。
- 工具线程超时改为 `TOOL_TIMEOUT_UNCERTAIN`，禁止自动重试可能仍在后台结束的调用。
- 数据库凭据移出源码，只从 `DATABASE_URL` 读取；生产默认关闭启动时 `create_all`，结构由 Alembic 管理。
- 时效计算由固定 365 天改为自然年推进，并显式支持劳动关系存续欠薪的开放期限类型和人工复核标记。

待完成：

- 由法律专业人员审核官网快照和规则金标。工程侧已提供待复核列表、候选/旧版正文对照、批准/驳回 CLI，以及复核人、说明和时间审计；当前四个官方来源版本均处于 `review_required`，不得自动启用。
- 在部署环境配置法源定时任务和告警接收端；工程侧已提供 `authority sync`、`health --strict`、逐来源 `partial_failed` 和非零退出码。Outbox 消费监控、备份恢复演练和多实例压测仍待完成。
- 完成登录身份、Matter 权限、敏感材料加密和审计留存策略。

2026-07-16 法源治理第二批已完成：

- 新增 `authority_source_reviews`，正文变化后的批准/驳回均独立记录复核人、说明、快照和时间。
- 同步批次记录 `trigger`、`requested_by` 和逐来源 `failed_count`；同一批次允许成功来源入库、失败来源继续阻断，整体健康门禁不因部分成功而放宽。
- 修复官网目录和正文重复条号导致的错误截断：优先识别行首条文标题，同一条号选择最长正文，正文中的条款引用不再被误判为边界。
- 首批来源从两组时效条款扩展为四组，增加《劳动合同法》欠薪、解除、经济补偿、违法解除条款和《劳动法》工资支付条款，均来自官方白名单站点。
- 该批次当时两组实体法来源为 `verified`、两组时效来源为 `review_required`；截至3.7C收尾，四组当前版本均待人工复核，健康状态为 `unavailable`，系统继续失败关闭。

阶段 3.5 验收门槛：确定性结论有效法源覆盖率 100%；无依据确定性结论为 0；事实/法源变化后旧草稿失效 100%；并发继续请求不重复执行工具；同步失败可告警且任务安全阻断。

### 阶段 3.6：方案 C 通用 Runtime、领域解耦与旧架构清理（已完成，2026-07-16）

目标：把劳动专用 Graph 提炼为一套全局 Runtime Graph，并让现有法律功能通过 Domain Package 渐进接入。

1. 建立 `CapabilityRegistry`、`DomainPackage`、`PlanTemplate`、`PlanRevision` 和分层验证契约。
2. 将 Graph 改为明确的单 Step 循环：`select → execute → observe → verify → decide`。
3. 将 Verifier 与状态路由解耦，由 `DecisionRouter` 统一产生 next/retry/context/replan/approval/handoff/finish 决策。
4. 把现有劳动三步计划下沉为 `labor_arbitration_application` 模板；保留原入口作为兼容适配器。
5. 增加 `labor_consultation`、`labor_case_analysis` 两个只读模板，验证同一领域多任务。
6. Plan revision 不可覆盖更新；可选步骤必须记录跳过原因；模板、工具和验证策略均记录版本。
7. 迁移过程保留旧页面和旧接口，每次接入一个领域；新 Runtime 稳定并通过回归后再切换入口。
8. 领域运行差异统一通过 `DomainRuntimeAdapter` 接入；通用 Runtime 禁止直接依赖领域 Service。

验收：新增模板不修改 Runtime Graph；同一模板可因事实不同生成不同 Plan；Verifier 可触发补充信息、单步重试或新 revision；劳动三类任务共享同一单步执行内核；现有劳动仲裁闭环行为保持兼容。

实施结果：

- 新增 `capabilities/` 契约和注册中心，领域包注册前校验模板、路由和工具白名单，重复注册失败关闭。
- 新增唯一 `CapabilityRuntimeGraph`，当前固定节点为 `dispatch → ensure_context → build_plan → select_next_step → execute_step → observe_step → verify_step → decide_step`；`task_type` 在进入 Graph 前由 `CapabilityRuntime` 每次请求解析一次并绑定到 Run，Graph 内不再重复路由，也没有劳动仲裁或文书工具名。
- `LayeredVerifier` 只生成 Global/Domain/Task 报告，`DecisionRouter` 独立产生 next/retry/context/replan/reject/handoff/finish；审批由步骤声明在执行前暂停。
- `agent_plans` 的每一行作为不可覆盖 revision，记录 domain、模板及版本、触发者、重规划原因和父计划；Step 保存类型、策略版本、跳过原因、Observation、Verification 和 Decision。
- 中国劳动能力包注册 `labor_arbitration_application`、`labor_consultation`、`labor_case_analysis`。旧 `cn_labor_dispute` 作为路由别名，旧 Router/Facade 方法签名与页面继续兼容。
- `CapabilityRegistry` 成对注册 `DomainPackage + DomainRuntimeAdapter`。劳动事实、法域、计划定制、工具参数和劳动校验已下沉到 `domains/labor/`；阶段 1 模拟摘要已下沉为 `domains/mock/` 能力包。
- 已删除两套旧执行内核及旧劳动 Planner：`runtime/runtime.py`、`runtime/graph.py`、`runtime/labor_runtime.py`、`runtime/labor_graph.py`、`runtime/planner.py`。旧 HTTP 方法只保留 Facade 薄包装。
- 新增架构边界测试，禁止旧文件回归，并禁止通用 Runtime 直接导入 domains、labor_disputes、matters、jurisdictions。
- Alembic 已升级到 `20260716_0004`；阶段 3.1、3.2、3.6 相关 10 个回归通过，前端 TypeScript 检查通过。

### 阶段 3.7：劳动用工垂直深化与数字人入口融合（进行中）

目标：不扩张新法律领域，先把劳动用工从“仲裁流程样板”深化为可分流、可组合、可解释的青年就业法律服务闭环。

#### 3.7A：案件分流与劳动关系判断

- 在普通咨询、劳动关系判断、正式劳动纠纷、非劳动纠纷和高风险人工处理之间分流。
- 对实习、兼职、勤工助学等场景先判断法律关系，不因出现“工资”或“欠薪”就默认进入劳动仲裁。
- 分流结果保存任务类型、争议标签、判断依据、缺失事实、风险等级和推荐下一步。
- 普通数字人聊天命中劳动场景后，通过受控入口创建并绑定 Matter，再按分流结果启动对应 Agent 任务。

实施结果（2026-07-21）：

- 新增 `LaborCaseTriageService` 与版本化 `labor_case_triages`，保存结构化分流事实和判断结果；结果包含五类分流、争议标签、关系倾向、依据、缺失事实、风险等级、推荐任务和人工复核标记。
- 新增 `labor_relationship_assessment` PlanTemplate 和 `assess_labor_relationship` 白名单工具，与现有劳动咨询、案件分析、仲裁申请共用同一 `CapabilityRuntimeGraph`。
- 判断同时核对主体资格、有偿劳动、劳动管理、业务组成和就业目的；学生身份、协议名称或“工资/欠薪”关键词均不能单独决定劳动关系。
- 学校安排实习、勤工助学、在校兼职、非劳动纠纷和人身/期限等高风险场景均有独立失败关闭分支；初筛结果明确 `legal_conclusion=false`，不替代仲裁、法院或法律专业人员认定。
- 新增分流读写 API；阶段 3.7A.1 进一步将聊天会话、Matter、分流结果、Agent Run 和右侧工作台绑定为同一状态链。简单咨询、劳动关系判断和正式纠纷分别启动既有 `labor_consultation`、`labor_relationship_assessment`、`labor_case_analysis`；缺失事实等待补充，非劳动和高风险不启动自动 Runtime。
- 当前没有真实人工服务通道，高风险仅标记“需要人工复核”，不得表述为已经转接律师；完整数字人 Agent 回归 45/45 通过。

#### 3.7B：劳动模板和组合式 Plan

- 在现有劳动咨询、案件分析、仲裁申请三个模板基础上，补充劳动关系判断、欠薪、解除和补偿分析模板。
- 以主模板为骨架，根据争议标签启用白名单可选步骤；处理依赖、去重、审批和失败策略。
- 复合劳动案件仍由一个 Run 和一份版本化 Plan 管理，不启动多个无共享状态的 Agent。
- 增加 Plan 组合边界测试：禁止未声明工具、重复公共步骤、越权文书步骤和原地覆盖 revision。

实施结果（2026-07-21）：

- 保留唯一 `CapabilityRuntimeGraph`；`labor_case_analysis` 与 `labor_arbitration_application` 按交付目的作为主模板，欠薪、解除、经济补偿下沉为模板内白名单可选步骤。
- 新增稳定标签 `wage_arrears`、`termination`、`economic_compensation`；兼容既有中文 `claim_types`，但任何未知标签均以 `INVALID_PLAN_COMPOSITION` 失败关闭。
- 公共证据检查、统一期限与法源分析、审批和草稿步骤均只声明一次；三个问题步骤按标签启用，未启用步骤保存 `skip_reason` 和空触发标签。
- Plan 持久化保存 `dispute_tags`、组合契约版本和步骤触发标签；补充事实后在同一 Run 创建新 revision，旧 Plan 保持不变并通过 `parent_plan_id` 追溯。
- Capability Registry 在领域 Adapter 定制后再次校验完整计划，禁止插入/删除步骤、替换工具、修改依赖或削弱审批；未新增数据库结构或 Runtime Graph 节点。
- 阶段 3.7B 专项及完整数字人 Agent 回归 49/49 通过，Python 编译、前端 TypeScript 检查和用户验收通过；验收中发现的解除日期/原因材料链路与步骤状态文案问题已修复。阶段 3.7B 正式完成，3.7C 仅完成任务初始化。

#### 3.7C：事实、证据、法源和规则深化

- 扩充实习协议、劳动合同、Offer、解除通知、考勤、工资记录和聊天记录的材料适配。
- 完善劳动关系、欠薪、试用期、解除、补偿和赔偿规则；结果必须返回事实、证据、法源、假设和人工复核要求。
- 完成当前官网法源待复核版本、规则金标和真实脱敏评测，法源健康未达门槛时继续失败关闭。
- 为青年就业旗舰案例建立正常、信息不足、非劳动关系、复合争议和高风险五类评测。

实施结果（2026-07-22）：

- 新增七类劳动材料领域适配器和证据矩阵；所有候选保留原文定位且不自动确认为案件事实。
- 新增欠薪、试用期、解除、补偿/赔偿版本化规则，劳动关系结果同步增加事实、证据和法源引用；规则统一保留假设、警告和人工复核标记。
- `probation` 作为主模板内白名单可选步骤接入，仍共享唯一 Runtime Graph；实体法源或关键事实不足继续失败关闭。
- 官方法源范围补入劳动关系和试用期核心条款；五类25条旗舰金标区分合成数据与官方公开案例改写。
- 阶段3.7C专项5/5、完整数字人Agent回归54/54和Python编译通过；未新增数据库表列，未修改前端或进入3.7D。生产法源4/4当前为 `review_required`，必须人工批准并达到 `ready` 后才完成最终验收。

#### 3.7C → 3.7D～3.7H 演进说明

```text
旧设计
→ 3.7D 统一承载一次一问、状态解释、流式文字、取消和基础语音

当前实施结果
→ 3.7A～3.7C 已完成劳动分流、Matter/Triage/Run/Workspace 最小绑定、
  组合式 Plan、事实证据、法源与劳动实体规则
→ 普通聊天仍使用固定最近 6 条历史
→ 普通 sendMessage 与前端劳动关键词分流仍是分散入口
→ 尚无 Rolling Summary、Structured Memory、ContextBuilder、
  统一 Router、Conversation Orchestrator 和会话 Trace

新阶段规划
→ 将原 3.7D 拆分为 3.7D～3.7H
→ 先建设统一会话基础，再建设工作台协同、流式数字人、语音和工程化评测
```

该拆分只细化后续实施顺序，不修改、覆盖或否定阶段 1～3.7C 的历史设计与实施结果。劳动 Agent 业务扩展在本轮冻结，现有 `CapabilityRuntimeGraph`、劳动 Domain Package、Plan、工具、验证、审批和持久化继续作为稳定执行内核。

#### 3.7D Conversation Foundation

目标：在不重写 Agent Runtime 的前提下，建立初始聊天模式和案件陪伴模式共用的会话基础设施，解决长对话、上下文构建和分散分流问题。

为什么现在做：

- `digital_human_messages` 已保存完整原始消息，但当前 LLM 每轮只读取最近 6 条，长对话会丢失用户目标和旧事实修改。
- 当前没有 Rolling Summary、Structured Memory、Token Budget 或统一 ContextBuilder。
- 前端仍存在 `sendMessage → isLaborQuestion → laborTriage.start` 的分散控制，普通回复、劳动分流、Matter 创建和 Agent 启动不属于同一个决策入口。
- Matter 已通过 `session_id` 持久绑定聊天 Session，但前端恢复仍依赖 `laborContextBySession` 本地缓存。

Memory 最终结构：

```text
Raw Messages
    +
Recent Window
    +
Rolling Summary
    +
Structured Memory
```

实施顺序必须为：

```text
Raw Messages
    ↓
Recent Window
    ↓
Structured Memory
    ↓
ContextBuilder
    ↓
Rolling Summary
```

- Raw Messages 继续完整持久化，不把全部历史逐轮发送给模型。
- Recent Window 从固定消息条数改为 Token Budget。
- Structured Memory 只保存当前主题、用户目标、会话阶段、Matter 关联、用户陈述、已确认决定和待解决问题等结构化信息。
- Rolling Summary 在基础 Memory 和 ContextBuilder 稳定后接入，3.7D 完成前必须具备长对话压缩能力，不在第一步构建复杂长期记忆系统。
- `Conversation Memory ≠ Matter Confirmed Facts`。聊天中的事实只能标记为 `user claim` 或 `candidate fact`；Assistant 历史内容不得成为正式案件事实来源。

统一 ContextBuilder 根据当前是否存在 Matter 自动切换上下文：

```text
无 Matter：
System / Guardrails
+ Structured Memory
+ Rolling Summary
+ Recent Messages
+ Current User Message

进入 Matter 后：
System / Guardrails
+ Current Matter Confirmed Facts
+ Current Agent State
+ Structured Memory
+ Rolling Summary
+ Recent Messages
+ Current User Message
```

统一优先级：

```text
安全规则 / 当前输入
    >
Matter 已确认事实
    >
Agent 真实状态
    >
最新用户陈述
    >
Structured Memory
    >
Rolling Summary
    >
较旧聊天历史
```

- 用户新陈述与 Matter 正式事实冲突时，不静默覆盖；数字人提示用户确认，并引导在工作台修改。
- 摘要与正式事实冲突时丢弃摘要中的冲突内容。
- Token 不足时优先压缩旧聊天，不截断安全规则、当前输入、Matter 已确认事实和 Agent 当前状态。

Router 与 Conversation Orchestrator 必须保持独立：

```text
Router
→ 判断“当前输入去哪里”

Conversation Orchestrator
→ 根据 Session、Memory、Matter、Run 和 RouterDecision
  判断“下一步做什么”

Agent
→ 真正执行案件分析
```

Router 采用“高优先级确定性规则 + 模糊场景结构化 LLM”组合，输出限定为：

```text
normal_chat
labor_consultation
labor_triage
matter_interaction
agent_continue
workspace_guidance
high_risk_handoff
```

Router 不创建 Matter、不启动 Agent、不执行审批。Orchestrator 统一执行 `reply_only`、`ask_one_key_question`、`create_matter`、`guide_to_workspace`、`start_agent`、`continue_agent`、`request_approval` 和 `stop_for_risk` 等受控动作。

产品规则：

- 普通劳动咨询不因命中关键词立即创建 Matter。
- 明确进入案件处理或完成最低限度分流后，再创建 Matter。
- 数字人每轮最多追问一个关键分流问题，并解释询问原因。
- 大量案件字段、材料和完整 `missing_facts` 统一交给工作台。
- 高风险、法源不足、审批和外部动作不能被会话层绕过。

预计涉及现有模块：

- `frontend/src/components/DigitalHuman/DigitalHumanChat.tsx`
- `frontend/src/components/DigitalHuman/useLaborTriage.ts`
- `frontend/src/store/digitalHumanStore.ts`
- `frontend/src/services/digitalHumanApi.ts`
- `flask_app/routers/digital_human.py`
- `flask_app/services/digital_human_service.py`
- `flask_app/models/db_models.py`

后续可新增独立 `conversation/` 服务包，分别承载 schemas、memory、token budget、context builder、router、orchestrator 和 actions；`digital_human_service.py` 保留兼容入口，禁止继续扩成超大 Service。

对现有 Agent 的影响：Memory、ContextBuilder、Router 为低风险；Orchestrator 接管调用入口为中风险；不修改现有 Runtime Graph、领域能力、Plan、Tool、Verifier 和持久化协议。

验收：

- 30～50 轮对话后仍能正确识别用户目标，输入 Token 在摘要后趋于稳定。
- 用户修改旧陈述后不继续使用旧候选值，且不会自动覆盖 Matter 正式事实。
- Assistant 历史推测进入正式案件事实的数量为 0。
- 同一句输入只进入一个 Router/Orchestrator 主流程。
- 普通咨询不自动创建空 Matter；高风险和法源不足场景保持失败关闭。

对应 Agent 知识：Memory、Context Engineering、Token Budget、Router、Orchestrator、事实来源隔离。

#### 3.7E Conversation × Workspace

目标：形成“初始聊天模式 → 当前 Matter 工作台 → 工作台侧边数字人”的连续产品体验，数字人、工作台和 Agent 各自承担明确职责。

产品包含两种交互模式。

**模式一：初始聊天模式**

```text
数字人完整聊天界面
    ↓
普通法律咨询
    ↓
理解用户需求
    ↓
Router 分流
    ↓
必要的关键追问
    ↓
满足条件后创建 Matter
    ↓
进入案件工作台
```

数字人负责接待、普通咨询、理解需求、劳动问题识别、关键分流问题、引导建立 Matter 和引导进入工作台。不得在该阶段连续询问大量案件字段。

**模式二：案件陪伴模式**

```text
完整聊天区域退出或弱化
    ↓
工作台成为主要操作区域
    ↓
数字人保留在工作台侧边
    ↓
围绕当前 Matter 持续沟通
```

数字人负责：

- 解释案件进度和下一步操作。
- 解释 Agent 当前状态。
- 提醒材料或信息缺失。
- 发起关键确认和审批确认。
- 回答当前 Matter 相关问题。
- 简要总结最终结果。

工作台继续负责：

- 大量案件事实和结构化字段。
- 材料上传、候选事实确认和证据。
- 时间线、法源、Agent Plan 和完整 `missing_facts`。
- 文书编辑和导出。

数字人不能变成案件表单录入机器人。

两种模式必须共享同一套：

```text
Session
Memory
Structured Memory
Rolling Summary
Recent Window
ContextBuilder
Router
Conversation Orchestrator
Trace
```

禁止为工作台侧边数字人建立第二套 Memory、第二套聊天后端或第二套 Orchestrator。UI 可以切换呈现方式，但 Session 和会话状态必须连续。

服务端恢复：

- Session、Matter 和 Agent Run 的数据库关系是权威来源。
- `laborContextBySession` 只作为前端缓存。
- 清理 localStorage 或刷新页面后，前端必须能按当前 Session 从服务端恢复 Matter、Triage 和 Run。

Conversation Presenter 采用确定性映射，不让 LLM 自由解释 Agent 状态：

```text
planning             → 正在整理案件处理步骤
verifying            → 正在核对法律依据
awaiting_information → 还有案件信息需要在工作台补充
blocked_authority    → 缺少可靠法律依据，系统已停止生成结论
awaiting_approval     → 草稿已经准备好，需要用户确认
completed             → 本次案件分析已完成
```

预计涉及现有模块：

- `frontend/src/components/DigitalHuman/DigitalHumanChat.tsx`
- `frontend/src/components/DigitalHuman/LaborTriageCard.tsx`
- `frontend/src/components/DigitalHuman/DigitalHumanMatterWorkspace.tsx`
- `frontend/src/store/digitalHumanStore.ts`
- `flask_app/routers/digital_human_agent.py`
- 现有 Matter、Triage、Agent Run 查询与持久化模块

可新增 Conversation Presenter 和轻量状态卡，但不复制 Agent 状态机。

对现有 Agent 的影响：低风险，只读取现有状态并调用既有 Facade。

验收：

- 初始聊天与工作台侧边数字人使用同一 Session，切换后历史和 Memory 连续。
- 清除 localStorage 后仍能从服务端恢复当前 Matter/Run。
- 聊天区域只呈现通俗摘要和下一步，内部模板 ID、英文状态和完整步骤留在工作台。
- 数字人只做关键确认，完整缺失字段仍由工作台处理。

对应 Agent 知识：Conversation Presenter、Human-in-the-loop、状态投影、会话与任务协同。

#### 3.7F Digital Human Interaction

目标：在会话和工作台协同稳定后，补齐文字流式输出和统一数字人状态控制。

当前后端虽调用 `llm.stream()`，但内部聚合完成后才一次性返回；前端动画状态也由多个业务位置直接设置。后续统一采用 Conversation SSE 事件协议和 AvatarController。

建议事件：

```text
meta
status
delta
presentation
done
error
```

交互状态：

```text
Request
→ thinking
→ Streaming 开始
→ speaking
→ Streaming 结束
→ idle
```

AvatarController 状态收敛为：

```text
idle
listening
thinking
speaking
serious
success
```

- 当前 PNG 状态继续作为稳定降级资源。
- WebM/视频循环动画逐步替换 PNG，但属于表现增强，不阻塞会话闭环。
- 流式中断后，未完成的 Assistant 文本不得作为正式历史进入下一轮 Context。
- SSE 只输出状态、可展示内容和结果，不输出模型思维链。
- 优先采用与当前 Flask 技术栈兼容的直接流式响应，不复制现有模拟法庭的进程内队列作为生产聊天架构。

预计涉及现有模块：

- `frontend/src/components/DigitalHuman/DigitalHumanAvatar.tsx`
- `frontend/src/components/DigitalHuman/DigitalHumanFloat.tsx`
- `frontend/src/store/digitalHumanStore.ts`
- `frontend/src/services/digitalHumanApi.ts`
- `flask_app/routers/digital_human.py`
- `flask_app/services/digital_human_service.py`

对现有 Agent 的影响：无影响；只改变 Conversation 输出和前端表现。

验收：

- 首段文本明显早于完整回复到达。
- 停止操作能终止前端流式显示，未完成回复不污染下一轮上下文。
- Avatar 状态只通过 AvatarController 驱动。
- WebM 加载失败时自动退化为现有 PNG。

对应 Agent 知识：Streaming、SSE、事件协议、取消与 UI 状态机。

#### 3.7G Voice Interaction

目标：完成第一版基础语音闭环，语音只作为同一 Conversation Orchestrator 的输入输出方式。

```text
语音输入
→ STT
→ 同一 Conversation Orchestrator
→ Streaming 文本
→ TTS
→ speaking 动画
```

第一版范围：

- 中文语音转文字。
- 识别文本进入原有会话流程。
- 回复可以朗读、停止朗读。
- 新输入能够打断旧朗读。
- 不支持语音时自动退化为文字输入。
- 可复用现有 `VoiceCourtroom.tsx` 中 Web Speech API 和 `speechSynthesis` 的实现经验，但应提取为独立轻量控制器，不引用整个模拟法庭业务组件。

当前阶段不做：

- 高精度实时口型。
- 复杂音频流。
- 专业级实时 Barge-in。
- 独立语音 Agent。
- 为语音建立第二套 Session、Memory、Router 或 Orchestrator。

对现有 Agent 的影响：无影响。

验收：

- Chrome/Edge 中文语音能够转文字并进入同一 Session。
- 流式回复能够朗读，停止和新输入可以取消旧 TTS。
- 不支持 Web Speech 的浏览器不影响文字聊天。

对应 Agent 知识：多模态输入输出适配、STT、TTS、打断与降级。

#### 3.7H Agent Engineering & Evaluation

目标：补齐会话到 Agent 全链路的最小 Trace、Guardrails、固定评测集和端到端验收，形成可持续回归的工程基线。

最小 Trace：

```text
User Input
→ Router
→ Memory
→ Context
→ Matter
→ Agent Run
→ Step
→ Tool
→ Verify
→ Decision
→ Response
```

Trace 至少保存 `trace_id`、`request_id`、`session_id`、`matter_id`、`run_id`、路由、理由代码、Memory 版本、Context 分区、Token 估算、受控动作、耗时、结果和错误码；复用现有 Agent Audit，不保存模型思维链，不默认复制完整敏感材料。

Guardrails：

- Client、Session、Matter 和 Run 归属校验。
- Router 和 Orchestrator 动作白名单。
- 审批动作必须明确确认并保持幂等。
- Assistant 内容禁止成为正式案件事实来源。
- 高风险场景停止自动推进。
- 法源不足状态不得被聊天层绕过。
- 用户文本和上传材料按数据处理，不得覆盖系统安全规则。

固定评测集控制在 20～30 个案例，建议首版 24 个，覆盖：

```text
普通咨询
欠薪
解除
经济补偿
实习
劳动关系不明确
信息不足
用户修改旧事实
长对话
法源不足
高风险
Matter 恢复
Agent 继续执行
```

指标至少包括：

```text
Router 正确率
重复追问率
Memory 正确率
事实污染率
Matter 事实准确率
Agent 完成率
法源阻断正确率
长对话 Token 增长
幻觉情况
```

首版建议门槛：

- Router 固定集正确率不低于 90%。
- Assistant 内容污染正式事实为 0。
- 高风险路由和法源阻断正确率为 100%。
- 重复追问率不高于 5%。
- Session → Matter 服务端恢复率为 100%。
- 长对话 Token 在摘要后趋于稳定。

评测分为确定性 Fake LLM 回归和真实模型抽样评测，不把模型随机性混入基础安全回归。

对现有 Agent 的影响：低风险，读取并关联现有 Audit；不修改 Runtime 执行决策。

验收：

- 24 个固定案例能够重复运行并输出结构化报告。
- 可使用一个 `trace_id` 关联 Router、Memory、Context、Matter 和现有 Agent Audit。
- 关键事实污染、高风险和法源阻断均有自动化失败用例。
- 完成数字人初始聊天、Matter 创建、工作台陪伴、Agent 继续、审批、结果总结、流式和语音降级的端到端验收。

对应 Agent 知识：Evaluation、Tracing、Guardrails、可观测性和安全回归。

#### 3.7D～3.7H 正式开发优先级

```text
P0
Memory
ContextBuilder
Router
Conversation Orchestrator
Session → Matter 服务端恢复
事实来源隔离
高风险 / 法源阻断保护

P1
Conversation Presenter
Streaming
AvatarController
Trace
Guardrails
Evaluation
基础 STT / TTS

P2
更完整 WebM 动画
更复杂语音体验
Trace 可视化界面
```

时间不足时优先缩减表现层。不得牺牲 Memory 正确性、Context 正确性、Router 单一入口、事实污染保护和 Evaluation。

#### 3.7D～3.7H 10～13 天实施安排

| 日期 | 主要目标 | 所属阶段 |
| --- | --- | --- |
| Day 1 | 基线、接口契约和数字人/工作台职责边界 | 3.7D |
| Day 2 | Raw Messages、Recent Window、Structured Memory | 3.7D |
| Day 3 | ContextBuilder、Token Budget、Rolling Summary | 3.7D |
| Day 4 | 单一 Router | 3.7D |
| Day 5 | Conversation Orchestrator | 3.7D |
| Day 6 | 两种数字人模式和 Conversation Presenter | 3.7E |
| Day 7 | Session → Matter/Run 服务端恢复与工作台协同 | 3.7E |
| Day 8 | Streaming/SSE 与 AvatarController | 3.7F |
| Day 9 | STT/TTS 基础闭环 | 3.7G |
| Day 10 | Trace 与 Guardrails | 3.7H |
| Day 11 | 20～30 个固定 Evaluation 案例 | 3.7H |
| Day 12 | 完整端到端、长对话和回归验收 | 3.7H |
| Day 13 | 缺陷修复、规划文档和验收收尾 | 3.7H |

允许在源码复杂度明确后合并 Day 1/2、Day 6/7 或 Day 12/13，将工期压缩到 10 天；不得改变 Memory → ContextBuilder → Router → Orchestrator → Workspace → Streaming → Voice → Evaluation 的依赖顺序。

阶段 3.7 验收：同一青年就业入口可以正确分流简单咨询、劳动关系判断和正式纠纷；复合劳动问题生成去重且可审计的 Plan；每个关键结论可追溯到事实、材料、证据和有效法源；数字人可从聊天引导到 Matter 和 Agent Run，但不能绕过确认、审批和人工接管。

### 阶段 4：实时 2D 数字人

目标：把成熟的 Agent 闭环接入自然语音互动。

阶段边界说明：保留阶段 4 的长期高级交互目标。3.7F/3.7G 只交付可降级的基础 Streaming、AvatarController 和浏览器 STT/TTS；阶段 4 再处理更高质量实时音频、专业级打断、口型、弱网体验和无障碍增强，避免与 3.7D～3.7H 重复建设会话基础设施。

- 流式 STT/TTS、字幕、轮次检测和打断。
- 2D listening/thinking/tool-running/approval/speaking 状态。
- 口型同步、弱网重连和文字降级。
- 老年模式、键盘操作和屏幕阅读器适配。

验收：用户能用语音完成阶段 3 主流程；插话能终止播报；网络异常不丢失案件状态。

### 阶段 5：扩展中国法律 Domain Package

目标：逐步覆盖合同、一般民事纠纷、文书和费用时效工具。

- 将现有法律咨询、合同审查、案件分析、纠纷、文书和计算 Service 逐步包装为统一工具，并按领域注册 PlanTemplate。
- 不直接让 Agent 调用大型 Router 文件中的混杂逻辑；先下沉 Service。
- 每新增一个领域必须同时增加 Domain Package、法域声明、Schema、模板、验证策略和评测。
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
   ↓
阶段3.5 生产可信化（可与下一阶段部分并行）
   ↓
阶段3.6 统一 Runtime Graph + Capability Registry
   ↓
阶段3.7A～3.7C 劳动用工深化 + 数字人最小融合
   ↓
阶段3.7D Conversation Foundation
   ↓
阶段3.7E Conversation × Workspace
   ↓
阶段3.7F Digital Human Interaction
   ↓
阶段3.7G Voice Interaction
   ↓
阶段3.7H Agent Engineering & Evaluation
   ├────────→ 阶段4 高级实时 2D 数字人
   └────────→ 阶段5 多领域 Domain Package
                      ↓
                阶段6 第二法域
                      ↓
                阶段7 跨境与多 Agent
```

阶段 4 可在阶段 3.7H 验收后与阶段 5 并行；第二法域必须建立在法域协议和来源验证稳定之后。

当前优先按 3.7D～3.7H 完成统一会话、工作台协同、基础交互和工程化评测，再决定阶段 4 的表现深度和阶段 5 的第二业务领域。比赛版本以青年就业劳动闭环为主线，其他旧平台功能只作为扩展能力展示。

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
- `agent_plan_revisions`
- `agent_plan_step_decisions`
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

阶段 3.4A～3.4E 和阶段 3.6 已落地，阶段 3.5 仍有生产可信化待办。下一步执行入口：

1. 继续完成法源复核、规则金标、定时同步告警、权限和长期运行等阶段 3.5 安全门槛。
2. 阶段3.7C代码已完成，先完成4个官方法源版本人工复核；阶段1～3.7C历史规划和实施结果继续保留。
3. 后续按 3.7D Conversation Foundation → 3.7E Conversation × Workspace → 3.7F Digital Human Interaction → 3.7G Voice Interaction → 3.7H Agent Engineering & Evaluation 实施，整体控制在10～13天。
4. 当前只完成后续规划更新，不自动启动3.7D或任何 Memory、Router、Orchestrator、Streaming、STT/TTS 实现；开始开发仍需进入独立实施任务。
5. 阶段 3.5 暂缓但必须在生产化前补齐法源复核、规则金标、定时同步告警、权限和长期运行保障。
6. 比赛主线稳定后，再按“只读合同审查 → 一般纠纷 → 文书 → 其他工具”的顺序接入新领域；新领域必须实现 `DomainPackage + DomainRuntimeAdapter + 领域评测`，不得复制 Runtime Graph。
