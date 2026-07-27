# 代码硬约束

## 通用

- 保留用户未提交改动；只改明确范围，禁止顺手大重构。
- 高耦合文件只作局部修改；变更前后保持公开契约兼容。
- 前后端联动先后端、再前端；同步契约并执行对应验证。
- 不读取、输出或写入 `.env`、密码、API Key；不放松法律法源、法域、审批和人工复核边界。

## 前端

- Next.js/React/TypeScript 严格类型；保持 Zustand `store → component` 状态流。新增持久化字段更新 `partialize`。
- 所有后端调用经 `frontend/src/services/digitalHumanApi.ts` 的 `request()`；组件禁止直接 `fetch`。
- Props、Store 和 API 类型改动必须同步所有调用方及后端契约。
- `DigitalHumanFloat.tsx` 的 styled-jsx：可追加 class；已有 class 只改属性，不删除或重命名；迁移样式方案需用户同意。
- 不擅自修改全局布局、全局样式、核心构建配置或引入新状态/CSS/UI 框架。
- 前端改动后必须 `cd frontend && npx tsc --noEmit`；类型通过不等于视觉验收。

## 后端与 Runtime

- Runtime 枚举不删除/重命名；`AgentState` 字段不删除，新增字段有默认值。
- `persistence.snapshot()` 变更同步前端 `DigitalHumanAgentRun`；Facade 公开方法不改参数顺序、不删除参数，新增参数必须默认值。
- Runtime 保持与 Domain 解耦；不得复制 Runtime Graph 或让 Domain 绕过审批、预算、验证。
- 新表/列必须 Alembic migration；不直接改列类型或删列；生产不使用 `AUTO_CREATE_DB_TABLES=True`。
- 可信来源仅官方域名；无来源或未验证来源必须失败关闭，不能内置法条降级或放松 `LegalAuthorityService.verify()`。

## 验证

按风险执行语法、类型、构建、接口、测试或人工视觉验证；失败必须修复或明确说明。任何代码、配置、文档或结构改动均追加 `newModify/modification-log.md`。
