# Matter-AgentRun

## 一级调用链

create_matter → Workspace 指针 → start_task → CapabilityRuntimeGraph（Plan → Step → Tool → Verifier → Decision）→ Persistence → 快照恢复

## 一句话目的

案件工作区（Matter）与受控 Agent 任务（Run）的完整生命周期：创建、暂停、恢复、完成、取消。Matter 是数据归属边界，Run 是受控执行单元（Plan → Step → Tool → Verifier → Decision → Persistence），两者都按 client_id 隔离，都支持幂等恢复。

## 调用链

```text
Matter 生命周期：
创建（chat 动作 / 工作台 Idempotency-Key → 稳定 matter_id）
→ facade.create_matter → ConversationWorkspaceState.select_matter（版本 CAS、Session 行锁）
→ 删除：workspace.delete_matter（同一事务：回退指针 → db.delete，衍生数据由 FK ondelete=CASCADE 清理）
→ 恢复：workspace.get_context（指针 → Matter → Triage → 最新 Run，行锁一致性快照）

AgentRun 生命周期：
facade.start_task → CapabilityRuntimeGraph（唯一通用 Runtime）
    Run → Plan（revision 保留）→ Step → ToolCall（ToolRegistry 白名单）→ Verifier → Decision
→ 暂停态：awaiting_jurisdiction / awaiting_information / awaiting_approval /
          blocked_authority / human_handoff
→ 恢复：continue_task（结构化动作）/ resume_run（审批布尔决定，必须用户明确给出）
→ 取消：cancel_run（状态标记型：Run/当前 Step 置 CANCELLED，不中断线程）
→ 快照：persistence.snapshot → DigitalHumanAgentRun（前端权威恢复来源）

法域与材料（Run 的前置）：
confirm_jurisdiction（仅用户确认）→ add_material / organize → extract_material_facts（候选）
→ 用户采用 → MatterFactAssertion(confirmed_by_user=True) → 才进入正式事实
```

## 关键状态

| 状态 | 谁写 | 谁读 |
| --- | --- | --- |
| Matter（status/session_id/client_id） | create/delete_matter | 指针解析、Run 归属 |
| AgentRun（status/current_step_id/plan_id/plan_revision/state_json/error_code/budget 系列） | Runtime persistence | snapshot / 恢复 / 前端 |
| AgentStep（status/observation/verification/decision） | 执行器 | 快照 |
| MatterFactAssertion（confirmed_by_user 标志） | 用户采用动作 | context_builder（对话上下文只读确认事实） |
| MatterJurisdiction（confirmed_by_user） | confirm_jurisdiction | 真实法律工具执行前置检查 |

## 判断点（已查过）

- **Runtime 边界**：不复制 CapabilityRuntimeGraph；Domain 不绕过审批、预算、验证；工具只经 ToolRegistry 白名单。
- **幂等恢复**：Run 按 run_id 恢复（恢复前查存在性与状态），重复启动不重复创建。
- **审批只能用户做出**：approved 必须是显式布尔决定，前端不能替用户默认确认；审批协议不绕过。
- **法源失败关闭**：blocked_authority 时停止生成结论；`authority_refs` 必须经有效性验证；不内置法条降级。
- **候选 ≠ 确认**：材料候选事实需用户采用；对话记忆与正式事实冲突时排除候选并引导工作台。
- **Plan revision 不被覆盖**；RunStatus/StepStatus 与实际执行结果一致；不确定结果不包装成确定法律结论。
- **取消是状态标记**（不中断线程）：与"服务端取消"模块（对话请求级）是两层不同机制，勿混淆。

## 保护它的测试

- `tests/test_digital_human_stage31_runtime.py`、`stage32_safety.py`、`stage34_completion.py`（Run 生命周期与安全）
- `tests/test_digital_human_stage35_authority_governance.py`、`stage35_authority_provider.py`（法源治理）
- `tests/test_digital_human_stage36_capability_runtime.py`（Graph/Registry/Executor）
- `tests/test_digital_human_stage37b_composite_plan.py`、`stage37c_labor_rules.py`（劳动组合 Plan 与实体规则）
