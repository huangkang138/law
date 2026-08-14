# YYS-Law Agent Bootstrap

用户当前明确指令优先。源码事实高于所有文档。

1. 先读 `AI_WORKFLOW/WORKFLOW.md`、`AI_WORKFLOW/CURRENT_TASK.md`，并按自然语言自动路由到 `AI_WORKFLOW/MODES.md`。
   - 功能实现、缺陷修复、实现返工：执行 `AI_WORKFLOW/LAW-DEV.md`。
   - 阶段验收、独立 Review：执行 `AI_WORKFLOW/LAW-REVIEW.md`，默认只读。
   - 验收导读、完整效果说明：先执行 `LAW-REVIEW.md`，再按 `MODES.md` 的 `ACCEPTANCE_GUIDE` 一次讲完，保持只读。
2. 涉及代码修改时读 `AI_WORKFLOW/CODE_RULES.md`；检查 Git 状态后再读直接相关源码。
3. 需要整体现状时读 `newModify/latest-project-analysis.md`；需要历史时按关键词查询 `newModify/modification-log.md`；需要长期设计时按需读 `raw/`。不默认全文读取历史资料或 `raw/archive/`。
4. 每次修改后按 `WORKFLOW.md` 更新修改记录；影响项目关键事实时更新最新项目分析。

根目录 `CLAUDE.md` 是 Claude Code 自动发现入口，规则正文同样在 `AI_WORKFLOW/`。不读取、输出或写入 `.env`、密码或 API Key；不得覆盖用户未提交工作。
