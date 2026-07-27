# 数字人 Agent 目录与完整流程导读

更新时间：2026-07-27  
适用范围：`flask_app/legal_agent_system/` 当前源码，共 8 个主要职责包、71 个 `.py` 文件。

这份文档解决两个问题：

1. 按路径说明每个包、每个 Python 文件负责什么。
2. 用一个“加班费劳动仲裁”案例，把数字人、聊天分流、案件工作台和 Agent Runtime 串成完整流程。

> 先记边界：数字人形象和聊天界面在前端；HTTP 接口在 `routers/digital_human_agent.py`；本目录负责真正的案件、领域能力、计划、工具、法源、验证、审批、审计和持久化。

## 调用
```text
用户 → Conversation / Triage → Matter 案件 → Facade → CapabilityRuntime 
→ CapabilityRuntimeGraph → Domain Adapter →Tool →Labor Service / Rule →Verifier →结果 / 补信息 / 审批 / 完成
```
## 一、先记住三层产品流程

```text
① 数字人展示与反馈
   frontend/src/components/DigitalHuman/DigitalHumanAvatar.tsx
                 ↓
② 初始聊天、劳动问题识别、追问和分流
   DigitalHumanChat.tsx + useLaborTriage.ts
                 ↓
③ Agent 案件工作台真正办案
   DigitalHumanMatterWorkspace.tsx
                 ↓ HTTP
   routers/digital_human_agent.py
                 ↓
   legal_agent_system/facade.py
                 ↓
   本目录中的 Runtime、领域包、工具、法源和数据库
```

当前不是把数字人、聊天和 Agent 写在一个大文件里，而是让它们通过 `session_id`、`matter_id` 和 `run_id` 串联：

| 标识 | 表示什么 | 主要作用 |
| --- | --- | --- |
| `session_id` | 一次聊天会话 | 恢复聊天，并关联当前案件上下文 |
| `matter_id` | 一个案件工作区 | 归集法域、材料、事实、证据和业务目标 |
| `run_id` | Agent 的一次执行任务 | 保存计划、步骤、工具调用、暂停、审批和最终结果 |

## 二、目录树总览

```text
legal_agent_system/
├─ facade.py                 总门面：Router 只通过它进入业务
├─ authority_cli.py          法源同步、健康检查和人工复核命令
├─ models.py                 本模块补充的数据库表模型
├─ capabilities/             “这个领域能做什么、用哪个计划”                   
├─ domains/                  “劳动领域怎样接入通用 Runtime”
│  ├─ labor/                 真实中国劳动领域
│  └─ mock/                  只用于验证 Runtime 的模拟领域
├─ runtime/                  通用 Agent 执行内核，不写具体劳动法规则
├─ tools/                    Runtime 能调用的白名单动作
├─ matters/                  案件、材料、定位事实、时间线和证据清单
├─ jurisdictions/            法域确认、官方法源同步、版本和复核
└─ labor_disputes/           劳动分流、事实、证据、规则、分析和草稿
   ├─ material_adapters/     七类劳动材料识别
   └─ labor_rules/           五类劳动实体规则
```

最短阅读顺序：

```text
facade.py
→ capabilities/contracts.py
→ domains/labor/package.py
→ domains/labor/adapter.py
→ runtime/capability_runtime.py
→ runtime/capability_graph.py
→ tools/labor_dispute_tools.py
→ labor_disputes/service.py
```

## 三、根目录每个文件

| 文件 | 主要对象 | 对应职责 |
| --- | --- | --- |
| `__init__.py` | `LegalAgentFacade`、`get_legal_agent_facade` | 对外导出包入口，Router 从这里取得 Facade。 |
| `facade.py` | `LegalAgentFacade` | 整个系统的装配和稳定门面。创建材料、法域、法源、劳动服务、工具注册表、能力注册表和 Runtime；自身不编排 Graph 步骤。 |
| `authority_cli.py` | `register_authority_commands` | 注册 `authority sync/health/pending/review` Flask CLI。普通用户 HTTP 不能写入或批准法源。 |
| `models.py` | 8 个 SQLAlchemy 模型 | 保存事实断言、计划 revision、幂等动作、事件 Outbox、法源同步批次/快照/复核、劳动分流版本。 |

`models.py` 中的表：

| 模型 | 保存内容 |
| --- | --- |
| `MatterFactAssertion` | 用户确认或材料候选形成的版本化事实断言 |
| `AgentPlan` | 不可覆盖的 Plan revision |
| `AgentRunAction` | `continue` 请求的幂等记录 |
| `AgentEventOutbox` | 可供后续监控或消息系统消费的运行事件 |
| `AuthoritySyncRun` | 一次法源同步批次 |
| `AuthoritySourceSnapshot` | 官方页面原始响应与内容哈希快照 |
| `AuthoritySourceReview` | 法律专业人员的批准或驳回记录 |
| `LaborCaseTriage` | 劳动案件分流与关系初筛版本 |

## 四、`capabilities/`：能力声明与计划生成

这个包回答：“收到某种任务后，属于哪个领域，使用哪个固定模板，允许哪些工具和步骤？”

| 文件 | 主要对象 | 对应职责 |
| --- | --- | --- |
| `capabilities/__init__.py` | 能力类型统一导出 | 让其他模块从 `legal_agent_system.capabilities` 导入公共契约。 |
| `capabilities/contracts.py` | `RoutingRule`、`PlanTemplate`、`TemplateStep`、`DomainPackage`、`PlanRevision` | 定义领域包、任务路由、模板、步骤、验证策略和本次运行计划的数据结构，并校验重复步骤、非法依赖和越权标签。 |
| `capabilities/domain_adapter.py` | `DomainRuntimeAdapter`、`ContextAssessment`、`RuntimeStep` | 定义领域接入通用 Runtime 必须实现的接口。劳动规则不能直接写入通用 Graph。 |
| `capabilities/plans.py` | `TemplatePlanBuilder` | 把已审核模板实例化为本次不可变 Plan；根据事实和争议标签启用或跳过可选步骤，计算输入指纹。 |
| `capabilities/registry.py` | `CapabilityRegistry`、`ResolvedCapability` | 成对注册 `DomainPackage + Adapter`；把 `task_type` 解析为唯一领域和模板；计划定制后再次检查是否插步、换工具或削弱审批。 |

关键区别：

- `PlanTemplate`：系统预先审核的固定办案策略。
- `PlanRevision`：某个案件、某次运行真正采用的计划快照。
- 用户补充事实导致计划变化时，新建 revision，不覆盖旧计划。

## 五、`domains/`：领域包与通用 Runtime 的接缝

### `domains/` 根包

| 文件 | 对应职责 |
| --- | --- |
| `domains/__init__.py` | 领域命名空间。新增真实领域时在这里的同级目录增加包，不能复制 Runtime Graph。 |

### `domains/labor/`：中国劳动领域

| 文件 | 主要对象 | 对应职责 |
| --- | --- | --- |
| `domains/labor/__init__.py` | 劳动包统一导出 | 导出劳动 Adapter 和领域包构建函数。 |
| `domains/labor/package.py` | `build_labor_domain_package` | 声明 `cn_labor` 领域、4 个任务模板、争议标签、步骤、工具白名单、依赖、审批和验证策略。 |
| `domains/labor/adapter.py` | `LaborDomainRuntimeAdapter` | 将劳动事实、法域、分流结果、工具参数和继续动作适配给通用 Runtime；决定缺事实、缺法域、人工接管或可以继续。 |
| `domains/labor/verifier.py` | `LaborResultVerifier` | 检查劳动关系、证据、问题规则、法源、综合分析和草稿结果是否满足领域要求。 |

当前 4 个真实劳动模板：

| `task_type` | 用途 |
| --- | --- |
| `labor_relationship_assessment` | 判断实习、兼职、毕业就业等场景是否倾向构成劳动关系 |
| `labor_consultation` | 只读劳动咨询，不生成仲裁草稿 |
| `labor_case_analysis` | 只读案件分析，可组合欠薪、试用期、解除、补偿和加班费步骤 |
| `labor_arbitration_application` | 完整仲裁闭环，最后必须审批才能生成草稿 |

### `domains/mock/`：模拟领域

| 文件 | 主要对象 | 对应职责 |
| --- | --- | --- |
| `domains/mock/__init__.py` | 模拟包统一导出 | 导出模拟领域包和 Adapter。 |
| `domains/mock/package.py` | `build_mock_domain_package` | 声明只有一个模拟摘要步骤的能力包，用于验证通用 Runtime。 |
| `domains/mock/adapter.py` | `MockDomainRuntimeAdapter` | 为模拟任务提供上下文、参数和验证适配，不代表真实法律领域。 |

## 六、`runtime/`：唯一通用 Agent 内核

这个包回答：“任务如何创建、暂停、恢复、逐步执行、验证和持久化？”它不应该包含欠薪、解除等具体业务规则。

| 文件 | 主要对象 | 对应职责 |
| --- | --- | --- |
| `runtime/__init__.py` | Runtime 公共类型导出 | 导出 `AgentState`、`AgentTool`、`ToolResult` 和 `CapabilityRuntime`。 |
| `runtime/capability_runtime.py` | `CapabilityRuntime` | 用例层。解析一次能力，创建/复用 Run，绑定领域和模板，处理补信息、确认法域、审批、重试法源等继续动作。 |
| `runtime/capability_graph.py` | `CapabilityRuntimeGraph` | 唯一 LangGraph 执行图：检查上下文、建计划、选步骤、执行、观察、验证、决策。 |
| `runtime/decision_router.py` | `DecisionRouter` | 把验证报告转换为继续、重试、补信息、重规划、拒绝、人工接管或完成。 |
| `runtime/enums.py` | `RunStatus`、`StepStatus`、`ErrorCode` | 集中定义稳定运行状态、步骤状态和错误码。 |
| `runtime/errors.py` | `AgentRuntimeError`、`RetryableToolError` | Runtime 统一异常，携带稳定错误码。 |
| `runtime/executor.py` | `PolicyToolExecutor` | 执行工具前检查输入 Schema、法域、审批和超时；不负责判断法律结果是否正确。 |
| `runtime/locks.py` | `RunExecutionLock` | 使用 PostgreSQL advisory lock 防止同一 Run 被并发执行。 |
| `runtime/persistence.py` | `AgentRepository` | 保存 Run、Plan、Step、ToolCall、审批、审计、幂等动作和快照，是跨进程恢复的权威来源。 |
| `runtime/registry.py` | `ToolRegistry` | 保存工具定义与处理函数；只能按白名单工具名调用，重复注册直接失败。 |
| `runtime/schemas.py` | `AgentState`、`AgentTool`、`ToolResult` 等 | 定义 Runtime 状态、工具声明、统一工具结果、法域上下文、材料引用和法源记录结构。 |
| `runtime/verifier.py` | `LayeredVerifier` | 先做全局结果校验，再合并领域/任务验证报告；只产出报告，不直接推进状态。 |

Graph 的固定循环：

```text
ensure_context
→ build_plan
→ select_next_step
→ execute_step
→ observe_step
→ verify_step
→ decide_step
    ├─ next_step       → 选择下一步骤
    ├─ retry_step      → 重试当前步骤
    ├─ request_context → 保存并等待用户补信息
    ├─ replan          → 保存原因，下一次生成新 revision
    ├─ require_approval→ 保存审批并暂停
    ├─ handoff/reject  → 停止自动执行
    └─ finish          → 完成
```

## 七、`tools/`：Runtime 可调用的白名单动作

工具文件只负责把领域 Service 包装成统一 `AgentTool + ToolResult`，不应复制业务公式。

| 文件 | 注册的主要工具 | 对应职责 |
| --- | --- | --- |
| `tools/__init__.py` | 所有 `register_*` | 工具注册函数统一导出。 |
| `tools/mock_case_summary.py` | `mock_case_summary` | 第一次模拟临时失败、第二次成功，用于测试重试、审批和恢复。 |
| `tools/material_tools.py` | `parse_document`、`extract_legal_facts`、`build_case_timeline`、`generate_evidence_checklist` | 将案件材料、事实定位、时间线和证据清单包装为 Runtime 工具。 |
| `tools/authority_tools.py` | `verify_legal_citation` | 只开放法源引用校验，不允许 Agent 写入或批准法源。 |
| `tools/labor_tools.py` | `calculate_labor_compensation` | 复用项目已有劳动补偿 Service，提供独立快速估算。 |
| `tools/labor_triage_tools.py` | `assess_labor_relationship` | 执行劳动关系初筛，返回依据、风险、证据和法源引用。 |
| `tools/labor_dispute_tools.py` | 证据、5类问题分析、综合分析、咨询、案件分析、仲裁草稿 | 把劳动领域 Service 包装成完整 Runtime 工具集；草稿工具声明 `requires_approval=True`。 |

`labor_dispute_tools.py` 中的重要工具：

```text
analyze_probation
analyze_wage_arrears
analyze_overtime_pay
analyze_labor_termination
analyze_economic_compensation
analyze_labor_dispute
analyze_labor_consultation
analyze_labor_case
draft_labor_arbitration_application
```

## 八、`matters/`：案件和材料

| 文件 | 主要对象 | 对应职责 |
| --- | --- | --- |
| `matters/__init__.py` | `MaterialService` 导出 | 材料包公共入口。 |
| `matters/materials.py` | `MaterialService` | 创建/读取/删除 Matter；按客户端隔离；保存文本材料并分片；提取带字符位置的事实；构建时间线和基础证据清单。 |

注意：PDF、Word、图片、音视频首先由目录外的 `services/material_extraction.py` 转成可编辑文字。用户确认整理稿后，才进入 `MaterialService.ingest_text`。

## 九、`jurisdictions/`：法域与官方法源

| 文件 | 主要对象 | 对应职责 |
| --- | --- | --- |
| `jurisdictions/__init__.py` | 法域组件统一导出 | 导出法域注册表和案件法域服务。 |
| `jurisdictions/registry.py` | `JurisdictionRegistry`、`get_jurisdiction_registry` | 注册支持法域；当前真实劳动能力只支持中国法域。 |
| `jurisdictions/service.py` | `MatterJurisdictionService` | 保存用户明确确认的国家、地区、适用日期等案件法域上下文。 |
| `jurisdictions/authorities.py` | `LegalAuthorityService` | 登记法源版本、验证法域/效力/日期/哈希、检索新鲜有效来源。 |
| `jurisdictions/authority_provider.py` | `OfficialCnLaborProvider` | 从官方白名单 HTTPS 地址抓取并解析中国劳动法条；限制域名、媒体类型和响应大小。 |
| `jurisdictions/authority_importer.py` | `TrustedAuthorityImporter` | 执行同步批次，保存原始快照；正文不变则复用，正文变化则生成待复核版本。 |
| `jurisdictions/authority_governance.py` | `AuthorityGovernanceService` | 计算法源健康、列出待复核版本、记录人工批准/驳回及审计。 |

法源安全链：

```text
官方白名单网站
→ Provider 下载和解析
→ Importer 保存原始快照与版本
→ Governance 等待人工复核
→ LegalAuthorityService 只检索 ready 且新鲜的版本
→ 工具结果携带 authority_refs
→ Verifier 再检查
```

## 十、`labor_disputes/`：劳动领域业务

### 10.1 根目录文件

| 文件 | 主要对象 | 对应职责 |
| --- | --- | --- |
| `labor_disputes/__init__.py` | 劳动组件统一导出 | 导出劳动纠纷、问题分析、材料建议和分流服务。 |
| `labor_disputes/triage_schemas.py` | `LaborTriageFacts`、问题字典 | 定义实习、兼职、学生状态、劳动管理、有偿劳动、就业目的和高风险等分流事实。 |
| `labor_disputes/triage_rules.py` | `LaborTriageDecisionEngine` | 确定性输出五类分流、关系倾向、缺失事实、问题、风险和推荐任务。 |
| `labor_disputes/triage.py` | `LaborCaseTriageService` | 合并并版本化保存分流事实、写入事实断言、恢复和执行初筛。 |
| `labor_disputes/dispute_tags.py` | `normalize_dispute_tags`、`dispute_tags_from_facts` | 把中文请求归一成稳定标签：欠薪、试用期、加班费、解除、经济补偿；未知标签失败关闭。 |
| `labor_disputes/schemas.py` | `LaborDisputeFacts`、`LaborRuleDecision` 等 | 定义完整劳动事实、证据项、规则决定及中文缺失字段描述。 |
| `labor_disputes/suggestions.py` | `LaborFactSuggestionService` | 综合材料适配器、已有定位事实和可选 LLM，生成带原文出处的候选事实；不自动确认。 |
| `labor_disputes/llm_extractor.py` | `ControlledLaborFactExtractor` | 可选 LLM 候选抽取；限制调用预算，并校验字段、原文位置和 Schema。 |
| `labor_disputes/evidence.py` | `LaborEvidenceService` | 将规则字段、确认事实、材料支持、冲突值和缺口组装成证据矩阵。 |
| `labor_disputes/issue_analysis.py` | `LaborIssueAnalysisService` | 为5类问题步骤调用对应实体规则，提供统一问题分析入口。 |
| `labor_disputes/rules.py` | `LaborRuleEngine` | 处理劳动仲裁时效等公共确定性规则。 |
| `labor_disputes/service.py` | `LaborDisputeService` | 劳动纠纷业务聚合服务：保存事实、计算缺失项、综合证据/规则/法源/期限、生成审批后的仲裁草稿。 |

### 10.2 `material_adapters/`：七类劳动材料

| 文件 | 主要对象 | 对应职责 |
| --- | --- | --- |
| `material_adapters/__init__.py` | `LaborMaterialAdapterRegistry` 导出 | 材料适配器包入口。 |
| `material_adapters/contracts.py` | `MaterialCandidate`、`LaborMaterialAdapter` | 定义材料候选的字段、值、置信度、原文、偏移和材料类型契约。 |
| `material_adapters/common.py` | 日期/金额正则及候选辅助函数 | 提供统一日期转换、原文偏移和候选构建，避免各适配器重复实现。 |
| `material_adapters/agreements.py` | `AgreementAdapter`、`OfferAdapter` | 识别实习协议、劳动合同和 Offer，提取主体、日期、工资、合同期限和试用期。 |
| `material_adapters/employment_records.py` | `TerminationNoticeAdapter`、`AttendanceAdapter`、`PayrollAdapter` | 识别解除通知、考勤和工资记录，提取解除、出勤、工资和欠付信息。 |
| `material_adapters/communications.py` | `ChatRecordAdapter` | 从聊天记录提取工资、欠薪、解除日期/原因等候选事实。 |
| `material_adapters/registry.py` | `LaborMaterialAdapterRegistry` | 根据文件名和正文关键词选择一个最匹配适配器，防止同一材料被多类重复抽取。 |

对应七类材料：

```text
实习协议 / 劳动合同 / Offer / 解除通知 / 考勤 / 工资记录 / 聊天记录
```

### 10.3 `labor_rules/`：五类实体规则

| 文件 | 主要对象 | 对应职责 |
| --- | --- | --- |
| `labor_rules/__init__.py` | 五类规则统一导出 | 供问题分析 Service 注册和调用。 |
| `labor_rules/base.py` | `decision` | 统一生成 `LaborRuleDecision`；缺事实返回 `information_required`，缺法源返回 `authority_required`，且始终标记人工复核、非最终法律结论。 |
| `labor_rules/wage.py` | `WageArrearsRule` | 计算或整理欠薪金额、欠薪期间及假设。 |
| `labor_rules/probation.py` | `ProbationRule` | 核对试用期期限、重复约定、试用期工资下限和解除复核要求。 |
| `labor_rules/termination.py` | `TerminationRule` | 识别解除审查路径，保留通知、工会程序、举证和特殊保护人工复核。 |
| `labor_rules/compensation.py` | `CompensationRule` | 按工作年限、工资基数、高工资封顶和补偿/赔偿类型估算。 |
| `labor_rules/overtime.py` | `OvertimePayRule` | 标准工时制下按工作日150%、休息日200%、法定节假日300%估算；特殊工时制失败关闭。 |

## 十一、完整案例：加班费劳动仲裁

### 11.1 用户输入

用户在数字人聊天框输入：

> 我已经毕业，在北京一家公司工作，公司安排我工作日加班10小时、休息日8小时、法定节假日4小时，月工资8700元，只支付了500元加班费，我想申请劳动仲裁。

### 11.2 数字人聊天和初筛

```text
DigitalHumanChat.handleSubmit
├─ digitalHumanStore.sendMessage
│  └─ POST /api/digital-human/chat
│     └─ 普通问答、情绪和导航回复
└─ isLaborQuestion = true
   └─ useLaborTriage.start
```

`useLaborTriage.start`：

1. 调用 `POST /api/digital-human/agent/matters` 创建 Matter。
2. 从原问题推断初始劳动事实和“加班费”请求。
3. 调用 `POST .../labor/triage`。
4. Router 进入 `LegalAgentFacade.update_labor_case_triage`。
5. `LaborCaseTriageService` 保存事实。
6. `LaborTriageDecisionEngine` 判断是简单咨询、关系判断、正式纠纷、非劳动问题还是高风险人工处理。
7. 缺初筛事实时，聊天区的 `LaborTriageCard` 继续追问；满足条件后启动推荐任务。

### 11.3 进入案件工作台

用户点击“案件工作台”，依次完成：

```text
创建/恢复 Matter
→ 确认中国法域和适用日期
→ 上传考勤、工资记录、聊天记录
→ 查看并修改识别整理稿
→ 用户确认后写入 Matter
→ 采用或编辑材料候选事实
```

对应后端：

| 动作 | 入口 | 本目录执行 |
| --- | --- | --- |
| 创建案件 | `POST /matters` | `Facade.create_matter → MaterialService.create_matter` |
| 确认法域 | `POST /matters/{id}/jurisdiction` | `MatterJurisdictionService.confirm` |
| 文件转文字 | `POST /materials/organize` | 目录外 `material_extraction.py`，此时不入库 |
| 确认材料 | `POST /materials` | `MaterialService.ingest_text`，保存材料和分片 |
| 读取候选 | `GET /labor-dispute/suggestions` | `LaborFactSuggestionService.suggest → material_adapters/` |

### 11.4 启动 Agent Run

工作台提交完整事实，调用：

```text
POST /api/digital-human/agent/matters/{matter_id}/labor-dispute/run
task_type = labor_arbitration_application
```

真实调用链：

```text
routers/digital_human_agent.py
→ get_legal_agent_facade()
→ LegalAgentFacade.start_task
→ CapabilityRuntime.start_task
→ CapabilityRegistry.resolve("labor_arbitration_application")
→ 得到 cn_labor + labor_arbitration_application 模板
→ LaborDomainRuntimeAdapter.prepare_start
→ AgentRepository.find_or_create_active_run
→ 绑定 domain/template/version
→ CapabilityRuntimeGraph.invoke
```

### 11.5 本案生成的计划

固定模板包含多个可选步骤。本案只有“加班费”标签，因此生成的 Plan revision 大致是：

| 顺序 | 步骤 | 状态 |
| --- | --- | --- |
| 1 | 核对材料与证据缺口 | 执行 |
| 2 | 分析试用期 | `skipped` |
| 3 | 分析欠薪 | `skipped` |
| 4 | 核算加班费 | 执行 |
| 5 | 分析解除 | `skipped` |
| 6 | 估算经济补偿/赔偿 | `skipped` |
| 7 | 统一计算期限并验证法律来源 | 执行 |
| 8 | 经审批生成劳动仲裁申请书草稿 | 等待审批后执行 |

每个跳过步骤仍保留 `skip_reason`，便于审计。

### 11.6 单个步骤怎样执行

以“核算加班费”为例：

```text
CapabilityRuntimeGraph._select_next_step
→ ToolRegistry.get("analyze_overtime_pay")
→ LaborDomainRuntimeAdapter.tool_arguments
→ PolicyToolExecutor.execute
→ tools/labor_dispute_tools.py 的 overtime handler
→ LaborIssueAnalysisService.overtime_pay
→ LaborEvidenceService.build
→ OvertimePayRule.evaluate
→ 返回 LaborRuleDecision
→ AgentRepository.save_tool_call
→ Graph.observe_step
→ LayeredVerifier.verify
→ LaborResultVerifier
→ DecisionRouter.decide
```

输入：

```text
月工资                 8700 元
工作日加班             10 小时
休息日加班              8 小时
法定节假日加班          4 小时
已支付加班费           500 元
工时制度               标准工时制
```

规则结果：

```text
小时工资基数 = 8700 ÷ 21.75 ÷ 8 = 50 元
工作日加班费 = 50 × 10 × 150% = 750 元
休息日加班费 = 50 × 8 × 200% = 800 元
法定节假日加班费 = 50 × 4 × 300% = 600 元
应付合计 = 2150 元
预计待付 = 2150 - 500 = 1650 元
```

结果同时包含：

- 采用的事实值；
- `fact_refs` 和 `evidence_refs`；
- 《劳动法》第四十四条等 `authority_refs`；
- 计算过程和假设；
- 风险警告；
- `manual_review_required=true`；
- `legal_conclusion=false`。

### 11.7 三种关键暂停

#### 缺事实

```text
OvertimePayRule 发现缺少工时制度或加班小时
→ ToolResult.error_code = INFORMATION_REQUIRED
→ Verifier 给出 request_context
→ RunStatus = awaiting_information
→ 前端展示中文问题
→ 用户提交 provide_information
→ 新建 Plan revision 后续跑
```

#### 缺有效法源

```text
LegalAuthorityService 找不到 ready 且新鲜的法源
→ AUTHORITY_REQUIRED
→ RunStatus = blocked_authority
→ 不生成确定性结论或草稿
→ 用户只能重试法源或转人工复核
```

#### 等待用户审批

```text
前序分析全部通过
→ 草稿步骤 requires_approval = true
→ AgentRepository.create_approval
→ RunStatus = awaiting_approval
→ 用户明确 approve
→ CapabilityRuntime.continue_task
→ draft_labor_arbitration_application
→ LaborDisputeService.create_draft
→ 保存 AgentArtifact
→ RunStatus = completed
```

### 11.8 最终前端看到什么

`AgentRepository.snapshot` 返回：

- 当前中文状态；
- 每个计划步骤及状态；
- 缺失事实和待回答问题；
- 证据、期限和五类规则结果；
- 已验证法源；
- 审批提示；
- 仲裁申请书草稿及交付物 ID。

工作台将其展示为规则卡片、法源引用、审批按钮和草稿预览。导出的 Word/PDF 仍标记为待人工复核草稿，不代表已经提交仲裁机构。

## 十二、遇到问题先找哪个文件

| 你想查的问题 | 先看 |
| --- | --- |
| HTTP 请求为何报错 | `routers/digital_human_agent.py` |
| 系统怎样组装 | `facade.py` |
| 某个任务用了哪个模板 | `domains/labor/package.py` |
| 为什么暂停补信息/法域 | `domains/labor/adapter.py` |
| Graph 为什么走到某状态 | `runtime/capability_graph.py` |
| Run/Step 数据为什么不一致 | `runtime/persistence.py` |
| 工具为什么不能执行 | `runtime/executor.py`、`runtime/registry.py` |
| 验证为什么失败 | `runtime/verifier.py`、`domains/labor/verifier.py` |
| 劳动分流为什么是这个结果 | `labor_disputes/triage_rules.py` |
| 材料为什么没有识别字段 | `labor_disputes/material_adapters/` |
| 欠薪/加班费计算为什么这样 | `labor_disputes/labor_rules/` |
| 法源为什么不可用 | `jurisdictions/authority_governance.py`、`authorities.py` |
| 草稿为什么没有生成 | `labor_disputes/service.py`、审批状态和法源状态 |

## 十三、必须保持的架构边界

1. 新领域不得复制 `CapabilityRuntimeGraph`。
2. Router 只做 HTTP 参数和错误映射，不直接编排业务。
3. Facade 只装配和转发，不实现具体劳动规则。
4. 具体法律事实、计划定制和领域验证放在 `domains/<领域>/`。
5. 业务动作放 `tools/` 或领域 Service。
6. 工具只能从 `ToolRegistry` 白名单获取。
7. 法源不足、关键事实不足、法域冲突必须失败关闭。
8. 高风险草稿必须显式审批。
9. 用户补充事实导致计划变化时创建新 revision，不覆盖旧计划。
10. 所有法律规则输出都必须保留事实、证据、法源、假设、警告和人工复核边界。
