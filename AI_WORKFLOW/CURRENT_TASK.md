# 当前任务

- 阶段/任务名称：法小助 Rive 数字人最终接入与完整角色展示
- 当前状态：`READY_FOR_ACCEPTANCE`（2026-09-09；无背景正式资源、桌面三处入口与 PNG 卸载已验证）
- 目标：使用正式 `.riv` 作为数字人主体；右下角、聊天面板和工作台助手展示真实 Rive 角色，不再沿用 PNG 阶段的圆形头像壳。
- 修改范围：仅前端数字人展示层、Rive 资源与可见性控制；不修改后端、API、数据库、Agent、SSE、TTS 或案件业务。
- 已确认：运行资源 `public/digital-human/law-xiaozhi/law-xiaozhi.riv` 已由保留的源文件 `digital-human/law_xiaozhi/无背景.riv` 覆盖，SHA-256 均为 `FE1EFD70967A31A1C9D83DF8E903E8B255300E2F173C6038ED55942E7EA7AAF8`；本地 `rive.wasm`、`Artboard 1`、`AvatarStateMachine`、`ViewModel1` 与 `expression`/`speaking`/`blink` 映射未变。
- 已确认：桌面浏览器的右下角、聊天与工作台各为 1 个 Rive Canvas、0 个数字人 PNG，Canvas 外层透明且无边框、圆角或旧光圈，控制台 0 error。不可见的双挂载实例不再渲染 PNG，重新显示和 Rive 加载失败时仍保留 PNG 兜底。
- 遗留：移动端真实视口仍待人工验收。

> 以下为上一项入口拆分任务记录。

- 阶段/任务名称：拆分数字人咨询入口与案件工作台入口
- 当前状态：`READY_FOR_ACCEPTANCE`（2026-09-09；入口拆分与跨页面覆盖返工均已通过类型检查、浏览器回归和 diff-check）
- 目标：数字人悬浮入口只表达咨询助手；案件工作台在全站顶栏提供独立入口。数字人聊天仅保留“转入案件办理”的上下文动作，不再把工作台作为数字人自身功能入口。
- 修改范围：仅调整前端入口与视图编排；继续复用现有 `digitalHumanStore`、`CaseWorkspaceShell`、session/matter/Agent/SSE/TTS 状态，不修改后端、API、数据库、案件流程或审批边界。
- 已确认决策：拆入口与界面职责，不拆底层上下文；保持聊天与工作台双挂载，避免切换导致草稿、在途上传、SSE 或滚动位置丢失。
- 返工根因：`DigitalHumanFloat` 位于根布局，路由变化不会卸载；普通导航只执行 `router.push`，未复位 `isOpen/workspaceOpen`，导致目标页面已加载但仍被固定定位的工作台覆盖。
- 验收：已在浏览器确认“案件与纠纷 → 案件工作台”可直接打开工作台、返回对话正常、关闭后点击数字人只打开咨询聊天、聊天内显示“转入办理”；返工后从工作台点击“合同审查”，URL 与目标页面均正常切换且工作台自动收起，控制台无错误。`npx tsc --noEmit` 与 `git diff --check` 通过。`npm run build` 因已有 Next 进程占用 `frontend/.next/trace` 长时间停在初始化，未擅自停止用户进程，需空闲时补跑。

> 以下为上一项待验收任务记录，不再作为当前实施目标。

- 阶段/任务名称：恢复全站数字人入口
- 当前状态：`READY_FOR_ACCEPTANCE`（2026-09-07；类型检查、生产构建、运行页面与 diff-check 已通过）
- 目标：撤销开学演示期间的临时隐藏，恢复完整数字人、劳动争议 Agent 和案件工作台的前端入口。
- 修改范围：仅恢复 `frontend/src/app/layout.tsx` 对 `DigitalHumanFloat` 的导入与全站挂载；不修改数字人内部逻辑、后端、API、数据库或业务状态。
- 验收：全站重新显示数字人悬浮入口，点击继续使用原有数字人聊天及其工作台；`npx tsc --noEmit`、`npm run build`、首页 HTTP 200 与入口文案渲染、`git diff --check` 已通过。

> 以下为已结束的临时展示任务记录。

- 阶段/任务名称：开学演示隐藏后续数字人及其 Agent 工作台入口
- 当前状态：`COMPLETED` 后按用户 2026-09-07 指令撤销隐藏
- 目标：当前完整项目继续保留数字人、劳动争议 Agent 和案件工作台代码，但开学演示时前端不展示入口，也不存在可点击触发元素。
- 修改范围：仅移除 `frontend/src/app/layout.tsx` 中全站 `DigitalHumanFloat` 挂载；不删除数字人组件，不修改原项目已有 `/agents` 页面、后端、API、数据库或业务状态。
- 验收：全站页面无数字人悬浮入口；DOM 不挂载数字人聊天/案件工作台；`npx tsc --noEmit`、`npm run build`、`git diff --check` 已通过。

> 以下为已暂停的历史任务记录；不再作为当前实施目标。

- 阶段/任务名称：完整 PNG 状态数字人（暂停 Rive 骨骼拆分）
- 当前状态：`READY_FOR_ACCEPTANCE`（2026-08-18；自动类型检查通过，待浏览器视觉与交互验收）
- 目标：以 `public/digital-human/first-gen/` 的完整角色 PNG 作为唯一正式视觉主体；保留统一头像状态入口与 `mouthOpen` 预留接口，Rive 仅保留为未来可选方向。
- 本次实现：新增纯展示层 `AvatarController` / `AvatarStateAdapter`，将现有 `emotion`、`isLoading`、`voiceSpeaking` 收敛为 idle/listening/thinking/speaking/success/warning 六态；聊天、悬浮入口和工作台助手全部复用同一映射。图片切换用 280ms crossfade，过渡结束立即卸载旧图；idle 呼吸、thinking 轻摆、speaking 律动、success 单次反馈、warning 静态。
- 边界：未使用或接入 `frontend/digital-human/fa-xiao-zhu/` 的 AI 拆层素材；未修改角色比例、`digitalHumanStore`、SSE、TTS、取消链、聊天/工作台业务结构；未引入 Rive 依赖或 `.riv`。
- 验证：`npx tsc --noEmit`、`npm run build`、`git diff --check` 通过；浏览器需检查六态视觉、切换无闪图、聊天与工作台一致，以及语音播放/停止和 SSE 取消保持原行为。

> 以下为已完成的工作台 UI 历史任务记录；不再作为当前实施目标。

- 阶段/任务名称：案件工作台 UI 布局与信息层级优化（最小范围视觉收敛）
- 当前状态：`IMPLEMENTING` → 实施完成待验收（2026-08-16 全部改动完成，tsc/diff-check 通过，已提交 `数字人前端优化`；浏览器视觉验收待用户执行 → 验收后 `COMPLETED`）
- 目标（用户规格）：不重新设计，在现有工作台做最小范围、高收益视觉收敛——三栏比例（左约 190~220px / 中自动剩余 / 右约 340~380px）；左栏降噪（当前案件置顶、最近会话限量、删除钮 hover、标题 1~2 行）；阶段条当前突出、非当前降权；表单橙色只在校验触发后出现（未填写只显示红色 *，顶部"还缺 N 项"常显）；右栏助手加宽并改为工作台式信息层级（判断/下一步/缺失待确认）；快捷操作 4 项（解释当前步骤/帮我检查材料/相关法律依据/继续提问，均走 preset 预填、用户确认发送）；返回对话统一只保留顶部右上角一个入口；输入区固定底部。
- 边界（用户明确）：禁改业务逻辑/Agent/SSE/cancel/案件状态机/表单数据结构/接口协议/后端/数字人资源；不引入新 UI 库；不处理"聊天↔工作台↔缩小"显示 Bug（已另修，不混入）；不做左栏折叠（避免状态管理重构）。
- 已完成：
  - 用户已完成部分：`AnalysisDocumentStage` 工作台式层级重构（分析结论/争议焦点/风险待确认/金额测算/草稿卡/已验证依据/运行详情）+ 配套 CSS；`LaborRuleResults` 导出 `LABOR_ISSUE_LABELS`；`DigitalHumanCaseAssistant` 摘要化（`buildCaseAssistantSummary` 压缩既有结果、最近上下文折叠、删除重复返回对话）；`WorkspaceSidebar` 当前会话分组/最近 4 条/查看全部/删除钮 hover；
  - Claude 补齐部分：三栏比例（左 200px、右 360px、中剩余，shellBody 12px 卡片间距，移动端复位）；侧栏"当前案件"置顶块 + 条目去卡片化 + 标题 2 行 clamp；阶段条非当前降权、徽标弱化；表单橙色门控（`LaborDisputeForm.highlightMissing` + `FactEvidenceStage.validationAttempted`，有缺失点击只点亮绝不启动分析）；助手快捷操作补"相关法律依据"、身份区压缩（头像 34px）；
  - 验证：`npx tsc --noEmit`、`git diff --check` 通过；已提交 `数字人前端优化`。
- 验收场景（用户浏览器）：
  1. 1920×1080 / 1600×900 / 1440×900 / 1366×768：三栏不重叠、右栏≥320px、中间表单可用、无横向滚动、输入栏底部稳定；
  2. 表单未提交时只有红色 * 与顶部"还缺 N 项"；点击"检查证据、期限和法源"（有缺失）→ 仅橙色点亮、Agent 未启动；补齐后可正常启动；
  3. 助手：当前判断/下一步建议/缺失待确认（与中间数据一致）、4 个快捷操作、相关法律依据预填需确认发送；
  4. 返回对话只在顶部右上角一个入口；
  5. 左栏：当前案件置顶块、默认 4 条最近会话、"查看全部会话（N）"可展开、删除钮 hover 出现（移动端常显）；
  6. ≤640px 移动端：侧栏抽屉、助手 Bottom Sheet、无横向溢出。
- 下一动作：用户浏览器视觉验收 → 反馈问题按 WORKFLOW 返工规则（视觉类走 FRONTEND，不动业务逻辑）；通过则 `COMPLETED`。

- 目标：默认悬浮聊天态（384×650）不变；"普通聊天态 → 用户主动进入案件工作台 → 完整案件办理空间"三级信息架构：桌面 = 左侧 240~260px 会话/案件侧栏 + 中间四阶段工作区 + 右侧 320px↔64px 可收起案件上下文助手；移动端 = 侧栏抽屉 + 阶段横滚 + Bottom Sheet 助手。案件工作台不默认展开；正式审批只在"分析与文书"阶段，数字人只解释不代审批。
- 已确认的追加实施约束（均已落实）：
  1. P2 拆分只拆 UI/展示职责：业务 state 与跨阶段动作保留统一逻辑容器 `useMatterWorkspace`（Shell 挂载一次），四个 Stage 只接收 props；
  2. keep-mounted 非强制：Stage 只挂载当前一个；聊天与工作台双挂载（CSS 切换）以保住 SSE/草稿/180s 上传/滚动位置，容器 state 集中在 Shell 层；
  3. 侧栏案件状态：确认 matters 列表接口无 status 字段后，采用 getLaborDisputeWorkflow 并行批量 + 按 matterId 缓存 + 只补缺失（无逐行 N+1）。
- 已完成：
  - store：`workspaceOpen/activeStage/sidebarTab/assistantCollapsed/workspaceGoalDraft/currentMatter` 纯 UI 状态（不持久化）；`openWorkspace/closeWorkspace` 纯视图切换（不 abort SSE、不清语音队列）；
  - `useMatterWorkspace`（统一逻辑容器）+ `JurisdictionStage/MaterialStage/FactEvidenceStage/AnalysisDocumentStage`（纯展示）+ `CaseStageNav/CaseStageContent/WorkspaceHeader/WorkspaceSidebar/CaseWorkspaceShell`；
  - `DigitalHumanCaseAssistant`（可收起 320↔64px、当前阶段状态、快捷操作只预填问题、返回对话、未读计数）；`MatterEntryCard` 聊天轻量入口（有关联案件=状态卡+继续办理；无案件=从对话创建/历史案件）；`ConversationComposer` 新增 preset/focusSignal（可选 props，原行为不变）；
  - 删除 `DigitalHumanMatterWorkspace.tsx`、`DigitalHumanCompanion.tsx`；新增 `Workspace.module.css`（含 ≤640px 移动端适配）；Float styled-jsx 既有 class 未删未改；
  - 验证：`npx tsc --noEmit` 通过、`git diff --check` 通过；模块地图《工作台.md》《数字人对话.md》已更新并标日期；modification-log 已追加。
- 关键验收场景（用户浏览器测试用）：
  1. 聊天面板正常、头部"案件工作台"：无当前案件 → 展开轻量入口；有案件 → 直接进工作台；
  2. 从当前对话创建案件 → 工作台阶段①预填最近一条用户问题；打开历史案件 → 侧栏案件页；
  3. 工作台四阶段自由切换，案件恢复时按 workflow 状态推导默认阶段；阶段切换不丢草稿、不重复请求；
  4. 发送消息后立刻进出工作台：SSE 流式与语音播报不断；返回对话滚动位置保留；上传大文件识别中切换视图结果不丢；
  5. 助手收起（64px rail：头像/状态点/thinking/说话波形/未读点）与展开；快捷操作只预填问题、发送需用户确认；助手无审批入口；
  6. 审批/Word/PDF 导出只在阶段④；底部风险/人工复核/草稿声明可见；
  7. 移动端 ≤640px：侧栏抽屉、助手 Bottom Sheet、阶段横滚、无横向溢出。
- 遗留项（验收后按需处理）：`dh-panel-expanded` 等旧样式类与部分 dh-matter-* 全局类已无引用（CODE_RULES 保留未删，P4 收尾时向用户确认是否清理）；Shell top 偏移写死 80px；无焦点陷阱。
- 下一动作：用户浏览器验收 → 反馈问题则按 WORKFLOW 返工规则处理；通过则 `COMPLETED`。不自动启动 3.7H 其余子项与下一阶段。
