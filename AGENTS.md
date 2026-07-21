# YYS-Law 仓库协作入口

本文件是仓库唯一 AI Agent 入口；用户当前明确指令高于 `CURRENT_TASK` 和其他协作状态。

## 协作导航

| 目的 | 权威位置 |
| --- | --- |
| 安全修改代码 | `CLAUDE.md` |
| 当前任务、状态流与 Mode | `AI_WORKFLOW/` |
| 当前完整项目事实 | `newModify/latest-project-analysis.md` |
| 完整修改历史 | `newModify/modification-log.md` |
| 长期规划和有效架构资料 | `raw/` |
| 被替代的历史资料 | `raw/archive/`（默认不读取） |

## 进入任务

1. 读取本文件、`CLAUDE.md`、`AI_WORKFLOW/CURRENT_TASK.md` 和对应 Mode。
2. 检查 Git 状态，核对用户目标与 `CURRENT_TASK`；不一致时标记 `CURRENT_TASK_MISMATCH`，优先服从用户目标，并按 `AI_WORKFLOW/README.md` 执行 Promote 或交接。
3. 再读取与任务直接相关的源码。

条件读取：跨模块、架构或需要整体状态时读取 `latest-project-analysis.md`；涉及长期方向时读取相关 `raw/` 文档；需要追溯历史或已有相关未提交改动时，按关键词检索 `modification-log.md`。不默认全文读取 `raw/` 或历史日志。

## 修改前检查

- 明确允许修改范围，保留工作树既有用户改动。
- 不读取、输出或写入 `.env`、密码、API Key 等敏感信息。
- 从只读分析转为代码修改时，重新检查 Git 状态和必要上下文。

## 修改后检查

- 执行与风险相称的语法、类型、构建、接口或视觉验证。
- 每次代码、配置、文档或结构修改后，追加 `newModify/modification-log.md`。
- 影响结构、启动、接口、数据模型、关键配置或业务流程时，更新 `newModify/latest-project-analysis.md`。
- 最终确认未修改任务范围外的用户代码。

代码任务默认交付“开发者记忆卡”；完整历史留在修改日志，除非用户要求否则不默认逐文件审计。
