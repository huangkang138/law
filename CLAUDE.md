# Law Claude Code Bootstrap

用户当前明确指令优先。执行任务时遵循：

1. `AI_WORKFLOW/WORKFLOW.md`：任务生命周期、自动路由、验收与返工。
2. `AI_WORKFLOW/CODE_RULES.md`：代码修改硬约束与验证。
3. `AI_WORKFLOW/CURRENT_TASK.md`：唯一当前任务状态。

入口安全边界：不读取、输出或写入 `.env`、密码、API Key；不删除或覆盖用户未提交工作；不得放松法律法源的失败关闭、可信来源和审批边界。
