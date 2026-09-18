# 当前任务

- 阶段/任务名称：`/chat` 顶部法小助欢迎 Hero 精修
- 当前状态：`READY_FOR_ACCEPTANCE`（2026-09-18；数字人尺寸、底部衔接和讲解手势可见性已完成真实浏览器验证）
- 目标：只恢复 Hero 数字人更高、更大、更靠下的展示效果，允许身体与讲解手势自然延伸到功能卡片上沿；保持横向区域、气泡、Hero 背景、文案、功能入口及页面业务行为不变。
- 修改范围：仅 `DailyConversationPage.module.css` 的 `.avatarStage` 与 Hero 内 `.dh-avatar` 视口样式及必要项目记录；顶部导航、左侧文案、左右栏、聊天区、四个功能入口、Store/API/SSE/TTS/后端保持不动。
- 已确认：继续使用 `DigitalHumanAvatar → RiveDigitalHuman → /digital-human/law-xiaozhi/digitalv3.riv` 正式链路，不引入旧 PNG 或新的数字人实现。
- 验收：`npx tsc --noEmit --incremental false`、`git diff --check` 通过；真实浏览器确认数字人为 560px 视口并采用绝对定位，数字人局部容器允许溢出、Banner 外层继续裁切，讲解状态右手完整可见且人物下沿由功能卡片自然遮挡；无横向溢出，正式 Rive 为单 Canvas，控制台无 error；视觉完成仍以用户人工页面验收为准。

> 上一项任务：普法问答聊天内容排版优化（已完成，以下记录保留作背景）。

> 以下为上一项 Rive 数字人接入任务记录。

- 阶段/任务名称：法小助全身 Rive 资源与身体动作接入
- 当前状态：`READY_FOR_ACCEPTANCE`（2026-09-17；已将内部身体组件重叠的 `digitalv2.riv` 替换为 `digitalv3.riv`，恢复原半身渐变；类型、差异及浏览器 idle/朗读组合验证通过）
- 目标：使用用户新增的全身 Rive 文件，页面仍按原方案显示半身；身体仅由 `bodyState` 五态控制，脸部由 `expression / speaking / blink` 组合驱动，不叠加 CSS 身体动画。
- 修改范围：`RiveDigitalHuman.tsx`、`DigitalHumanAvatar.tsx`、`DailyConversationPage.module.css` 的数字人视口、`DigitalHumanFloat.tsx` 的共享头像动画规则、`frontend/public/digital-human/law-xiaozhi/digitalv3.riv` 及必要项目记录；不修改 Store/API/SSE/TTS、三栏结构、案件流程或后端。
- CURRENT_TASK_MISMATCH：本次用户目标已从上一项 `/chat` UI 精修切换为聊天内容排版优化；以下 UI 内容保留为已完成背景。
- 已确认：顶部导航保留；左侧约 240px 只读 `digitalHumanStore`/后端数字人会话记录；中央保持回答卡片既有尺寸；右侧约 300px 增加只读真实上下文栏，移动端顺序堆叠；数字人居中放大并以渐变柔和遮挡下半身；快捷问题只预填不自动发送。
- 已确认：普通法律问题直接回答；合同审查、文书起草等使用已有 `route/routeLabel` 按钮；明确劳动仲裁/维权/案件处理只引导用户进入现有劳动仲裁 Agent/案件工作台，不自动跳转、不新增 Agent；`/chat` 不显示右下角重复数字人，其他页面继续保留。
- 已确认：数字人状态继续由真实 `emotion`、`isLoading`、`voiceSpeaking` 驱动，STT 识别期间补充“正在聆听”；对话区保留全部用户和 AI 消息，AI 回答支持朗读/停止与复制；不编造摘要、结论或业务状态；不修改后端/API/数据库/Agent/SSE/TTS 契约。
- 验收：新建/切换/删除数字人会话、Rive 单实例、Idle/聆听/思考/回答、SSE/停止、STT/TTS/复制、快捷问题预填、功能页/案件工作台入口、右栏真实数据与空态、1366×768/1440×900/移动端无重叠和横向滚动；执行 TypeScript、相关测试/构建和 `git diff --check`。
- 继续实施（2026-09-16）：按当前会话最新确认的右栏方案，案件工作台右侧保持约 360px 展开、64px 收起的案件上下文助手；展示当前判断/下一步/缺失待确认，四个快捷操作只预填，移动端使用 Bottom Sheet，不增加审批或自动发送。

> 以下为上一项 Rive 数字人接入任务记录。

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
