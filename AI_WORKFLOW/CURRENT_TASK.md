# 当前任务

- 阶段/任务名称：数字人最小全链路 Trace（3.7H 的 Trace 子项）—— trace_id 串联 会话→路由→记忆→案件→Agent。
- 当前状态：`COMPLETED`（2026-08-15 实现与自动验证完成：trace 专项 10/10，全量回归 152/152，tsc/compileall/diff-check 通过；后端基础设施无需浏览器验收，重启后端后即可在 logs/trace.jsonl 与 app.log 看到 [trace] 链路）。
- 目标：正常运行时按 trace_id（=request_id）即可回溯一次会话：请求开始 → 路由决策 → 动作执行（建案/启动 Run，run_id↔trace_id 关联）→ 完成/取消/失败；写 logs/trace.jsonl（JSONL）并镜像 app.log；写入失败绝不拖垮业务。
- 已完成：
  - `services/conversation/tracing.py`：trace()/link_run/trace_for_run/unlink_run/set_trace_file；
  - 挂点：digital_human_service（request_start/request_error/request_cancelled）、orchestrator（request_replayed/route_decision/action_executed/request_completed/request_failed/request_cancelled）、actions（matter_created/run_started + link_run）；execute 新增可选 request_id；
  - `test_digital_human_trace.py` 10/10；全量回归 152 项复跑中；
  - 模块文档 `法律AI/模块地图/链路追踪.md` 已产出。
- 边界：不改 Agent 业务逻辑、不侵入 legal_agent_system（步骤明细仍以 DB AgentRun.steps 为准）；不做 Guardrails、评测集（用户裁定）；前端零改动。
- 前序任务（已收尾）：语音 Phase 1 仍待浏览器验收（Qwen 语音链路），状态保持 READY_FOR_ACCEPTANCE。
- 下一动作：收尾（提交时机由用户决定）；不自动启动 3.7H 其余子项（Guardrails/评测集）与下一阶段。语音 Phase 1 浏览器验收仍待用户执行。
- 目标：比赛展示可用的语音效果：
  ```text
  LLM 流式回复 → 语音文本标准化 → 按完整句切分 → 后端 TTS → 前端音频队列 → 连续播放 → 支持立即打断
  ```
- 范围：
  - 后端独立语音层 `services/voice/`：`SpeechTextNormalizer`（展示文本→朗读文本，只变形式不变法律含义：Markdown/URL/括号/千分位/百分比/emoji）、`SentenceSegmenter`（。！？；成句即产出，短碎片缓冲，超长兜底截断）、`VoiceProfile`（法小助配置，仅环境变量）、`TtsProvider` 抽象+注册表（synthesize/cancel，业务不依赖 SDK）、`VoiceOrchestrator`（requestId 隔离、句缓冲、primary/fallback 明确标记、取消）；
  - SSE 新增 `voice` 事件（seq/text/tts_mode/audio_b64），仅 `voice=true` 请求出现；呈现循环内取消信号即停并 CANCELLED 收尾；`cancel_request` 联动语音编排器；
  - 前端 `streamingAudioPlayer.ts`：队列播放（enqueue/playNext/pause/resume/stop/clear/destroy）、状态机 IDLE/BUFFERING/PLAYING/PAUSED/STOPPED/ERROR、onSpeechStart/End/Pause/Resume/Cancelled 事件预留、requestId 隔离（迟到片段丢弃）、单条错误跳下一条不卡死；`speechSynthesis` 保留为明确的 FALLBACK_TTS（`tts_mode: "fallback"`，不静默混用）；
  - 打断闭环：停止生成 = cancel_chat(requestId) + 停 LLM + 取消在途 TTS + 停在播音频 + 清队列 + 迟到音频禁入；语音开关关闭只停 TTS/播放，不影响文字与 Agent。
- 关键事实：当前 3.7F 架构是"已验证回复的呈现流"，原始 LLM token 不提前出后端；句级流水线接在呈现层（句子完成即合成下发，首句播放与后续合成并行）。真正的 token 级增量需改 Orchestrator 主链路，本阶段按要求不动。
- 不做：ASR、麦克风输入、口型/Viseme、AvatarMotionDriver、动画、聊天窗口重构、Agent 业务修改。
- Provider 现状：已接入 Qwen DashScope（用户提供密钥与参数，2026-08-15）：`services/voice/provider/qwen_provider.py`，经查证 qwen-audio-3.0-tts-flash 走官方 dashscope SDK 的 WebSocket 协议（非 HTTP 接口）；`requirements.txt` 新增 dashscope 并已安装；真实 API 冒烟通过（每句约 17KB mp3，orchestrator 产出 primary 模式片段）。密钥只从环境变量读取，未写入代码或 .env —— 待用户自行把 DASHSCOPE 变量加入 flask_app/.env 并重启后端后生效。
- 验证：
  - `test_digital_human_voice_phase1.py` 32/32（normalizer/segmenter/orchestrator 取消与降级/voice 事件序与 fallback 标记/取消呈现/Qwen Provider 假 SDK 注入/前端播放器守卫）；3.7G 31/31；全量回归 142/142；`npx tsc --noEmit`、compileall、`git diff --check` 通过；
  - 真实 API 冒烟：默认全局 WS 地址合成成功（约 17KB mp3/句，primary 模式）；
  - 人工验收场景 1-7：短回答自然播放、长回答句级流式连续不重叠不乱序、法律文本朗读自然（法条/日期/金额/百分比）、停止立即打断、A 取消后 B 隔离、TTS 异常文字正常、关闭语音无声音且 Agent 正常。
- 下一动作：用户在 flask_app/.env 添加 DASHSCOPE 变量并重启后端 → 浏览器验收场景 1-7 → `COMPLETED`。工作区改动未提交，提交时机由用户决定。
- 关联方案：用户规格（本阶段禁止项与 Provider 边界以用户消息为准）；`newModify/阶段3.7G架构设计.md` 为前序语音基线。
