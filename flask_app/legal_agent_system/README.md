# `legal_agent_system` 文件与调用说明

本文只回答三件事：每个包做什么、每个文件做什么、函数怎样调用。

## 1. 包对应什么

| 包/文件 | 对应职责 | 谁调用它 |
|---|---|---|
| `facade.py` | 系统总入口，组装并转发各能力 | `routers/digital_human_agent.py` |
| `capabilities/` | 能力契约、任务路由、计划模板 | `facade.py`、通用 Runtime |
| `domains/` | 具体法律领域的能力声明 | `CapabilityRegistry` |
| `runtime/` | Run 状态、计划执行、工具调用、验证、决策、持久化 | `facade.py` |
| `tools/` | 可被 Runtime 执行的最小动作 | `ToolRegistry`、`PolicyToolExecutor` |
| `matters/` | 案件、材料、事实、时间线、证据清单 | Facade、Runtime、Tools |
| `jurisdictions/` | 法域确认、官方法源同步与校验 | Facade、Runtime、Tools |
| `labor_disputes/` | 劳动事实、规则、分析、建议、草稿 | 劳动工具、通用 Runtime |
| `models.py` | 本模块新增的数据库模型 | `runtime/persistence.py`、法源服务 |

![包关系图](./diagrams/legal-agent-packages.svg)

图源：[legal-agent-packages.mmd](./diagrams/legal-agent-packages.mmd)

## 2. 每个文件对应什么

### 根目录

| 文件 | 主要入口 | 对应内容 |
|---|---|---|
| `__init__.py` | `get_legal_agent_facade` | 包导出入口。 |
| `facade.py` | `LegalAgentFacade` | Router 的唯一业务门面；组装工具、能力包、Runtime 和业务服务。 |
| `models.py` | `AgentPlan` 等 | 计划 revision、事实断言、操作幂等、Outbox、法源同步记录。 |
| `README.md` | - | 当前文件索引。 |
| `analyse-agents.md` | - | 历史演进和详细架构分析，不作为日常文件索引。 |

### `capabilities/`

| 文件 | 主要入口 | 对应内容 |
|---|---|---|
| `__init__.py` | - | 统一导出能力契约。 |
| `contracts.py` | `DomainPackage`、`PlanTemplate`、`TemplateStep` | 领域包、路由、模板、步骤、验证策略的数据结构。 |
| `registry.py` | `CapabilityRegistry.register/resolve` | 注册领域包；把 `task_type` 解析为领域包和模板。 |
| `plans.py` | `TemplatePlanBuilder.build` | 将模板实例化为本次 Run 的 Plan revision。 |

### `domains/`

| 文件 | 主要入口 | 对应内容 |
|---|---|---|
| `__init__.py` | - | 领域包命名空间。 |
| `labor/__init__.py` | `build_labor_domain_package` | 导出劳动领域包。 |
| `labor/package.py` | `build_labor_domain_package` | 声明劳动仲裁、劳动咨询、案件分析三种模板及工具白名单。 |

### `runtime/`

| 文件 | 主要入口 | 对应内容 |
|---|---|---|
| `__init__.py` | - | Runtime 公共类型导出。 |
| `capability_runtime.py` | `start`、`continue_run` | 通用任务用例层；创建/恢复 Run，处理用户继续动作。 |
| `capability_graph.py` | `CapabilityRuntimeGraph.invoke` | 当前主执行图；上下文、路由、计划、执行、观察、验证、决策。 |
| `registry.py` | `ToolRegistry.register/get` | 工具名称到工具定义/处理函数的注册表。 |
| `executor.py` | `PolicyToolExecutor.execute` | 检查 Schema、法域、审批、超时、重试后执行工具。 |
| `verifier.py` | `LayeredVerifier.verify` | Global/Domain/Task 分层验证，只返回验证报告。 |
| `decision_router.py` | `DecisionRouter.decide` | 将验证报告转换为下一步、重试、补信息、审批、移交或结束。 |
| `persistence.py` | `AgentRepository` | 保存 Run、Step、Plan、工具调用、审批、审计、幂等和 Outbox。 |
| `schemas.py` | `AgentState`、`AgentTool`、`ToolResult` | Runtime 的输入、状态和工具结果契约。 |
| `enums.py` | `RunStatus`、`StepStatus`、`ErrorCode` | 稳定状态和错误码。 |
| `locks.py` | `RunExecutionLock.acquire` | 防止同一 Run 并发执行。 |
| `errors.py` | `AgentRuntimeError` | Runtime 统一异常。 |
| `graph.py` | `AgentGraph` | 阶段 1 模拟摘要 Graph，兼容保留。 |
| `runtime.py` | `AgentRuntime` | 阶段 1 模拟摘要 Runtime，兼容保留。 |
| `labor_graph.py` | `LaborDisputeGraph` | 旧劳动专用 Graph，不是当前入口。 |
| `labor_runtime.py` | `LaborDisputeRuntime` | 旧劳动专用 Runtime，不再由 Facade 实例化。 |
| `planner.py` | `LaborPlanBuilder` | 旧劳动 Planner，仅保留兼容。 |

### `tools/`

| 文件 | 主要入口 | 对应内容 |
|---|---|---|
| `__init__.py` | - | 工具统一导出。 |
| `material_tools.py` | `register_material_tools` | 材料解析、事实提取、时间线、证据清单工具。 |
| `authority_tools.py` | `register_authority_verification_tools` | 法源引用校验工具。 |
| `labor_tools.py` | `register_labor_tools` | 劳动补偿金额计算工具。 |
| `labor_dispute_tools.py` | `register_labor_dispute_tools` | 劳动分析、只读咨询、案件分析、仲裁草稿工具。 |
| `mock_case_summary.py` | `register_mock_tools` | 阶段 1 模拟摘要工具。 |

### `matters/`

| 文件 | 主要入口 | 对应内容 |
|---|---|---|
| `__init__.py` | `MaterialService` | 材料服务导出。 |
| `materials.py` | `MaterialService` | Matter 增删查、材料分片、事实定位、时间线、证据清单、客户端隔离。 |

### `jurisdictions/`

| 文件 | 主要入口 | 对应内容 |
|---|---|---|
| `__init__.py` | `JurisdictionRegistry`、`MatterJurisdictionService` | 法域组件导出。 |
| `registry.py` | `get_jurisdiction_registry` | 注册和读取法域包；当前包含中国法域。 |
| `service.py` | `MatterJurisdictionService.confirm` | 保存用户明确确认的案件法域。 |
| `authorities.py` | `LegalAuthorityService` | 法源登记、版本、有效性、新鲜度和检索。 |
| `authority_provider.py` | `OfficialCnLaborProvider.fetch` | 从官方白名单来源下载并解析劳动法条。 |
| `authority_importer.py` | `TrustedAuthorityImporter.import_all` | 同步批次、原始快照、版本变化和失败审计。 |

### `labor_disputes/`

| 文件 | 主要入口 | 对应内容 |
|---|---|---|
| `__init__.py` | - | 劳动争议组件导出。 |
| `schemas.py` | `LaborDisputeFacts` | 劳动争议事实字段 Schema。 |
| `service.py` | `LaborDisputeService` | 确认事实、缺失项、分析结果和仲裁草稿。 |
| `suggestions.py` | `LaborFactSuggestionService.suggest` | 从材料提取带原文出处的候选事实。 |
| `llm_extractor.py` | `ControlledLaborFactExtractor.extract` | 可选 LLM 候选提取，校验 Schema、原文位置和预算。 |
| `rules.py` | `LaborRuleEngine.limitation` | 劳动仲裁期限等确定性规则。 |

## 3. 函数调用流程

### 3.1 入口函数调用

![入口函数调用图](./diagrams/legal-agent-call-flow.svg)

图源：[legal-agent-call-flow.mmd](./diagrams/legal-agent-call-flow.mmd)

### 3.2 Runtime 单步循环

![Runtime 单步循环图](./diagrams/legal-agent-runtime-loop.svg)

图源：[legal-agent-runtime-loop.mmd](./diagrams/legal-agent-runtime-loop.mmd)

### 3.3 启动一个劳动任务

```text
Router.start_labor_dispute_run
-> LegalAgentFacade.start_labor_dispute_run
-> CapabilityRuntime.start
-> CapabilityRegistry.resolve
-> AgentRepository.find_or_create_active_run
-> CapabilityRuntimeGraph.invoke
-> _ensure_context
-> _route_task
-> _build_plan
-> _select_next_step
-> _execute_step
-> _observe_step
-> _verify_step
-> _decide_step
-> AgentRepository.snapshot
```

### 3.4 用户补信息、确认法域、审批或重试

```text
Router.continue_labor_dispute_run
-> LegalAgentFacade.continue_labor_dispute_run
-> CapabilityRuntime.continue_run
-> _continue_run_locked
-> AgentRepository.load_state / begin_action
-> 根据 action 更新事实、确认法域、记录审批或同步法源
-> CapabilityRuntimeGraph.invoke
-> AgentRepository.snapshot / finish_action
```

### 3.5 其他常用调用

| 需求 | 调用链 |
|---|---|
| 创建案件 | `Facade.create_matter -> MaterialService.create_matter` |
| 上传材料 | `Facade.add_material -> MaterialService.ingest_text` |
| 提取事实 | `Facade.extract_material_facts -> MaterialService.extract_facts` |
| 确认法域 | `Facade.confirm_jurisdiction -> MatterJurisdictionService.confirm` |
| 同步官方法源 | `Facade.import_official_labor_authorities -> TrustedAuthorityImporter.import_all -> OfficialCnLaborProvider.fetch` |
| 事实建议 | `Facade.suggest_labor_dispute_facts -> LaborFactSuggestionService.suggest` |

## 4. 新代码放哪里

- 新法律领域：`domains/<领域>/package.py`。
- 新任务模板：对应领域的 `package.py`。
- 新工具：`tools/`，并在 `facade.py` 和领域包中注册。
- 新运行控制：仅放 `runtime/`，不能写具体劳动/合同业务。
- 新业务规则：对应业务服务包，不写进 `capability_graph.py`。
- 新数据库字段：模型加 Alembic migration。

详细背景见 [analyse-agents.md](./analyse-agents.md)。
