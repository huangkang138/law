# 下一步

## 已完成

- 阶段 3.7A～3.7E 已完成并收尾（3.7E 已提交 `e00e578`，技术验收 PASS）。
- 阶段 3.7F 全部完成并收尾（状态 `COMPLETED`，2026-08-15）：
  - 第一部分（SSE 增量呈现）：用户验收通过。
  - 第二部分（服务端取消）：取消双通道、LLM 流中断、取消状态机与幂等重试、`POST /chat/cancel`、前端停止按钮通知服务端；返修完成窗口竞态（complete_request 白名单）与停止提示即时显示；取消专项 26/26，全量 79/79。

## 当前

- 无进行中的开发任务；工作区含 3.7F 未提交改动（由用户自行决定提交时机，本轮不自动提交）。

## 下一步（按依赖顺序，不自动启动）

- 3.7G Voice Interaction：浏览器 STT/TTS 基础语音闭环，语音只作为同一 Conversation Orchestrator 的输入输出方式；可复用 `VoiceCourtroom.tsx` 的 Web Speech 经验（提取独立控制器）；不做高精度口型/复杂音频/独立语音 Agent；不支持语音自动退化文字。
- 3.7H Agent Engineering & Evaluation：会话到 Agent 全链路最小 Trace（trace_id 关联 Router/Memory/Context/Matter/Agent Audit）、Guardrails 白名单与归属校验、20～30 个固定评测案例（建议首版 24 个）与结构化报告；复用 `flask_app/evals/labor_disputes/`。
- 语音、口型与数字人动画的高阶形态归属阶段 4；3.5 生产可信化、第二法律领域继续暂缓。
- 正式环境仍须重新同步 3.7C 法源，并由有权限的法律专业人员完成真实复核。

## 暂缓

- 阶段 3.5：身份权限、告警、加密、长期运行保障（含匿名身份 Cookie 续期）。
- 第二真实法律领域、基础语音与复杂数字人动画。
