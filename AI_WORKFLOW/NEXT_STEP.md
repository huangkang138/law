# 下一步

## 已完成

- 阶段 3.7A～3.7E 已完成并收尾（3.7E 已提交 `e00e578`，技术验收 PASS）。
- 阶段 3.7F 全部完成并收尾（状态 `COMPLETED`，2026-08-15，已提交 `1b2f6ac`）：
  - 第一部分（SSE 增量呈现）：用户验收通过。
  - 第二部分（服务端取消）：取消双通道、LLM 流中断、取消状态机与幂等重试、`POST /chat/cancel`、前端停止按钮通知服务端；返修完成窗口竞态（complete_request 白名单）与停止提示即时显示；取消专项 26/26，全量 79/79。

## 当前

- 数字人语音 Phase 1（AI 回复 → 句级 TTS → 连续播放）已实现并完成自动验证（`CURRENT_TASK` 状态 `READY_FOR_ACCEPTANCE`）：后端独立语音层（normalizer/segmenter/profile/provider 抽象/orchestrator + 取消）、SSE 句级 voice 事件、前端 StreamingAudioPlayer（队列/状态机/requestId 隔离）；已接入 Qwen DashScope Provider（WebSocket SDK，密钥仅环境变量，真实 API 冒烟通过）；`speechSynthesis` 保留为明确标记的 FALLBACK_TTS；全量回归 142/142。待用户按验收场景 1-7 浏览器验收（重启后端后开播报开关）。
- 3.7G 与 Phase 1 已提交 `a1081fc`。

## 下一步（按依赖顺序，不自动启动）

- 3.7H 剩余子项（Trace 已完成）：Guardrails 白名单与归属校验、20～30 个固定评测案例（建议首版 24 个）与结构化报告；复用 `flask_app/evals/labor_disputes/`。
- 语音、口型与数字人动画的高阶形态归属阶段 4；3.5 生产可信化、第二法律领域继续暂缓。
- 正式环境仍须重新同步 3.7C 法源，并由有权限的法律专业人员完成真实复核。

## 暂缓

- 阶段 3.5：身份权限、告警、加密、长期运行保障（含匿名身份 Cookie 续期）。
- 第二真实法律领域、基础语音与复杂数字人动画。
