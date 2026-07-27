# 开发者记忆卡

## 阶段：劳动入口编排与任务运行（3.7A / 3.7A.1）

- 一句话功能：数字人聊天识别劳动问题后，创建案件并以分流结果决定是否启动受控劳动 Agent Run。
- 代码地图：入口 `DigitalHumanChat` / `useLaborTriage.start()`；核心 `useLaborTriage` + Facade；出口 `LaborTriageSnapshot` 与 Agent Run/Workspace 状态；出问题优先找 `useLaborTriage.ts`、`digitalHumanStore.ts`、`digital_human_agent.py`。
- 核心文件：`useLaborTriage.ts`、`digitalHumanStore.ts`、`DigitalHumanChat.tsx`、`digital_human_agent.py`、`facade.py`。
- 主调用链：Chat → `useLaborTriage` → Matter/Triage API → 推荐 `task_type` → Facade → Runtime Graph → Workspace。
- 关键规则：仅后端确认的推荐任务可启动；缺失事实、高风险、非劳动均阻断；保持 Store → Chat → Workspace 状态流。
- 风险：关键词和事实提取有限；每会话仅当前 Matter/Run 映射；尚无真实人工服务通道。
- 代码重新定位入口：先读 `flask_app/legal_agent_system/实际Agent架构与运行流程.md`，再从 `useLaborTriage.ts` 的 `startRuntime()`、`facade.py` 的 `start_task()` 与 `runtime/capability_graph.py` 的执行节点进入。

## 已完成接力点：阶段 3.7B

- 状态：组合式 Plan、解除日期/原因材料链路和步骤状态文案均已完成；49 项完整数字人 Agent 回归、Python 编译、前端类型检查和用户验收通过。
- 一句话功能：按交付目的选择劳动主模板，以稳定争议标签启用欠薪、解除、补偿白名单步骤；一个复合案件只使用一个 Run 和不可变 Plan revisions。
- 代码地图：入口 `Facade.start_task()`；核心 `dispute_tags.py`、`TemplatePlanBuilder` 与 Registry；出口带标签和触发原因的 Plan revision；出问题优先找 `dispute_tags.py`、`plans.py`、`package.py`。
- 核心文件：`dispute_tags.py`、`issue_analysis.py`、`package.py`、`plans.py`、`registry.py`。
- 主链：劳动事实 → 标签归一化 → Plan 启用/跳过步骤 → 白名单复核 → 固定 Graph 执行 → 保存 revision。
- 必须理解：不复制 Graph；未知标签和任何插步/换工具/改依赖/弱化审批均失败关闭；revision 不可原地覆盖。
- 风险：三个问题步骤当前是初步结构化分析，经济补偿沿用既有估算公式；实体规则深化属于 3.7C。
- 重新定位入口：`AI_WORKFLOW/CURRENT_TASK.md` → `domains/labor/package.py` → `capabilities/plans.py` → `tests/test_digital_human_stage37b_composite_plan.py`。

## 当前验收接力点：阶段 3.7C

- 状态：`READY_FOR_ACCEPTANCE`；专项5/5、完整数字人 Agent 回归54/54和Python编译通过；生产法源4/4为 `review_required`，健康状态 `unavailable`。
- 一句话功能：七类材料经领域适配器形成带原文位置的事实候选，规则通过证据矩阵和有效法源输出统一、可追溯、需人工复核的劳动判断。
- 核心实现：`material_adapters/`、`evidence.py`、`labor_rules/`、`LaborRuleDecision`、`probation`可选步骤，以及五类25条旗舰评测。
- 不变边界：唯一 Runtime Graph；劳动规则留在 `cn_labor`；事实或法源不足失败关闭；结果必须保留假设、出处和人工复核要求。
- 下一动作：有权限复核人审核4个官方法源版本，健康状态达到 `ready` 后完成验收；不自动进入3.7D。
- 重新定位入口：`material_adapters/registry.py` → `evidence.py` → `labor_rules/` → `service.evaluate_rule()` → `domains/labor/verifier.py` → `test_digital_human_stage37c_labor_rules.py`。
