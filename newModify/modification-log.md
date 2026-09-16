# 项目修改记录

本文件用于持续记录每次项目解析、文档修改、代码修改和配置调整。后续默认追加到本文件，便于按时间和会话追溯。

## 2026-08-18（完整 PNG 状态数字人：暂停 Rive 骨骼拆分）

- 原因与边界：AI 生成的 body/arm/cape 拆层素材无法与原始法小助 PNG 保持像素级透视、比例和造型一致，故 `frontend/digital-human/fa-xiao-zhu/` 未接入、未提交，Rive 仅保留为未来可选方向。
- 新增 `AvatarController.ts` 与 `AvatarStateAdapter.ts`：纯展示映射层，保留 `mouthOpen` 可选接口；根据既有 `emotion`、`isLoading`、`voiceSpeaking` 输出 idle/listening/thinking/speaking/success/warning 六态，且不写入或重构 `digitalHumanStore`。
- `DigitalHumanAvatar.tsx` 改为只读取 `public/digital-human/first-gen/` 完整状态图；两层 PNG 仅在 280ms crossfade 内共存，过渡结束即卸载旧图。`DigitalHumanFloat.tsx` 追加 idle 呼吸、thinking 轻摆、speaking 律动、success 一次轻弹与 warning 静态样式，不改变图像比例或引入拆层素材。
- 聊天区、悬浮入口和案件工作台助手均把既有加载/朗读状态传给同一头像映射层；SSE、TTS、取消、案件工作台和接口链路零改动。
- 验证：`npx tsc --noEmit`、`npm run build`、`git diff --check` 通过；浏览器视觉验收待用户执行。

## 2026-07-09 11:01:58 +08:00

- 会话 ID：`019f44b9-02ee-71d1-a9cb-cb659cb92392`
- 分支/Git 状态：当前分支 `master`；执行修改前存在未跟踪目录 `frontend/digital-human/`，本次未触碰。
- 用户请求：在项目根目录创建 Markdown 规则文件，要求后续项目解析和项目修改前优先读取 `raw` 与 `newModify` 资料；远程仓库有新改动时刷新最新项目解析；每次修改后记录时间、会话 ID、修改思路和具体方案。同时询问后端应如何查看。
- 修改前阅读：
  - `D:\项目\law\raw\项目解析报告.md`
  - `D:\项目\law\flask_app\app.py`
  - `D:\项目\law\flask_app\routers\__init__.py`
  - `D:\项目\law\flask_app\core\config.py`
  - `D:\项目\law\flask_app\core\database.py`
  - `D:\项目\law\requirements.txt`
  - `flask_app/routers`、`flask_app/services`、`flask_app/models` 的结构扫描结果
- 修改思路：把长期协作规则放在项目根目录，方便后续一进项目就能看到；把会变化的最新项目解析和修改追溯放在 `newModify` 下，并使用固定文件名，避免解析文档越生成越多。
- 具体方案：
  - 新增根目录 `PROJECT_CONTEXT_RULES.md`，记录上下文读取顺序、远程更新触发规则和后端阅读路线。
  - 新增根目录 `PROJECT_MODIFICATION_RULES.md`，记录每次修改后必须写入的追溯字段和模板。
  - 新增 `newModify/latest-project-analysis.md`，作为当前最新项目解析，后续远程更新时覆盖它。
  - 新增 `newModify/modification-log.md`，作为持续追加的修改追溯文件。
- 实际改动：
  - `D:\项目\law\PROJECT_CONTEXT_RULES.md`
  - `D:\项目\law\PROJECT_MODIFICATION_RULES.md`
  - `D:\项目\law\newModify\latest-project-analysis.md`
  - `D:\项目\law\newModify\modification-log.md`
- 验证：已按 UTF-8 读取新增 Markdown 文件；`git status --short --untracked-files=all` 确认新增文件为本次文档，且既有未跟踪目录 `frontend/digital-human/` 仍未触碰。本次未修改业务代码，未运行后端或前端测试。
- 风险与后续：当前只是建立规则和初始解析。以后如果代码结构、接口或启动方式发生变化，应覆盖刷新 `newModify/latest-project-analysis.md` 并追加本日志。

## 2026-07-11 22:18:39 +08:00

- 会话 ID：`019f5101-3bf7-7831-85d0-762bfbe13dac`
- 分支/Git 状态：当前分支 `master`；工作树在本次开始前已经存在未跟踪的规则文档、`raw`/`newModify` 资料和 `frontend/digital-human/` 素材，以及已暂存的空数字人 Router/Service 文件。本次保留这些既有内容，没有提交、推送或清理用户改动。
- 用户请求：阅读数字人方案，参考现有 `legal.py` 与 `legal_agent.py` 实现独立数字人 Agent；注册后端接口；实现全局悬浮数字人前端和状态动作；补充数字人数据模型所需的 `Float` 导入；排查本地代理连接问题。
- 修改前阅读：
  - `D:\项目\law\raw\数字人智能助手实现方案.md`
  - `D:\项目\law\newModify\latest-project-analysis.md`
  - `D:\项目\law\flask_app\routers\legal.py`
  - `D:\项目\law\flask_app\services\legal_agent.py`
  - `D:\项目\law\flask_app\services\llm_factory.py`
  - `D:\项目\law\flask_app\core\config.py`
  - `D:\项目\law\flask_app\models\db_models.py`
  - `D:\项目\law\sql\public.sql` 中现有法律问答会话/消息表结构
  - 前端 `package.json`、`layout.tsx`、`globals.css`、`chatStore.ts`、`TopNavbar.tsx`、`next.config.js` 和数字人状态图
  - 本次补记前重新读取 `PROJECT_CONTEXT_RULES.md`、`PROJECT_MODIFICATION_RULES.md` 与本修改日志
- 修改思路：数字人保持轻量级对话助手定位，复用现有 LLM 工厂和消息调用方式，但使用独立 Router、Service、状态管理和 UI，避免影响专业普法问答；模型只输出受限意图和情绪，真实跳转由后端白名单控制；前端沿用现有蓝色法务设计体系和用户提供的角色素材。
- 具体方案：
  - 新建数字人 Service，完成专属提示词、最近 6 条上下文、流式结果聚合、结构化 JSON 容错、意图白名单、情绪字段和 0.6 跳转阈值。
  - 新建数字人 Router，提供聊天与重置接口，并在 Router 汇总和 Flask 入口中注册 Blueprint。
  - 新建前端 API、Zustand Store、悬浮入口、聊天面板和状态头像组件；在根布局中全局挂载；复制 8 张状态图到 Next.js `public` 目录。
  - 通过 CSS `transform`/`opacity` 实现悬浮呼吸、上下浮动、面板过渡、状态切换和思考脉冲，并提供移动端和 `prefers-reduced-motion` 适配。
  - 为现有数字人 SQLAlchemy 模型补充 `Float` 导入，使 `confidence` 字段可加载；当前未把 Service 会话读写迁移到数据库。
  - 诊断 Next.js 代理错误，确认 `localhost` 在当前 Windows/Node 环境优先选择 `::1`，而 Flask 只监听 IPv4；本次仅给出诊断，没有修改 `next.config.js`。
- 实际改动：
  - `D:\项目\law\flask_app\services\digital_human_service.py`
  - `D:\项目\law\flask_app\routers\digital_human.py`
  - `D:\项目\law\flask_app\routers\__init__.py`
  - `D:\项目\law\flask_app\app.py`
  - `D:\项目\law\flask_app\models\db_models.py`
  - `D:\项目\law\frontend\src\services\digitalHumanApi.ts`
  - `D:\项目\law\frontend\src\store\digitalHumanStore.ts`
  - `D:\项目\law\frontend\src\components\DigitalHuman\DigitalHumanAvatar.tsx`
  - `D:\项目\law\frontend\src\components\DigitalHuman\DigitalHumanChat.tsx`
  - `D:\项目\law\frontend\src\components\DigitalHuman\DigitalHumanFloat.tsx`
  - `D:\项目\law\frontend\src\app\layout.tsx`
  - `D:\项目\law\frontend\public\digital-human\first-gen\` 下 8 张状态图副本
  - `D:\项目\law\newModify\latest-project-analysis.md`
  - `D:\项目\law\newModify\modification-log.md`
- 验证：后端相关 Python 文件通过 AST 语法检查；`POST /api/digital-human/chat` 已由用户实际调用并返回 `success=true`、`reply`、`intent`、`emotion`、`confidence` 和 `dh_` 会话 ID；前端 TypeScript 全量检查通过；8 张 public 状态图与原图哈希一致；Git 范围核对确认现有前端文件只改动 `layout.tsx` 的导入和挂载。Next.js 正式构建曾运行约 3 分钟无输出后主动终止，因此生产构建结果未确认。代理诊断中 `127.0.0.1:8001/api/health` 返回 200，而 `[::1]:8001` 连接失败，确认地址族不匹配。
- 风险与后续：数字人数据库表模型已存在，但 Service 仍使用内存会话；下一步应接入数据库事务、最近消息查询、会话更新时间和历史接口。当前匿名会话缺少归属隔离。若继续使用 Next.js rewrite，应处理 `localhost` 的 IPv6 解析问题。状态图是静态姿态图，目前动态效果来自 CSS 和状态切换；连续动画可后续升级为 Lottie、Spine 或视频序列。

## 2026-07-11 22:25:29 +08:00

- 会话 ID：`019f5101-3bf7-7831-85d0-762bfbe13dac`
- 分支/Git 状态：当前分支 `master`；工作树仍包含本会话数字人功能改动和用户已有的未跟踪资料，本次未提交、推送或清理任何既有改动。
- 用户请求：根据对规则漏读原因的分析，在项目根目录新增标准 `AGENTS.md` 入口，提高后续代码代理对项目规则的自动发现能力。
- 修改前阅读：`PROJECT_CONTEXT_RULES.md`、`PROJECT_MODIFICATION_RULES.md`、`raw/数字人智能助手实现方案.md`、`newModify/latest-project-analysis.md`、`newModify/modification-log.md`，并检查当前 Git 状态。
- 修改思路：不复制和分叉现有规则内容，而是建立一个短小、标准、可自动发现的仓库入口，明确开始检查点、从只读转修改时的重新检查点，以及修改后的日志和解析更新检查点。
- 具体方案：新增根目录 `AGENTS.md`，转引两份项目规则和固定上下文路径；要求修改前确认范围和脏工作树，修改后执行验证、追加日志，并在结构性变化时更新最新项目解析。
- 实际改动：
  - `D:\项目\law\AGENTS.md`
  - `D:\项目\law\newModify\modification-log.md`
- 验证：确认 `AGENTS.md` 位于仓库根目录；按 UTF-8 读取检查内容；执行 Markdown 差异检查；核对本次未修改业务代码。由于本次只增强规则发现入口，不改变项目接口、数据模型、启动方式或业务流程，因此未更新 `latest-project-analysis.md`。
- 风险与后续：规则能否自动注入仍取决于具体代理环境，但 `AGENTS.md` 是更常见的仓库级入口；即使环境不自动读取，也应在人工或代理工作流中保留根目录规则枚举步骤。

## 2026-07-12 10:12:29 +08:00

- 会话 ID：`019f5407-6950-7de3-bb03-f9c08f3023ca`
- 分支/Git 状态：当前分支 `master`；修改前已有用户对 `flask_app/.env.example` 的未提交改动，本次保留且未触碰。
- 用户请求：将数字人发送和回复记录持久化到本地 PostgreSQL，不再只保存在后端内存。
- 修改前阅读：`PROJECT_CONTEXT_RULES.md`、`PROJECT_MODIFICATION_RULES.md`、`raw/数字人智能助手实现方案.md`、`newModify/latest-project-analysis.md`、`newModify/modification-log.md`，并核对 `flask_app/app.py`、数字人 Router、Service、数据库模型、前端 Store 和当前 Git 状态。
- 修改思路：以 PostgreSQL 作为数字人后端会话上下文的权威来源；大模型调用成功后再以单个事务保存完整一轮对话，避免出现只有用户消息的半截记录；下一轮调用直接查询数据库最近 6 条消息。
- 具体方案：移除 Service 内存会话字典；新增数据库历史读取和事务保存方法；首次消息先写入父会话并刷新事务，再写入用户与助手消息；显式设置同轮消息时间顺序；现有会话更新活跃状态和更新时间；重置接口同步删除消息与会话并支持回滚。
- 实际改动：
  - `D:\项目\law\flask_app\services\digital_human_service.py`
  - `D:\项目\law\newModify\latest-project-analysis.md`
  - `D:\项目\law\newModify\modification-log.md`
- 验证：使用项目 Anaconda Python 和真实本地 PostgreSQL、伪造 LLM 响应运行临时集成测试；验证一次聊天生成 1 条会话和 2 条按 user/assistant 排序的消息、数据库历史可恢复、重置后会话和消息清零，测试通过且临时数据已清理。另执行 Python AST 语法检查和 Git 范围核对。
- 风险与后续：当前 `user_id` 仍为 `anonymous`，在开放会话列表或历史查询接口前需要实现用户或浏览器级归属隔离；前端刷新展示仍依赖 localStorage，尚未从数据库主动拉取历史。

## 2026-07-12 10:49:53 +08:00

- 会话 ID：`019f5195-f45c-7c12-8464-e269667a0bb9`
- 分支/Git 状态：当前分支 `master`；修改前已有 `flask_app/.env.example`、`flask_app/services/digital_human_service.py`、`newModify/latest-project-analysis.md` 和本日志的未提交改动，本次保留且未覆盖用户已有内容。
- 用户请求：按照已确定的“2D 可互动数字人 + 可执行法律 Agent”最终方向制定详细计划，考虑未来扩展到国际法律，并将方案放入 `D:\项目\law\raw`。
- 修改前阅读：`PROJECT_CONTEXT_RULES.md`、`PROJECT_MODIFICATION_RULES.md`、`raw/项目解析报告.md`、`raw/数字人智能助手实现方案.md`、`newModify/latest-project-analysis.md`、`newModify/modification-log.md`，并检查当前 Git 状态。
- 修改思路：以最终产品目标为导向，但按工程依赖拆分阶段；使用 LangGraph 状态图、动态 Plan-and-Execute 和受限 ReAct；从数据结构和工具协议层面引入显式法域上下文，使中国法律成为首个法域实现而非核心硬编码。
- 具体方案：新增长期总体规划，描述目标架构、法域模型、Agent 状态、工具协议、审批风险、2D 实时交互、首个劳动纠纷闭环、七阶段实施路径、数据审计、评测指标和总体完成标准。
- 实际改动：
  - `D:\项目\law\raw\多法域数字人法律Agent总体规划.md`
  - `D:\项目\law\newModify\modification-log.md`
- 验证：执行 Markdown 内容读取、关键章节检索和 Git 差异范围检查；本次只新增规划文档并追加修改日志，未修改接口、数据模型、启动方式或业务代码，因此不更新 `latest-project-analysis.md`。
- 风险与后续：规划涉及长期多阶段建设，实施前应先为阶段 1 单独形成技术设计和验收清单；第二法域应根据真实用户需求、权威数据来源和合规条件选择，不应仅根据开发便利决定。

## 2026-07-12 10:55:46 +08:00

- 会话 ID：`019f5195-f45c-7c12-8464-e269667a0bb9`
- 分支/Git 状态：当前分支 `master`；工作树仍包含此前数字人持久化和规划文档相关未提交改动，本次只调整规划文档并追加日志。
- 用户请求：将规划中的 Runtime、工具、法域、案件和数字人适配模块统一放入 `flask_app` 下的一个总文件夹，强化代码边界。
- 修改前阅读：`PROJECT_CONTEXT_RULES.md`、`PROJECT_MODIFICATION_RULES.md`、`raw/多法域数字人法律Agent总体规划.md`、`raw/数字人智能助手实现方案.md`、`newModify/latest-project-analysis.md`、`newModify/modification-log.md`，并检查 Git 状态。
- 修改思路：采用单一领域总包隔离新 Agent 体系，避免在 Flask 根目录平铺多个顶级模块；通过门面控制外部依赖方向，同时保留现有数字人 Service 的渐进迁移路径。
- 具体方案：规划目录改为 `flask_app/legal_agent_system/`，内部包含 `runtime`、`tools`、`jurisdictions`、`matters` 和 `digital_human`；增加 `facade.py` 公共门面及各子包的依赖边界约束；明确阶段 1 不提前创建无实现空目录。
- 实际改动：
  - `D:\项目\law\raw\多法域数字人法律Agent总体规划.md`
  - `D:\项目\law\newModify\modification-log.md`
- 验证：检查新目录树、`legal_agent_system` 关键字和边界约束章节，并核对 Git 改动范围；本次未创建业务目录或修改运行结构，因此不更新 `latest-project-analysis.md`。
- 风险与后续：总包名称已定为 `legal_agent_system`；阶段 1 实施时应从 `facade.py`、契约 Schema、最小 Runtime 和一个模拟工具开始，避免一次性创建全部模块。

## 2026-07-12 12:10:00 +08:00

- 会话 ID：`019f5449-e6c2-7820-ab2c-7df6f877bf42`
- 分支/Git 状态：当前分支 `master`；开始前已有 `.env.example`、数字人持久化、项目分析、修改日志和总体规划文档的未提交改动，均予以保留并增量修改。
- 用户请求：核验数字人 Agent 所处阶段并开始执行；确认当前不实现登录功能，采用浏览器匿名身份完成阶段 0。
- 修改前阅读：两份项目规则、两份数字人规划、最新项目分析、相关修改日志及数字人前后端源码。
- 修改思路：PostgreSQL 作为会话权威来源；以浏览器持久化 `client_id` 隔离匿名用户；使用独立请求表实现幂等；不提前创建阶段 1 空架构。
- 具体方案：所有数字人接口携带并校验客户端标识；补齐会话列表、消息历史和删除接口；新增请求幂等表；前端支持历史恢复、切换、删除、45 秒超时和取消等待；localStorage 不再保存完整消息。
- 实际改动：数字人数据模型、Router、Service、前端 API、Store、聊天组件、样式，以及本项目分析和修改日志。
- 验证：Python `py_compile`、前端 `npx tsc --noEmit`、`git diff --check` 通过。完整后端导入未完成：系统 Python 缺 `flask_sock`，Anaconda Python 缺 `flask_cors`；前端正式构建长时间无输出后停止，按用户要求不继续处理环境。
- 风险与后续：当前是浏览器级匿名隔离，不是账号认证；前端取消可立即结束本地等待，但无法保证同步 Flask 工作线程终止上游模型调用；进入阶段 1 前需在正式环境完成 PostgreSQL 建表、跨客户端隔离、重复请求和服务重启恢复联调。

## 2026-07-12 11:57:00 +08:00

- 会话 ID：`019f5449-e6c2-7820-ab2c-7df6f877bf42`
- 用户请求：用户完成环境安装后继续运行时验证。
- 修改思路：完整 Flask 导入受无关旧模块依赖阻挡，因此使用数字人专用集成测试直接验证本次数据库链路，不为本任务修改图像处理或模拟法庭模块。
- 实际改动：新增 `flask_app/tests/test_digital_human_stage0.py`；更新最新项目分析和本日志。
- 验证：在 Anaconda Python 中安装数字人链路所需依赖后，使用真实 PostgreSQL 和伪造 LLM 响应运行集成测试；匿名客户端隔离、2 条消息历史、相同 `request_id` 响应复用、会话删除及测试数据清理全部通过。
- 环境说明：完整 `app.py` 导入仍被其他模块阻挡，包括 pytesseract/pandas/pyarrow 与 NumPy 2 的二进制兼容问题，以及 `courtroom_websocket.py` 缺少 FastAPI。数字人专用测试不依赖这些模块。

## 2026-07-12 12:52:00 +08:00

- 会话 ID：`019f5449-e6c2-7820-ab2c-7df6f877bf42`
- 用户请求：修复 `npm run dev` 出现的 `.next/trace` EPERM 和 webpack runtime `undefined.call`，首页返回 500。
- 修改前阅读：项目上下文与修改规则、数字人总体规划、最新项目分析、相关修改日志、当前 Git 状态和前端差异。
- 根因：此前中断的 Next 正式构建留下损坏的 `.next` 生成物；开发服务器启动时无法创建 trace，随后服务端 webpack runtime 引用了不完整模块。数字人 TypeScript 源码检查通过，不是组件导入错误。
- 处理方案：确认 3000 端口 Node 进程归属，只停止本项目的 npm/Next 进程；校验 `.next` 路径位于前端目录后删除生成缓存；以单个 `npm run dev` 进程重新编译。
- 实际改动：未修改业务源码；清理并重新生成 `frontend/.next`，追加本日志。
- 验证：`.next/trace` 与新的 `webpack-runtime.js` 正常生成；连续三次请求 `http://127.0.0.1:3000/` 均返回 200；`npx tsc --noEmit` 和 `git diff --check` 通过。
- 风险与后续：开发服务器当前保持运行。避免在同一个 `.next` 目录中同时运行或强制中止 `next build` 与 `next dev`；若再次发生，先停止本项目 Node 进程再清理 `.next`。

## 2026-07-12 13:00:00 +08:00

- 会话 ID：`019f5449-e6c2-7820-ab2c-7df6f877bf42`
- 用户请求：前端仍无法启动，要求重新诊断并修复。
- 根因：上次验证留下的隐藏 `next dev` 占用 3000 端口和 `.next`；用户再次运行后形成第二套同项目开发进程，两套实例争用相同端口与构建目录。上次日志中“保持运行”的处理不适合用户继续手动启动。
- 处理方案：按命令行识别两套 npm/Next 进程并全部停止；安全清理 `.next`；独占启动一次开发服务器完成复现验证；验证后停止全部测试子进程，把 3000 端口释放给用户。
- 实际改动：未修改业务源码；重新生成前端开发缓存并追加本日志。
- 验证：独占 `npm run dev` 后 `http://127.0.0.1:3000/` 返回 200、响应长度 37460；随后彻底停止测试进程，确认 `PORT_3000_FREE=True`；`npx tsc --noEmit` 通过。
- 风险与后续：后续只能启动一个 `next dev`。当前端口已释放，用户可在自己的终端运行 `npm run dev`；不要同时再启动第二个实例。

## 2026-07-12 13:10:00 +08:00

- 会话 ID：`019f5449-e6c2-7820-ab2c-7df6f877bf42`
- 用户请求：数字人面板点击圆形刷新图标后记录消失，要求检查。
- 根因：聊天面板的 `RotateCcw` 图标被绑定到 `reset()`；该方法会调用后端 reset 接口并永久删除当前会话，与用户理解的“刷新记录”语义不一致。
- 修改方案：圆形箭头改为重新拉取会话列表和当前会话历史，不再调用 reset；显式垃圾桶按钮继续承担删除会话职责。
- 实际改动：`frontend/src/components/DigitalHuman/DigitalHumanChat.tsx`，以及本日志。
- 验证：前端 TypeScript 全量检查通过；代码检索确认圆形箭头不再调用 reset；Git 差异检查通过。
- 风险与后续：此前通过旧按钮已经从数据库删除的记录无法由刷新恢复；修复后新记录不会再因点击圆形箭头被删除。

## 2026-07-12 13:20:00 +08:00

- 会话 ID：`019f5449-e6c2-7820-ab2c-7df6f877bf42`
- 用户请求：修复页面未完全加载时数字人图片短暂铺满全屏的问题。
- 根因：头像使用 Next.js `Image fill`，关键尺寸完全依赖 styled-jsx；初始样式尚未生效时，绝对定位图片会以视口为尺寸参照。
- 修改方案：移除 `fill`，为图片提供明确的 width/height 属性；头像容器使用内联关键几何约束，并通过 CSS 变量保留桌面和移动端尺寸适配。
- 实际改动：`frontend/src/components/DigitalHuman/DigitalHumanAvatar.tsx`、`frontend/src/components/DigitalHuman/DigitalHumanFloat.tsx`，以及本日志。
- 验证：前端 TypeScript 全量检查通过；检查生成代码确认图片具有固有尺寸、容器在样式表加载前也具有最大边界；Git 差异检查通过。
- 风险与后续：本次只调整首屏关键尺寸约束，不改变数字人状态切换或图片资源。

## 2026-07-12 13:35:00 +08:00

- 会话 ID：`019f5449-e6c2-7820-ab2c-7df6f877bf42`
- 用户请求：圆形箭头刷新行为仍不可信，且原生历史下拉框存在内容和交互问题。
- 根因：刷新逻辑并发调用列表与当前会话加载，错误被静默处理；历史使用原生 select，当前会话、切换行为和删除边界表达不清，弹出层遮挡内容。
- 修改方案：Store 新增顺序执行的 `refreshHistory`；圆形箭头只调用该方法；新增不删除旧记录的“新对话”；历史改为自定义列表，明确标识当前会话、切换操作和独立垃圾桶删除。
- 实际改动：`frontend/src/store/digitalHumanStore.ts`、`frontend/src/components/DigitalHuman/DigitalHumanChat.tsx`、`frontend/src/components/DigitalHuman/DigitalHumanFloat.tsx`，以及本日志。
- 验证：前端 TypeScript 全量检查和 Git 差异检查通过；在本地页面实际打开数字人，确认刷新按钮、历史会话按钮、新对话按钮分别存在；展开历史列表不会使用浏览器原生下拉框，空状态和面板布局正常。
- 风险与后续：历史标题当前仍取首条用户消息前 30 字；后续可增加自动摘要标题，但不影响会话归属和消息正确性。

## 2026-07-12 15:00:16 +08:00

- 会话 ID：`019f550e-f809-7d63-9c7d-cb1ad0e1173d`
- 分支/Git 状态：当前分支 `master`；开始前已有未跟踪的 `flask_app/tests/` 和 `raw/多法域数字人法律Agent总体规划.md`，本次保留并增量使用，没有清理、提交或推送用户改动。
- 用户请求：确认阶段 1 计划并实现 Agent 基础协议与 Runtime，包括状态机、工具协议、模拟工具、失败重试、暂停确认、恢复、审计和前端最小交互。
- 修改前阅读：`PROJECT_CONTEXT_RULES.md`、`PROJECT_MODIFICATION_RULES.md`、`raw/数字人智能助手实现方案.md`、`raw/多法域数字人法律Agent总体规划.md`、`newModify/latest-project-analysis.md`、`newModify/modification-log.md`，以及 Flask 入口、Router、数字人 Service、数据库模型、阶段 0 测试和数字人前端源码。
- 修改思路：遵守总体规划的 `flask_app/legal_agent_system/` 单一总包边界；原数字人问答保持不变，通过独立 Router 和 Facade 接入；以 PostgreSQL 保存运行状态，LangGraph 负责流程编排，权限、重试和审批规则由确定性代码控制。
- 具体方案：定义 Pydantic 协议、枚举和错误码；新增 Matter、Run、Step、ToolCall、Approval、Audit 六类模型；实现工具注册中心和首次失败后成功的模拟摘要工具；实现规划、执行、审批暂停、跨实例恢复、完成和取消；开放运行创建、查询、恢复、取消和审计 API；前端增加模拟任务步骤与审批卡片。
- 实际改动：`flask_app/legal_agent_system/`、`flask_app/routers/digital_human_agent.py`、`flask_app/models/db_models.py`、`flask_app/routers/__init__.py`、`flask_app/app.py`、`flask_app/tests/test_digital_human_stage1.py`、数字人前端 API/Store/Chat/全局样式、`newModify/latest-project-analysis.md` 和本日志。
- 验证：安装 requirements 已声明但当前环境缺失的 LangGraph 1.2.9；Python compileall、前端 `npx tsc --noEmit`、`git diff --check` 通过；使用真实 PostgreSQL 运行阶段 0 与阶段 1 集成测试，共 2 项通过。阶段 1 验证失败重试、暂停审批、新 Facade 实例恢复、跨客户端隔离、完成结果和审计事件。
- 风险与后续：当前为单步骤模拟工具闭环，不构成真实法律服务；阶段 2 前应补充正式数据库迁移机制，并在阶段 1 后续迭代增加运行列表、API 级测试、步骤/工具预算和过期审批测试。

## 2026-07-12 15:18:57 +08:00

- 会话 ID：`019f550e-f809-7d63-9c7d-cb1ad0e1173d`
- 分支/Git 状态：当前分支 `master`；保留阶段 1 的全部未提交改动和此前未跟踪资料，本次只增强注释与可读性。
- 用户请求：参考项目现有注释风格，为刚实现的阶段 1 代码补充中文注释，降低阅读成本。
- 修改前阅读：两份项目规则、阶段 1 总体规划、最新项目分析、相关修改日志、现有 `legal_agent.py`/`legal.py` 注释风格，以及本次新增的后端、前端和测试代码。
- 修改思路：注释重点说明架构边界、状态流转原因、事务一致性、重试计数、暂停恢复、匿名隔离和安全约束；避免对显而易见的语句逐行翻译造成噪声。
- 具体方案：为 `legal_agent_system` 各模块补充模块说明、类和方法 docstring、关键分支行内注释；为数据模型关键字段、Agent API、前端 API/Store/UI 和集成测试补充中文说明。
- 实际改动：`flask_app/legal_agent_system/`、`flask_app/models/db_models.py`、`flask_app/routers/digital_human_agent.py`、`flask_app/tests/test_digital_human_stage1.py`、`frontend/src/services/digitalHumanApi.ts`、`frontend/src/store/digitalHumanStore.ts`、`frontend/src/components/DigitalHuman/DigitalHumanChat.tsx` 和本日志。
- 验证：Python compileall、前端 `npx tsc --noEmit`、`git diff --check` 通过；真实 PostgreSQL 阶段 0/1 集成测试共 2 项通过，确认只增强可读性，没有改变运行行为。
- 风险与后续：后续新增 Runtime 节点、工具或数据模型时，应同步添加说明职责、输入输出、安全边界和失败策略的中文注释。

## 2026-07-12 15:50:46 +08:00

- 会话 ID：`019f550e-f809-7d63-9c7d-cb1ad0e1173d`
- 分支/Git 状态：当前分支 `master`；工作树包含阶段 1 未提交改动和此前资料，本次在其上增量实现阶段 2，没有清理、提交或覆盖用户文件。
- 用户请求：阶段 1 没问题后进入阶段 2。
- 修改前阅读：两份项目规则、数字人总体规划中阶段 2/法域/来源/工具章节、最新项目分析和相关修改日志；并盘点现有 `document_parser.py`、`rag_service.py`、文档 Router、数据模型及阶段 1 Runtime。
- 修改思路：不直接复用现有仅支持 UTF-8 读取的早期 DocumentParser 和内存模拟 RAG 作为权威层；先在 `legal_agent_system` 内建立材料、事实、法域和法律来源的可追溯数据基础，并继续维持 Router→Facade→领域层边界。
- 具体方案：新增材料/片段/事实/法域/法律来源模型；实现 Matter+client_id 访问控制、文本切片、候选事实定位、时间线和证据清单；建立 CN 法域包和显式确认机制；实现来源登记、有效期/状态/法域/哈希校验及无法验证时降级；包装统一材料和来源工具并开放 API。
- 实际改动：`flask_app/legal_agent_system/matters/`、`flask_app/legal_agent_system/jurisdictions/`、阶段 2 工具适配器、Runtime Schema、Facade、`flask_app/models/db_models.py`、`flask_app/routers/digital_human_agent.py`、`flask_app/tests/test_digital_human_stage2.py`、最新项目分析和本日志。
- 验证：Python compileall、前端 `npx tsc --noEmit`、`git diff --check` 通过；真实 PostgreSQL 阶段 0/1/2 集成测试共 3 项通过。阶段 2 验证材料位置引用、匿名隔离、时间线、证据清单、法域确认、未知来源降级和不支持法域拒绝。
- 风险与后续：当前只完成阶段 2 的文本材料与来源协议闭环；后续仍需接入 PDF/DOCX/图片 OCR 解析器、真实权威法律来源连接器、结构化 LLM 事实提取及重复事实去重。测试来源使用 `.invalid` 域名和明确测试文本，不包含或冒充真实法律内容。

## 2026-07-12 19:30:02 +08:00

- 会话 ID：`019f550e-f809-7d63-9c7d-cb1ad0e1173d`
- 分支/Git 状态：当前分支 `master`；保留阶段 1/2 的未提交改动和用户资料，本次继续增量修改数字人前端与独立 Matter 创建链路。
- 用户请求：按已确认方案实现阶段 2 前端，使用户能在现有数字人面板直接验证材料事实出处，而不是继续看到阶段 1 模拟任务。
- 修改前阅读：项目规则、阶段 2 规划、最新项目分析与修改历史，以及数字人 Chat、Store、API、样式和阶段 2 后端材料接口。
- 修改思路：保留头像、聊天、历史会话和输入框；将阶段 1 模拟卡替换为独立小组件，按“创建案件→确认法域→添加材料→查看分析”组织流程，避免继续膨胀 Chat 组件。
- 具体方案：新增不触发模拟 Runtime 的 Matter 创建接口；新增前端阶段 2 API 类型与聚合调用；新增 `DigitalHumanMatterWorkspace.tsx`，支持目标输入、中国法域确认、省市、TXT 选择/文本粘贴、事实出处展开、时间线和证据提示；明确显示法律来源为 0 和尚未连接权威检索。
- 实际改动：`legal_agent_system/matters/materials.py`、Facade、Agent Router、阶段 2 测试、`frontend/src/services/digitalHumanApi.ts`、`frontend/src/components/DigitalHuman/DigitalHumanMatterWorkspace.tsx`、`DigitalHumanChat.tsx`、`digitalHumanStore.ts`、`globals.css`、最新项目分析和本日志。
- 验证：Python compileall、前端 `npx tsc --noEmit`、`git diff --check` 通过；真实 PostgreSQL 阶段 0/1/2 集成测试共 3 项通过，阶段 2 测试已改为使用与前端一致的独立 Matter 创建链路。
- 风险与后续：当前前端仅支持 TXT/粘贴文本；关闭并重新挂载数字人面板后，尚未完成的本地表单不会恢复，但已提交到 PostgreSQL 的 Matter 和材料仍存在。后续应增加案件列表/恢复接口，并接入 PDF、DOCX、OCR 和权威法律来源。

## 2026-07-12 20:02:16 +08:00

- 会话 ID：`019f550e-f809-7d63-9c7d-cb1ad0e1173d`
- 分支/Git 状态：当前分支 `master`；保留此前阶段 1/2 改动和用户资料，本次增量实现阶段 2.5 与首个真实工具。
- 用户请求：理清并执行下一步方案，完善当前 Agent，代码参考项目风格添加中文注释。
- 修改前阅读：项目规则、总体规划阶段 2/3 与工具边界、最新项目分析和修改历史；盘点 `legal_tools.py`、劳动补偿模型、法律计算器前端、阶段 2 Matter/材料服务和工具注册中心。
- 修改思路：先解决当前 Agent 的案件恢复、删除和重复数据问题，再将项目已有劳动补偿能力下沉为共享 Service，Agent 仅作为受控工具调用方，不复制计算公式或重写计算器。
- 具体方案：增加 Matter 列表/删除；材料按内容哈希去重，事实提取幂等复用；新增带中文注释的劳动补偿 Service；原 Router 改为调用 Service；注册 `calculate_labor_compensation` 工具并要求用户确认 CN 法域；前端增加案件继续/删除与劳动补偿估算区。
- 实际改动：Matter/材料 Service、Agent Facade/Router/工具注册、`services/labor_compensation_service.py`、`routers/legal_tools.py`、数字人 API/材料工作区/样式、`tests/test_digital_human_stage25.py`、最新项目分析和本日志。
- 验证：Python compileall、前端 TypeScript、`git diff --check` 通过；真实 PostgreSQL 阶段 0/1/2/2.5 集成测试共 4 项通过。2.5 验证案件恢复/删除、材料和事实去重、Agent 与原工具共用公式。
- 风险与后续：劳动补偿仍是项目既有简化估算公式，不是完整法律规则引擎；正式数据库迁移框架、案件详情完整恢复、ToolCall 持久化审计和工资封顶/解除原因等规则仍需继续补齐。前端法律计算器自己拼装的“总月份数”展示逻辑与后端既有公式存在历史不一致，后续应统一改为直接展示 Service 返回的 calculation。

## 2026-07-12 20:22:45 +08:00

- 会话 ID：`019f550e-f809-7d63-9c7d-cb1ad0e1173d`
- 分支/Git 状态：当前分支 `master`；保留此前阶段 1-2.5 未提交改动和用户文件，本次只增量修改 Matter 详情及数字人布局。
- 用户请求：修复法域反复要求确认的问题，并扩大当前 Agent 操作画面。
- 修改前阅读：项目规则、总体规划、最新分析和修改历史；检查 Matter/法域后端、数字人 Float/Chat/材料工作区、全局样式和当前 Git 状态。
- 修改思路：根因是恢复案件只读取列表摘要并直接跳到材料步骤，未查询已确认法域；布局问题来自 384px 面板同时承载聊天和完整工作区，并叠加内部滚动。通过 Matter 详情恢复权威状态，并将 UI 拆成普通聊天和展开工作台双模式。
- 具体方案：新增 Matter 详情 API 返回已确认法域；恢复案件时按后端状态决定是否需要确认；显示绿色法域状态和一次性确认说明；普通模式只保留工作台入口；桌面展开为约 920px 左右双栏，移动端近全屏上下布局；移除材料工作区自身高度限制和内部滚动。
- 实际改动：Matter MaterialService、Agent Facade/Router、阶段 2.5 测试、数字人 API、`DigitalHumanMatterWorkspace.tsx`、`DigitalHumanChat.tsx`、`DigitalHumanFloat.tsx`、全局样式、最新项目分析和本日志。
- 验证：Python compileall、前端 `npx tsc --noEmit`、`git diff --check` 通过；真实 PostgreSQL 阶段 0/1/2/2.5 回归测试 4 项全部通过，包含 Matter 法域恢复断言。
- 风险与后续：当前展开状态只保存在组件内，关闭数字人后会回到普通模式；这是界面偏好而非业务状态，不影响 Matter、法域和材料持久化。后续可增加聊天/工作台移动端页签，进一步减少上下布局滚动。

## 2026-07-12 20:42:00 +08:00

- 会话 ID：`019f564d-4e3b-7061-a54c-48bf13da647e`
- 分支/Git 状态：当前分支 `master`；开始前已有阶段 1-2.5 未提交/未跟踪改动、总体规划文档和 `flask_app/uploads/` 中的用户文件，本次全部保留，仅增量实施阶段 3。
- 用户请求：Agent 第二阶段完成后，参考项目文档开始执行第三阶段。
- 修改前阅读：`PROJECT_CONTEXT_RULES.md`、`PROJECT_MODIFICATION_RULES.md`、`raw/项目解析报告.md` 目录与项目风险、`raw/数字人智能助手实现方案.md`、`raw/多法域数字人法律Agent总体规划.md` 的架构/状态/工具/风险/阶段 3/评测章节、最新项目分析、相关修改历史，以及当前 Facade、Runtime、Matter、来源、工具、Router、模型、测试和前端工作台源码。
- 修改思路：保持 Router→Facade→领域层边界，不把劳动纠纷流程继续堆入阶段 1 模拟 Runtime 或大 Router；使用确定性代码控制缺失事实、法域、来源验证、期限规则和草稿审批，复用阶段 2 材料/来源及阶段 2.5 劳动补偿能力。
- 具体方案：新增劳动纠纷事实 Schema、动态追问和动态计划；持久化流程状态与交付物；实现 CN 法域前置校验、仲裁期限初步推算、已登记法律来源检索和有效性验证、证据清单聚合、明确审批后生成仲裁申请书草稿；新增 REST API、前端事实表单/状态反馈/草稿预览和阶段 3 端到端测试。
- 实际改动：`flask_app/legal_agent_system/labor_disputes/`、Facade、Agent Router、数据库模型、`flask_app/tests/test_digital_human_stage3.py`、数字人前端 API/案件工作台/全局样式、最新项目分析和本日志。
- 验证：Python `compileall`、前端 `npx tsc --noEmit`、`git diff --check` 通过；使用 Anaconda Python 和真实 PostgreSQL 单独运行阶段 1/2/2.5/3 集成测试共 4 项全部通过。阶段 3 验证缺失事实暂停、来源不足硬拦截、有效测试来源、期限推算、审批和草稿持久化。一次性发现阶段 0-3 时，阶段 0 在当前沙箱因 Loguru 创建 Windows 多进程管道触发 `WinError 5`，阶段 1-3 均正常通过。
- 风险与后续：当前来源检索仅查找已登记且内容明确匹配仲裁时效规则的来源，没有联网连接权威数据库；测试使用 `.invalid` 地址和明确测试文本，不冒充真实法律内容。正式上线前仍需权威来源适配器、数据库迁移、更多劳动规则（工资封顶、解除原因、时效中止/中断）、离线评测样本扩充和 API 级测试。

## 2026-07-12 20:50:00 +08:00

- 会话 ID：`019f564d-4e3b-7061-a54c-48bf13da647e`
- 分支/Git 状态：当前分支 `master`；保留阶段 1-3 的全部现有改动和用户上传文件，本次只新增测试案件资料及本日志。
- 用户请求：生成一个案件，用于检验当前数字人的功能。
- 修改前阅读：项目上下文与修改规则、数字人总体规划、最新项目分析、阶段 3 修改记录和当前 Git 状态。
- 修改思路：生成完全虚构且显式标注的劳动争议材料，覆盖日期、工资、解除、欠薪、证据清单和仲裁请求；同时给出与当前工作台字段一致的输入与预期结果，避免将测试材料误认为真实法律事实或权威来源。
- 具体方案：新增一份可直接上传的 UTF-8 TXT 综合材料和一份手工/自动化验证说明；不向数据库写入永久测试案件，不伪造真实法律来源。
- 实际改动：`outputs/stage3-demo-case/01-测试案件材料.txt`、`outputs/stage3-demo-case/02-测试输入与预期结果.md` 和本日志。
- 验证：检查测试材料包含可提取日期、金额和“事实：”标记；阶段 3 PostgreSQL 集成测试单项通过；`git diff --check` 通过。
- 风险与后续：手工测试在没有权威来源适配器时应停在 `blocked_authority`，这是预期安全行为；完整草稿链路由自动化测试使用 `.invalid` 测试来源验证，不得用于真实法律结论。

## 2026-07-13 09:54:04 +08:00

- 会话 ID：`019f564d-4e3b-7061-a54c-48bf13da647e`
- 分支/Git 状态：当前分支 `master`；开始前存在用户已加入索引的 Agent 文件，以及未跟踪的测试目录、上传 DOCX、前端工作台、输出资料和总体规划，本次全部保留并在现有阶段 1-3 改动上增量实现。
- 用户请求：规划 Agent 完善方案，并直接执行完善。
- 修改前阅读：项目上下文与修改规则、原始项目解析、数字人实现方案、多法域 Agent 总体规划、最新项目分析、相关修改历史、新增 `legal_agent_system/analyse-agents.md`，以及当前 Runtime、Repository、工具、Facade、Router、劳动纠纷服务、前端 API/工作台和阶段测试。
- 修改思路：消除“阶段 1 LangGraph 只跑模拟工具、阶段 3 真实业务绕过 Runtime”的双轨架构；保留现有模拟 Runtime 兼容性，新增劳动纠纷专用 Graph 和用例层，领域规则继续由 `LaborDisputeService` 维护，Graph 只负责编排和安全状态。
- 具体方案：扩展 AgentState 和运行枚举；为已有 Matter 创建/复用劳动纠纷 Run；将动态计划写入 AgentStep；把证据清单、劳动分析、草稿生成包装为受控工具并持久化 ToolCall；支持法域/事实/来源/审批四类暂停恢复；增加 Runtime API；前端切换到真实 Run/Step；新增跨实例恢复集成测试。
- 实际改动：`runtime/enums.py`、`schemas.py`、`persistence.py`、`labor_graph.py`、`labor_runtime.py`、Runtime 导出、`tools/labor_dispute_tools.py`、工具导出、Facade、Agent Router、数字人前端 API/案件工作台、`tests/test_digital_human_stage31_runtime.py`、最新项目分析和本日志。
- 验证：Anaconda Python `compileall` 通过；前端 `npx tsc --noEmit` 通过；`git diff --check` 通过；真实 PostgreSQL 阶段 1/2/2.5/3/3.1 集成测试共 5 个模块、6 个用例全部通过。3.1 验证等待法域、等待事实、三步计划、真实 ToolCall、来源阻断、来源重试、审批通过/拒绝、跨 Facade 恢复和草稿完成；拒绝草稿不会污染已完成分析步骤。
- 风险与后续：当前真实来源仍仅来自已登记数据库记录，测试来源为 `.invalid`；劳动期限和补偿规则仍是初步版本。旧阶段 3 直接 Service API 为兼容暂时保留，后续稳定后可标记弃用。正式上线前仍需权威来源连接器、通用四类 Verifier、步骤/工具/时长预算、计划版本表、过期审批与幂等草稿测试、Alembic 迁移和更完整离线评测集。

## 2026-07-13 10:34:12 +08:00

- 会话 ID：`019f564d-4e3b-7061-a54c-48bf13da647e`
- 分支/Git 状态：当前分支 `master`；保留阶段 1-3.1 全部现有改动和未跟踪用户文件，本次只增量实施阶段 3.2。
- 用户请求：继续完善未完成的 Agent，并确认当前是否只能处理劳动纠纷。
- 修改前阅读：项目上下文与修改规则、多法域 Agent 规划、Agent 分析文档、最新项目分析、阶段 3.1 修改历史和当前 Git 状态。
- 修改思路：当前统一 Runtime 的业务闭环确实只支持中国劳动纠纷；本轮先补可被后续合同/民事领域复用的安全基础，不在没有权威数据源的情况下伪造来源连接器或扩张法律结论。
- 具体方案：新增结构/事实/来源/风险四类验证器；在 Graph 每次工具结果后验证；增加最大计划步骤和工具调用预算；重复劳动仲裁草稿幂等复用；增加审批过期、预算、幂等和验证失败专项测试。
- 实际改动：`runtime/verifier.py`、Runtime 枚举/状态/Graph/Repository、劳动纠纷 Service、前端 AgentRun 类型、`tests/test_digital_human_stage32_safety.py`、最新项目分析和本日志。
- 验证：Python `compileall`、前端 `npx tsc --noEmit`、`git diff --check` 通过；真实 PostgreSQL 阶段 1/2/2.5/3/3.1/3.2 共 6 个测试模块、10 个用例全部通过。
- 风险与后续：当前只实现步骤和工具次数预算，尚未实现总时长与模型费用预算；验证器覆盖当前劳动工具契约，后续每接入一个领域需增加对应验证规则。统一 Agent 尚不能执行合同、一般民事、模拟法庭等旧模块；下一阶段应选择一个领域，将 Router 逻辑下沉 Service 后按同一工具/验证/评测协议接入。

## 2026-07-13 10:54:33 +08:00

- 会话 ID：`019f564d-4e3b-7061-a54c-48bf13da647e`
- 分支/Git 状态：当前分支 `master`；保留阶段 1-3.2 改动和全部未跟踪用户文件，本次增量修改材料建议链路。
- 用户请求：劳动纠纷字段每次手动输入过于繁琐，希望从已上传 TXT 材料默认提取，用户可选择采用或自行填写。
- 修改前阅读：项目规则、多法域规划、最新项目分析与修改历史；检查用户截图、当前材料分片/事实提取、劳动事实 Schema、Facade/Router、前端 API 和案件工作台表单。
- 修改思路：材料提取结果只能作为候选，不能未经用户确认直接成为法律事实；建议必须保留来源原文并与确认事实写入分离。前端先展示建议卡，用户显式采用后再填表，且保留编辑能力。
- 具体方案：新增独立劳动事实建议提取器；从授权材料确定性识别姓名、单位、日期、工资、地点、争议和请求；开放只读建议 API；材料分析后自动获取建议；增加采用/拒绝和来源展开交互。
- 实际改动：`labor_disputes/suggestions.py`、劳动纠纷导出、Facade、Agent Router、前端 API/案件工作台/全局样式、`tests/test_digital_human_stage33_suggestions.py`、最新项目分析和本日志。
- 验证：Python `compileall`、前端 `npx tsc --noEmit`、`git diff --check` 通过；真实 PostgreSQL 阶段 1-3.3 共 7 个测试模块、11 个用例全部通过。3.3 验证测试材料字段、来源原文、读取不落库和跨客户端拒绝。
- 风险与后续：当前采用确定性文本规则，适合格式清晰的 TXT；复杂自然语言、表格、PDF/DOCX 和图片仍可能缺字段或误识别，因此 UI 始终要求用户核对。后续可接入结构化 LLM 提取，但必须继续要求出处、Schema 校验和用户确认。

## 2026-07-13 16:34:05 +08:00

- 会话 ID：`019f5a67-dce1-7691-913c-80a112528e9d`
- 分支/Git 状态：当前分支 `master`；开始前只有 `flask_app/tests/`、用户上传 DOCX、前端工作台和 `outputs/` 等未跟踪内容，本次全部保留，不删除、不覆盖用户文件。
- 用户请求：绘制当前 Agent 和最终目标架构图到 `raw/`，确认采用方案 B，更新总体规划，并继续完善 Agent。
- 修改前阅读：`PROJECT_CONTEXT_RULES.md`、`PROJECT_MODIFICATION_RULES.md`、`raw/多法域数字人法律Agent总体规划.md`、`newModify/latest-project-analysis.md`、相关修改历史，以及当前 Router、Facade、来源服务、工具注册、Runtime、模型、测试和数据库入口。
- 修改思路：先把当前实现与目标边界固化为可编辑图件，再把方案 B 写回唯一总体规划；代码先实施 3.4A 保护网，不在来源、迁移和评测未稳定时提前增加 Planner 或 LLM 自主性。
- 具体方案：生成两套 Mermaid/Excalidraw/SVG/PNG 架构图；总体规划增加当前基线、方案 B、3.4A～3.4E 和新的依赖顺序；移除公开来源登记 API 与 Agent 来源登记工具；测试来源限制为 `.invalid`；建立 Alembic 非破坏性接管基线；新增 30 个劳动纠纷离线案例、Schema、Runner 和基础测试。
- 实际改动：`raw/当前Agent架构图.*`、`raw/目标Agent架构图.*`、总体规划；来源 Service、Facade、来源工具注册、Agent Router；`requirements.txt`；`flask_app/alembic.ini`、`flask_app/migrations/`、`flask_app/evals/`、阶段 2/3/3.1/3.2 测试调用及新增 `test_digital_human_stage34a_foundation.py`；最新项目分析和本日志。
- 验证：架构图离线渲染成功并完成视觉检查；Python compileall 通过；3.4A 基础测试 4/4 通过；阶段 1～3.4A 共 8 个模块、15 个用例全部通过；Alembic head/history/离线升级 SQL 通过；未对现有数据库执行 stamp 或结构写入。
- 风险与后续：当前 Alembic revision 是接管已有结构的空操作基线，启动时 `create_all` 暂保留兼容；下一阶段 3.4B 必须建立可信 Provider、来源版本和信任等级，之后才适合完善劳动规则和动态 Planner。数据库连接配置仍存在历史硬编码敏感信息，本次未读取 `.env`、未在新文档复制该值，后续应单独迁移到环境变量。

## 2026-07-13 阶段 3.4B～3.4E 完成

- 用户请求：完成阶段 3.4 的全部剩余内容。
- 修改范围：可信法源 Provider/导入与检索、来源元数据、事实断言与规则版本、草稿输入指纹、动态计划与计划版本、统一工具执行器、操作幂等、事件 Outbox、受控 LLM 候选抽取、预算字段、迁移、测试和规划文档。
- 数据库：将现有本地库非破坏性 stamp 到 `20260713_0001`，执行 `20260713_0002` 升级到 head；首次验证发现 ORM 曾预建新表，迁移已改为检测并跳过已有结构，不删除现有数据。
- 安全边界：官方来源只能通过可信 Provider 内部导入；模型候选必须通过 Schema 和原文 quote/offset 校验，且不会自动成为确认事实；继续动作支持幂等键冲突和处理中保护。
- 验证：Python compileall 通过；Alembic current 为 `20260713_0002 (head)`；阶段 1～3.4 共 9 个相关测试模块、19 个用例全部通过。
- 保留内容：未修改或删除用户已有未跟踪前端工作台、上传文档和 outputs 文件。

## 2026-07-13 20:26:57 +08:00

- 会话 ID：`019f5a67-dce1-7691-913c-80a112528e9d`
- 分支/Git 状态：当前分支 `master`；保留既有 Agent 改动、未跟踪上传文档、前端工作台、测试和 outputs，本次仅增量修复法源闭环与前后端契约。
- 用户请求：确认数字人是否只有 3 张数据库表，检查前后端 Agent 功能是否同步，并修复上一轮分析指出的半成品问题。
- 修改前阅读：项目上下文/修改规则、总体规划、最新分析、相关修改历史、数据库实表、Alembic 状态、Facade、Runtime、Router、前端 API 和案件工作台。
- 根因：截图中的 3 张表只属于聊天层；Agent 数据实际分散在 Matter/Run/Step 等表。官方 Provider 只被测试调用，生产启动与来源重试均未同步；前端来源数量与提示写死，重试按钮重复调用启动流程，期限和预算类型落后于后端。
- 具体方案：生产共享 Facade 开启可信法源自动同步；任务开始前和来源重试时幂等同步；前端调用真实 `retry_authority`，展示实际来源，更新期限/预算契约和幂等请求头；补生产门面空法源端到端测试。
- 实际改动：`facade.py`、`labor_runtime.py`、`app.py`、`digitalHumanApi.ts`、`DigitalHumanMatterWorkspace.tsx`、阶段 3.4 完成测试、总体规划、最新分析和本日志。
- 数据库：实库共 75 张表，其中按数字人/Agent职责核对为 20 张；Alembic 为 `20260713_0002 (head)`；当前库已导入 2 条 `official_cn_labor` 可信来源。
- 验证：Python compileall、前端 `npx tsc --noEmit`、阶段 3.4 专项 5/5、阶段 1～3.4 相关回归 20/20 全部通过；新增用例从空法源开始，自动同步后到达 `awaiting_approval` 并返回可信来源。
- 风险与后续：当前官方 Provider 是经过白名单约束的内置权威条款清单，不是定时联网采集器；生产级仍需定时复核任务、同步失败监控和更多劳动实体规则。旧服务进程需要重启后才能加载本次代码。

## 2026-07-13 20:46:06 +08:00

- 会话 ID：`019f5a67-dce1-7691-913c-80a112528e9d`
- 用户请求：说明官方法源同步实际做什么、为什么界面看不到法律，并解释第二个功能；根据截图继续修复体验。
- 排查结果：最近失败 Run 的错误为 `BUDGET_EXCEEDED`，同一 Run 已累计 8 次工具调用；其中 4 次分析均发生在旧法源链路，反复返回 `AUTHORITY_REQUIRED`。当前 2 条官方来源本身为 effective/trusted/verified，按该案件法域日期可正常检索。
- 修改方案：新增只读法源目录接口，前端展开工作台时直接显示法源库状态和官方链接；把两个劳动功能改为明确的“快速金额估算”和“生成仲裁申请书”；翻译 Agent 状态和预算错误；来源阻断时禁用主流程重复执行，只保留专用同步重试。
- 实际改动：Agent Facade、Agent Router、前端数字人 API、案件工作台、阶段 3.4 测试、最新项目分析和本日志。
- 验证：前端 `npx tsc --noEmit` 通过；Python compileall 通过；阶段 1～3.4 相关测试 20/20 通过；法源目录测试确认 ready 且至少返回 2 条来源。
- 后续：需要重启后端加载新增目录接口。旧的 failed Run 不会复用，点击“重新开始新的分析任务”将创建新 Run；案件材料和确认事实保持不变。

## 2026-07-13 21:56:55 +08:00

- 会话 ID：`019f5b92-52ca-7e82-be56-03aafa11c425`
- 分支/Git 状态：当前分支 `master`；修改前已跟踪文件无未提交变化，保留 `flask_app/evals/`、`migrations/`、`tests/`、用户上传 DOCX、前端工作台、outputs 和架构图等既有未跟踪内容。
- 用户请求：在 Agent 框架基本完成后，继续完善生产级法律内容和运行保障。
- 修改前阅读：`PROJECT_CONTEXT_RULES.md`、`PROJECT_MODIFICATION_RULES.md`、`raw/多法域数字人法律Agent总体规划.md`、最新项目分析、阶段 3.4 相关历史，以及当前 Provider/Importer/Authority Service、Facade、Runtime、ToolExecutor、Verifier、数据库模型、迁移和测试。
- 修改思路：保留现有 LangGraph 确定性工作流，不增加自主性；先消除“内置摘要被标成官网已验证”的信任缺口，再补来源变更阻断、Run 并发租约、超时不确定性和数据库配置治理。
- 具体方案：官方 HTTPS HTML/PDF 下载与条款精确抽取；同步批次和原始快照；首次/同内容/变更三种版本状态；七天新鲜度；失败关闭；Matter 创建锁和 Run 执行锁；工具超时禁止自动重试；自然年时效；`DATABASE_URL` 与 Alembic 单一结构管理。
- 实际改动：`.env.example`、`flask_app/app.py`、`core/config.py`、`core/database.py`、Agent Facade、法源 Provider/Importer/Service、劳动规则、Runtime persistence/locks/executor/labor_runtime/verifier、Agent/法源模型、`20260713_0003` 迁移、阶段 3.4/3.5 测试、总体规划和最新项目分析。
- 验证：Anaconda Python compileall 通过；无数据库专项 6/6 通过；Alembic head 为 `20260713_0003`；`20260713_0002:head --sql` 通过；`git diff --check` 通过。真实官网访问确认官方站点在当前代理/TLS环境存在间歇性连接失败，系统按设计失败关闭。
- 风险与后续：源码凭据已移除后，必须先在本地 `.env` 配置 `DATABASE_URL`，再执行实库 `alembic upgrade head` 和完整 PostgreSQL 回归；首批新官网版本若与旧内置版本不同会进入 `review_required`，需内部人工复核后启用。完整欠薪/解除/补偿规则、真实脱敏金标、定时任务/告警、Outbox 消费、身份权限和长期压测仍属于阶段 3.5 后续批次。

## 2026-07-14 01:04:20 +08:00

- 会话 ID：`019f5bcb-109a-7561-ad48-016e11c95730`
- 用户请求：分析数字人聊天编解码错误、案件“请求参数格式错误”和历史记录消失，并完成修复。
- 修改前检查：重新阅读项目上下文、修改规则、数字人方案、多法域规划、最新分析和相关历史；检查当前 Git 状态并完整保留阶段 3.5、测试、迁移、上传文档、工作台与 outputs 等既有改动。
- 根因：`DATABASE_URL` 指向的专用 PostgreSQL 运行账号不存在；数据库返回的本地化认证错误又被驱动按 UTF-8 解码，形成 `UnicodeDecodeError`。该异常继承 `ValueError`，Agent Router 因捕获顺序将其误报为参数错误；前端列表加载同时静默吞错，造成记录像被删除。
- 数据恢复：记录实际未丢失。为现有配置补建非超级用户运行账号并授予业务运行权限，不修改、不输出 `.env`；实库从 `20260713_0002` 非破坏升级到 `20260713_0003`。当前匿名客户端核对为 4 条会话、20 条消息、7 条案件记录。
- 代码修复：数字人及 Agent Router 将数据库异常统一转换为安全的 `503 DATABASE_UNAVAILABLE`；修正重置会话异常分支；前端历史与案件列表区分“加载失败”和“空记录”并支持重试；Loguru 关闭 `diagnose`，避免后续异常日志展开局部敏感变量。没有修改数字人窗口尺寸或双栏布局。
- 验证：配置运行账号连接成功；会话 API 返回 4 条、案件 API 返回 7 条；临时会话聊天成功并已清理；实库 Alembic 为 `20260713_0003`；前端 `npx tsc --noEmit` 通过；数字人故障回归及阶段 0/2/3.5 回归共 12 项通过。
- 风险与后续：旧日志可能已含历史异常上下文，后续应轮换数据库凭据并按运维策略清理受控日志；生产环境继续使用独立迁移账号执行 DDL，运行账号只保留业务运行权限。

## 2026-07-16 02:12:40 +08:00

- 会话 ID：`019f66aa-b826-7f01-a8de-b93ef323043f`
- 分支/Git 状态：当前分支 `master`；修改前工作树已有大量 Agent、配置、前端、测试、迁移、上传材料和图件改动，本次全部保留，仅增量修改 Agent 规划与架构文档及目标图件。
- 用户请求：参考讨论方案，确定方案 C 的最终法律 Agent 框架和完整执行流程，并更新项目中对应的 Agent 文档。
- 修改前阅读：`CLAUDE.md`、`PROJECT_CONTEXT_RULES.md`、`PROJECT_MODIFICATION_RULES.md`、`raw/多法域数字人法律Agent总体规划.md`、当前/目标 Agent Mermaid 图、`flask_app/legal_agent_system/analyse-agents.md`、`newModify/latest-project-analysis.md`、相关修改历史，以及当前 Planner、Labor Graph、ToolRegistry、ToolExecutor、Verifier、Runtime Schema 和 Facade 源码。
- 修改思路：明确区分当前实现与长期目标；当前劳动三步流程继续作为兼容基线，最终采用一套全局 Runtime Graph，通过 Capability Registry 加载 Domain Package、PlanTemplate、工具和验证策略，每次 Run 生成不可静默修改的 Plan revision，特殊控制流程才允许使用 Subgraph。
- 具体方案：固化 `execute_step → observe_step → verify_step → decide_step` 单 Step 闭环；Verifier 拆为 Global/Domain/Task 三层且只返回报告，由 Decision Router 统一路由；补充模板/计划版本、跳过原因、重规划审计、工具元数据、Subgraph 准入和并行迁移顺序；新增阶段 3.6 作为方案 C 通用 Runtime 落地阶段。
- 实际改动：`raw/多法域数字人法律Agent总体规划.md`、`raw/目标Agent架构图.mmd`、`raw/目标Agent架构图.svg`、`raw/目标Agent架构图.png`、`raw/目标Agent架构图.excalidraw`、`flask_app/legal_agent_system/analyse-agents.md`、`newModify/latest-project-analysis.md`、本日志。
- 验证：使用离线 Mermaid/Excalidraw 渲染包成功生成目标图 SVG、PNG 和可编辑 Excalidraw，PNG 尺寸为 1950×2303 并完成视觉检查；检查目标架构关键术语、当前/目标边界、Markdown/Mermaid 代码块和 Git 差异；本次未修改业务代码、接口或数据库，因此不运行后端/前端测试。
- 风险与后续：方案 C 当前只是已确认并写入文档的目标架构，Capability Registry、通用 Runtime Graph、Observation/Decision 节点、多模板和新 Plan revision 数据仍未实现；实施时必须保留现有入口并分领域迁移，不能将目标文档对外描述为当前已完成能力。

## 2026-07-16 02:38:10 +08:00

- 会话 ID：`019f6703-dccf-7a10-825b-73928bbebd43`；关联架构决策会话 `019f66aa-b826-7f01-a8de-b93ef323043f`。
- 分支/Git 状态：当前分支 `master`；修改前已有 Agent 文档、前端工作台、测试、迁移、上传材料、outputs 和架构图等大量已修改/未跟踪内容，本次保留并仅增量修改阶段 3.6 相关文件。
- 用户请求：跳过阶段 3.5 剩余的生产可信化与运行保障，直接实现阶段 3.6“方案 C 通用 Runtime 与能力注册”。
- 修改前阅读：`CLAUDE.md`、项目上下文/修改规则、`raw/多法域数字人法律Agent总体规划.md`、`newModify/latest-project-analysis.md`、关联会话历史记录、`analyse-agents.md`，以及当前 Facade、劳动 Graph/Runtime、Planner、ToolRegistry/Executor、Verifier、Persistence、数据库模型、迁移、Router、前端契约和测试源码。
- 修改思路：保留旧 HTTP/Facade 入口和数据字段，以并行兼容方式新增唯一通用 Runtime；领域包只提供声明式模板和工具/验证声明，不掌握 Run 状态；Verifier 只报告，Decision Router 唯一路由；计划变化只追加 revision。
- 具体方案：新增 `capabilities/` 契约、注册中心与模板 Planner；新增中国劳动 Domain Package 和仲裁申请/咨询/案件分析三模板；新增 `CapabilityRuntimeGraph` 的 select/execute/observe/verify/decide 单步循环及通用用例层；扩展 Plan/Step 审计字段与 `20260716_0004` 非破坏迁移；旧 `cn_labor_dispute` 映射仲裁模板，原路径支持可选 `task_type` 并新增能力查询 API；同步前端运行快照类型。
- 实际改动：新增 `legal_agent_system/capabilities/`、`domains/labor/`、`runtime/capability_graph.py`、`capability_runtime.py`、`decision_router.py`、迁移 `20260716_0004` 和阶段 3.6 测试；修改 Facade、Runtime schemas/enums/persistence/verifier、劳动工具、Agent/Step 模型、Router、前端 API 类型、总体规划、Agent 分析和最新项目分析。
- 验证：Python compileall 通过；Alembic 从 `20260713_0003` 升级并确认 `20260716_0004 (head)`；阶段 3.1/3.2/3.6 共 10 个相关用例通过；前端 `npx tsc --noEmit` 通过；`git diff --check` 通过。全量 30 个后端用例中 28 个通过，阶段 0 因沙箱禁止 Loguru 多进程管道、阶段 3.4 fixture 因数据库残留官方快照撞唯一键失败，均未修改相关代码或删除现有数据。
- 风险与后续：当前只完成劳动领域多模板，其他领域和第二法域尚未接入；阶段 3.5 的法源复核、监控、权限和长期压测仍未完成；旧 `LaborDisputeGraph` 暂留兼容，待新 Runtime 生产稳定后再单独评估移除。

## 2026-07-16 数字人启动恢复与目录说明

- 用户请求：为 `flask_app/legal_agent_system` 生成易读的文件说明文档，并排查截图中历史会话、案件记录均提示“数字人服务暂时不可用”的前端故障。
- 修改前检查：重新阅读仓库协作规则、总体规划、最新项目分析和相关修改历史；检查 Git 工作树并保留阶段 3.6、前端、测试、迁移、上传材料和图件等既有改动；核对数字人前端错误映射、后端端口、应用启动链路及 Agent 全目录源码。
- 根因：前端两个读取请求均因 8001 后端未监听失败。应用启动先在 Loguru `enqueue=True` 创建多进程队列时遇 Windows `PermissionError`；修复后又被主入口未使用的 FastAPI 旧 WebSocket Router 导入阻断。
- 实际改动：`core/logger.py` 在异步日志队列不可用时同步降级；`app.py` 移除未使用的 `courtroom_websocket` Router 导入，实际 Flask-Sock 路由不变；新增 `legal_agent_system/README.md`，并从详细分析文档交叉链接；同步更新最新项目分析和本日志。
- 验证：应用导入和服务初始化成功；后端已在 `127.0.0.1:8001` 启动；`/api/health`、`/api/digital-human/sessions`、`/api/digital-human/agent/matters` 均返回 HTTP 200。阶段 0、数据库故障和阶段 3.6 专项共 5 个测试通过；Python compileall、前端 `npx tsc --noEmit`、README 本地链接检查和 `git diff --check` 通过。
- 兼容说明：OCR 可选依赖仍输出 NumPy/pyarrow 二进制兼容警告，但异常已被旧纠纷 Router 隔离，不影响数字人基础服务；本次未修改用户数据、数据库结构或前端布局。

## 2026-07-16 Agent README 重构

- 用户反馈：原 README 内容过多，重点不清，流程表示不准确；需要优先说明每个包、每个文件以及真实函数调用关系。
- 实际改动：重写 `legal_agent_system/README.md`，删除背景性长说明，按“包职责、逐文件索引、函数调用、新代码位置”组织；基于当前 Facade、CapabilityRuntime 和 CapabilityRuntimeGraph 源码重新绘制包关系图与函数调用图。
- 图件：新增包关系、入口函数调用、Runtime 单步循环三组可编辑图件。将原本过高且长函数名断行的单图拆开；Mermaid 源文件作为单一事实源，README 引用渲染后的 SVG，避免 Markdown 环境直接解析复杂 Mermaid 时出现布局差异。
- 验证：三张图均完成离线渲染和视觉检查；SVG 可解析、Excalidraw JSON 有效、PNG 已生成；README 本地链接检查与 `git diff --check` 通过。

## 2026-07-16 10:19:42 +08:00

- 会话 ID：`019f6703-dccf-7a10-825b-73928bbebd43`。
- 分支/Git 状态：当前分支 `master`；工作树已有阶段 3.6、前端、测试、迁移、上传材料和图件改动，本次全部保留，仅新增数据库表说明并追加本记录。
- 用户请求：统计项目初始到当前新增了多少张表、每张表对应什么，并将清单放入 `flask_app/models`。
- 修改前阅读：`CLAUDE.md`、项目上下文/修改规则、`raw/项目解析报告.md` 的数据库章节、最新项目分析、相关修改历史、初始 `sql/public.sql`、当前 ORM、Agent 扩展模型、Alembic 迁移和实际 PostgreSQL `information_schema`。
- 修改思路：不只统计 ORM；以初始 SQL 快照和当前实库表名做差集，同时用 ORM/迁移核对新增表职责，避免漏掉 SQL-only 历史表和 Alembic 管理表。
- 具体方案：记录初始 54、当前 77、净新增 23；按数字人聊天、Agent Runtime、材料/法域/法源、劳动纠纷、版本化可信运行、迁移管理分组说明新增表。
- 实际改动：新增 `flask_app/models/数据库表新增清单.md`；追加本修改记录。
- 验证：初始 SQL 为 54 张、当前实库为 77 张，差集 23 张与文档逐表清单完全一致；Markdown 清单计数和 `git diff --check` 通过。
- 风险与后续：统计基线是仓库现有 `sql/public.sql`，不是 Git 最早历史提交；若以后替换初始 SQL 快照，应重新计算差集。

## 2026-07-16 15:38:05 +08:00

- 会话 ID：`019f6703-dccf-7a10-825b-73928bbebd43`。
- 分支/Git 状态：当前分支 `master`；工作树已有阶段 3.6、前端、测试、迁移、上传材料和图件等改动，本次仅增量修改 Agent 入口、能力解析、Graph、相关测试与架构文档。
- 用户请求：当前 Agent 代码不利于分析和维护，按已讨论方向统一入口、减少重复解析并明确 Runtime/Graph 职责。
- 修改前阅读：`CLAUDE.md`、项目上下文/修改规则、阶段 3.6 总体规划、最新项目分析、相关修改历史，以及 Router、Facade、Capability Registry、CapabilityRuntime、CapabilityRuntimeGraph、Repository 和阶段 3.1/3.2/3.6 测试源码。
- 修改思路：保留现有 HTTP 路径和 Facade 旧方法签名，避免破坏前端；新代码统一调用通用任务入口；能力路由只在 Runtime 用例层执行一次，Graph 不再同时承担任务解析。
- 具体方案：新增 `Facade/CapabilityRuntime.start_task` 与 `continue_task`；旧劳动命名方法保留为兼容包装；`resolve()` 返回带字段名且兼容元组解包的 `ResolvedCapability`；Runtime 将领域/模板绑定并审计到 Run；移除 Graph 的 `route_task`；未绑定 Run 直接调用 Graph 时返回明确的 `CAPABILITY_NOT_RESOLVED`。
- 实际改动：修改能力注册、Runtime、Graph、Facade、数字人 Agent Router 和阶段 3.2/3.6 测试；同步更新 README、详细 Agent 分析、总体规划、最新项目分析，以及入口/Runtime 两组 Mermaid、SVG、PNG、Excalidraw 图件。
- 验证：Python compileall 通过；阶段 3.1/3.2/3.6 共 12 个用例通过；应用导入成功并注册 200 条路由；两组 SVG/XML、Excalidraw JSON、README 本地链接和 `git diff --check` 通过；图件已离线渲染并完成视觉检查。
- 风险与后续：HTTP 路径和返回契约未变化；旧劳动命名方法及 `labor_runtime` 兼容别名暂时保留。通用 Graph 内部仍直接依赖劳动上下文服务，后续接入第二领域前应再抽取 Domain Runtime Adapter；应用导入仍输出既有 NumPy/pyarrow、OCR/PDF 可选依赖警告，本次未修改该环境问题。

## 2026-07-16 20:25:00 +08:00

- 会话 ID：`019f6703-dccf-7a10-825b-73928bbebd43`；关联架构决策会话 `019f66aa-b826-7f01-a8de-b93ef323043f`。
- 用户请求：执行阶段 3.6 的“领域解耦与旧架构清理”，并确保代码规范、便于后续维护和交接。
- 修改前检查：重新读取仓库规则、总体规划、最新分析、相关历史和当前源码，检查并保留工作树中已有的阶段 3.6、前端、迁移、测试、上传材料和图件改动。
- 架构改动：新增 `DomainRuntimeAdapter` 与 `ContextAssessment`；`CapabilityRegistry` 成对注册 `DomainPackage + Adapter`；通用 Runtime/Graph 只依赖 Adapter 契约。劳动上下文、计划定制、工具参数、法域、继续动作和劳动校验下沉到 `domains/labor/`。
- 旧架构清理：阶段 1 模拟摘要迁入 `domains/mock/` 普通能力包，旧 HTTP 方法仅保留 Facade 薄包装；删除 `runtime/runtime.py`、`graph.py`、`labor_runtime.py`、`labor_graph.py`、`planner.py`，项目只保留 `CapabilityRuntime + CapabilityRuntimeGraph` 一套执行内核。
- 可维护性：通用 `TemplatePlanBuilder` 移除劳动争议名称定制；`LayeredVerifier` 只负责全局校验和领域报告聚合；新增架构边界测试，禁止旧内核文件回归及 Runtime 直接导入领域 Service。README、详细分析、总体规划、最新分析和包关系图同步更新。
- 验证：Python compileall 通过；阶段 1、3.2、3.6 和架构边界共 14 个专项测试通过；数字人阶段全量 32 个用例中 31 个通过，唯一失败是既有官方来源残留快照唯一键 fixture 问题；应用导入成功并注册 200 条路由；`git diff --check` 通过。包关系 Mermaid 已离线生成 SVG、PNG、Excalidraw，并完成视觉检查。
- 风险与后续：真实法律领域当前仍只有中国劳动，`domains/mock` 只承担旧阶段 1 兼容，不能算第二法律领域；阶段 3.5 的法源复核、监控、权限和长期运行保障仍按用户要求暂缓。后续新增领域必须走 `DomainPackage + DomainRuntimeAdapter + 领域评测`，不得复制 Graph。
## 2026-07-16 21:35:00 +08:00

- 会话 ID：`019f6b12-00d7-72e2-9760-29e31a326a40`。
- 分支/Git 状态：当前分支 `master`；修改前已有方案 C、前端工作台、测试、迁移、上传材料和图件等大量未提交改动，本次全部保留，仅增量修改法源治理、官方来源、相关前端状态、测试和文档。
- 用户请求：在方案 C 已落地后优先完善法源闭环。
- 修改前阅读：`CLAUDE.md`、项目上下文/修改规则、`raw/多法域数字人法律Agent总体规划.md`、最新分析、法源相关历史，以及当前 Provider、Importer、Authority Service、Facade、模型、迁移、Router、前端法源状态和测试。
- 修改思路：不继续扩 Runtime；先补最小生产级法源治理，保持普通 HTTP/Agent 无写权限，官网正文变化必须由法律专业人员复核，所有不完整来源继续失败关闭。
- 具体方案：新增同步/健康/待复核/复核 CLI；新增复核决策审计表及同步触发字段；健康状态统计覆盖、新鲜度、缺失、失败和待复核；逐来源同步允许部分进展但整体门禁不放松；修复跨批次快照约束和官网条文截断；扩充劳动合同法与劳动法官方条款。
- 实际改动：`app.py`、`authority_cli.py`、Facade、Authority Provider/Importer/Governance、Agent 法源模型、`20260716_0005`～`0007` 迁移、法源治理/Provider 测试、前端 API 契约和法源状态展示、Agent README、总体规划、最新项目分析及本日志。
- 官方来源核对：只采用国家机关官方页面；新增市场监管总局《劳动合同法》《劳动法》页面及国家税务总局法规库备用页，没有加入商业法律网站或内置法条降级。
- 验证：Python compileall 通过；Alembic 当前为 `20260716_0007 (head)`，增量离线 SQL 通过；数字人 Agent 全量 39/39 测试通过；前端 `npx tsc --noEmit` 和 `git diff --check` 通过；CLI help、health 和真实官网同步均实际运行。
- 真实同步结果：四组来源均已成功抓取。新增《劳动合同法》《劳动法》实体条款为 `verified`；两个时效来源因从历史版本切换到官网正文进入 `review_required`，健康状态为 `degraded`。未擅自替代法律专业人员批准，因此依赖时效来源的确定性结论继续安全阻断。
- 风险与后续：需要法律专业人员运行 `authority pending` 对照候选/旧版正文，再用 `authority review` 填写依据并批准或驳回；部署环境仍需实际配置定时任务和告警接收端。应用 CLI 启动会输出既有 NumPy/pyarrow 与 OCR 可选依赖警告，不影响法源命令执行，但应另行治理依赖环境。

## 2026-07-16 21:50:00 +08:00

- 用户请求：解释 CLI，并参考常见 Agent 架构画一张更简单、易理解的项目框架图。
- 设计取舍：参考 LangGraph 官方文档中“步骤、状态、人工介入”的表达方式，但不复制其工程细节；主图仅保留用户、法律 Agent、能力包、工具与官方法源、安全校验、结果六个节点。
- 实际改动：新增 `diagrams/legal-agent-simple.mmd`、`.svg`、`.png`、`.excalidraw` 四种图件；没有修改运行时代码、接口、数据模型或现有复杂架构图。
- 验证：完成离线渲染和视觉检查；Mermaid 中文经 UTF-8 传输，SVG 可解析且中文标签完整，Excalidraw JSON 有效，PNG 已生成。

## 2026-07-16 22:05:00 +08:00

- 用户纠正：上一张图是业务流程，不是期望的 Agent 框架；要求采用网上常见、直观的 Agent 架构表达。
- 参考方式：检索常见 Agent Anatomy/Runtime 图，采用“中心 Agent 核心 + 能力、记忆、工具、知识、安全护栏”的中心辐射结构，并映射到本项目实际能力。
- 实际改动：新增 `diagrams/legal-agent-internal-simple.mmd`、`.svg`、`.png`、`.excalidraw`；图中不展示源码调用顺序，只展示 Agent 的核心组成和边界。
- 验证：完成离线渲染与视觉检查；SVG 中文标签正常，Excalidraw JSON 有效，PNG 已生成；未修改业务代码、接口或数据结构。
- 后续校正：明确 `Verifier` 只是安全护栏的一部分，护栏还包含工具策略和人工审批；将法律知识改为“可信法律知识库”，并补画“白名单官方网站 -> 法源治理 CLI -> 已同步、已审核法源”的后台治理链路，避免误解为 Agent 每次运行都通过 CLI 上网检索。

## 2026-07-16 22:40:00 +08:00

- 会话 ID：`019f6b12-00d7-72e2-9760-29e31a326a40`。
- 分支/Git 状态：当前分支 `master`；工作树已有 Agent、前端、迁移、测试、法源治理和图件等未提交改动，本次全部保留。
- 用户请求：阅读当前法律 Agent 源码，按整体流程、核心模块、劳动欠薪案例、单步循环和源码对应关系整理成项目文档。
- 修改前阅读：仓库协作规则、Agent 总体规划、最新项目分析、相关修改历史，以及 Router、Facade、CapabilityRuntime、CapabilityRuntimeGraph、能力模板、领域 Adapter、工具执行器、Observer 节点、Verifier、DecisionRouter、Repository、劳动规则与专项测试。
- 修改思路：严格区分普通数字人聊天与可执行 Agent Runtime；以当前源码和阶段 3.6 测试为依据，不把目标架构或通用 Agent 理论写成已实现能力。
- 实际改动：新增 `flask_app/legal_agent_system/实际Agent架构与运行流程.md`；记录八节点主流程、核心模块输入输出、欠薪咨询真实执行条件、单 Step 循环、预算边界、源码对应表及未实现项。
- 验证：核对文档中的节点名、模板步骤、状态分支、默认预算和源码路径；未修改业务代码、接口、数据结构或运行配置。
- 风险与后续：当前普通聊天不会自动启动 Agent，Planner 是确定性模板构建器，且没有独立自然语言 Response Generator；文档已明确标注这些边界。

## 2026-07-21 11:29:19 +08:00

- 会话 ID：`019f8287-4627-74b2-bd42-1d59748e1ba1`。
- 分支/Git 状态：当前分支 `master`；修改前已有 `CLAUDE.md`、Agent 图件、迁移、测试、上传材料、数字人工作台和 `outputs/` 等未跟踪内容，本次全部保留，只修改四份规划/解析文档。
- 用户请求：总结已讨论的劳动用工垂直定位，说明 LangGraph 与 Plan 如何按不同问题处理，并更新相关文档和后续规划。
- 修改前阅读：`CLAUDE.md`、`PROJECT_CONTEXT_RULES.md`、`PROJECT_MODIFICATION_RULES.md`、`raw/项目解析报告.md`、`raw/多法域数字人法律Agent总体规划.md`、`raw/数字人智能助手实现方案.md`、`raw/AI前端问题与Agent架构分析.md`、`newModify/latest-project-analysis.md`、相关修改历史；并重新核对 `facade.py`、劳动 Domain Package、`CapabilityRuntimeGraph`、`TemplatePlanBuilder`、数字人 Service 和实际 Agent 流程文档。
- 修改思路：保持“一套固定 Runtime Graph + 劳动 Domain Package + 受控组合 Plan”的架构边界；把大学生实习、兼职和初入职场青年定义为第一批产品入口，而不是新技术 Domain；严格区分当前已实现能力和下一阶段规划。
- 具体方案：总体规划增加劳动用工垂直定位、数字人/Agent 分工、LangGraph 与 Plan 组合规则，以及阶段 3.7“劳动用工深化与数字人入口融合”；实际流程文档补充复合劳动问题的主模板、争议标签、步骤去重和 Plan revision 策略；最新项目解析同步记录产品决策与开发优先级。
- 实际改动：`raw/多法域数字人法律Agent总体规划.md`、`flask_app/legal_agent_system/实际Agent架构与运行流程.md`、`newModify/latest-project-analysis.md`、`newModify/modification-log.md`。
- 验证：仅修改 Markdown 文档；核对当前源码仍只有劳动咨询、劳动案件分析、劳动仲裁申请三个真实劳动模板，普通数字人聊天仍不会自动启动 Agent；随后执行关键词检查、`git diff --check` 和限定文件差异复核。
- 风险与后续：劳动关系判断、欠薪/解除/补偿模板、聊天转 Agent、组合式 Plan 和基础语音均是规划能力，尚未实现；对外介绍必须继续与当前源码能力分开。下一步应先形成阶段 3.7A 的详细实现方案和验收用例，再修改代码。

## 2026-07-21 14:06:20 +08:00

- 会话 ID：`019f832d-788d-7080-85db-7d503fa11450`。
- 分支/Git 状态：当前分支 `master`；修改前已有规划文档、Agent 图件、迁移、测试、上传材料、数字人工作台和 `outputs/` 等大量未提交/未跟踪内容，本次全部保留，仅增量修改阶段 3.7A 相关文件及规定文档。
- 用户请求：暂缓阶段 3.5 的身份、告警、加密和长期运行工作，改为实施阶段 3.7A，增加劳动案件分流和劳动关系判断，优先覆盖实习、兼职和初入职场。
- 修改前阅读：`CLAUDE.md`、项目上下文/修改规则、`raw/多法域数字人法律Agent总体规划.md`、最新项目分析、阶段 3.5/3.6/3.7 相关历史，以及当前劳动 Schema/Service/Domain Package/Adapter/Verifier、Capability Runtime、工具、Router、Facade、模型、迁移和测试。
- 修改思路：不修改通用 Graph，不因学生身份、协议名称或欠薪关键词直接认定劳动关系；用独立、可解释、版本化的领域分流服务生成初筛结果，再以第四个劳动 PlanTemplate 接入现有 Runtime。
- 具体方案：新增五类分流、劳动关系倾向、缺失事实、风险和推荐任务契约；按主体资格、有偿劳动、劳动管理、业务组成和就业目的综合初筛；高风险和非劳动问题失败关闭；新增分流表、API、工具、模板、Adapter 分支和领域 Verifier；覆盖学校实习、勤工助学、学生兼职、普通兼职、信息不足和高风险用例。
- 实际改动：新增职责分离的 `labor_disputes/triage_schemas.py`、`triage_rules.py`、`triage.py`，以及 `tools/labor_triage_tools.py`、迁移 `20260721_0008` 和阶段 3.7A 测试；更新模型、劳动 Domain Package/Adapter/Verifier、Capability Adapter 契约、Runtime 调用、Facade、Router、README、阶段 3.6 测试、总体规划和最新分析。另将阶段 3.4 测试 Provider 的抓取时间改为运行时当前时间，避免七天新鲜度门禁造成日历型测试失败。
- 验证：Python compileall 通过；阶段 3.6+3.7A 专项 11/11 通过；完整数字人 Agent 回归 44/44 通过；本地 PostgreSQL 已从 `20260716_0007` 非破坏性升级到 `20260721_0008 (head)`。
- 风险与后续：当前为结构化初筛，不是最终劳动关系法律结论；尚未为自然语言聊天自动提取全部分流字段，也未自动启动推荐任务。阶段 3.5 法源复核/权限/告警仍按用户决定暂缓；下一步可进入 3.7B 的欠薪、解除、补偿模板与受控组合 Plan，或先做 3.7D 的聊天入口融合。

## 2026-07-21 16:24:10 +08:00

- 会话 ID：`019f832d-788d-7080-85db-7d503fa11450`。
- 分支/Git 状态：当前分支 `master`；修改前已有阶段 3.7A、迁移、测试、工作台、图件、上传材料和输出物等未提交或未跟踪内容，本次全部保留，仅增量修改分流编排闭环相关代码、测试与规定文档。
- 用户请求：执行阶段 3.7A.1，打通 `Chat Session ↔ Matter ↔ Triage Result ↔ Agent Run ↔ DigitalHumanMatterWorkspace`，让五类分流真正决定后续 Runtime 行为。
- 修改前阅读：`CLAUDE.md`、项目上下文/修改规则、总体规划、最新项目分析、阶段 3.6/3.7A 历史，以及当前聊天 Store、分流 Hook/Card、Workspace、API、Matter Service、Facade、Router、Capability Runtime、劳动 Adapter 和专项测试。
- 修改思路：不复制 Runtime、不新增 3.7B 模板；把 Matter/Triage/Run 提升到现有 Zustand Store，后端只补齐 Matter 已有 `session_id` 外键的安全写入；前端严格校验后端推荐任务后调用既有 Runtime。
- 具体方案：数字人会话创建的 Matter 持久绑定并校验 `session_id`；Store 按会话保存当前 Matter/Run 标识并从后端恢复快照；简单咨询、关系判断、正式纠纷分别启动 `labor_consultation`、`labor_relationship_assessment`、`labor_case_analysis`；缺失事实不启动 Run，高风险和非劳动保持阻断；Workspace 共用当前 Matter/Run，法域确认和事实补充继续同一 Run，并展示分流、缺失事实、状态和最终结果入口。
- 实际改动：Matter Service/Facade/Router 的可选会话绑定；前端 API 契约、数字人 Store、分流编排 Hook/Card、Chat 与 Workspace；阶段 3.7A 测试；总体规划、最新分析和本日志。
- 验证：阶段 3.6+3.7A 专项 12/12 通过；完整数字人测试 45/45 通过；前端 `npx tsc --noEmit` 通过；在隔离临时目录中完成 Next.js 生产构建，37 个静态页面全部生成。正式 `.next` 仍由正在运行的开发服务占用，因此未停止用户服务，隔离构建完成后临时目录已清理。
- 风险与后续：劳动场景入口仍采用前端保守关键词和有限结构化提取；浏览器只保存每个会话当前的一组 Matter/Run 映射，后端尚无“按 Matter 查询全部历史 Run”的恢复接口；高风险只有人工复核标记，没有真实人工服务通道；阶段 3.7B 未进入。

## 2026-07-21 16:45:00 +08:00

- 会话 ID：当前环境未暴露；本地追踪标识 `ai-workflow-20260721`。
- 分支/Git 状态：当前分支 `master`；修改前工作树已有劳动分流、前端工作台、迁移、测试、图件、上传材料和输出物等未提交改动，本次全部保留。
- 用户请求：仅整理 Markdown 协作规则和工作流文档，新增 `AI_WORKFLOW/` 六种模式与初始化状态；禁止修改业务代码、配置、数据库或前后端源码。
- 修改前阅读：`AGENTS.md`、`CLAUDE.md`、`PROJECT_CONTEXT_RULES.md`、`PROJECT_MODIFICATION_RULES.md`、`raw/多法域数字人法律Agent总体规划.md`、`flask_app/legal_agent_system/实际Agent架构与运行流程.md`、`newModify/latest-project-analysis.md`、相关修改历史，以及当前 Facade、Router、前端 Store 与劳动分流 Hook。
- 修改思路：保留既有权威资料位置，建立轻量工作流面板；当前任务和下一步允许覆盖，架构决策与阶段记忆保持可检索且不复制完整项目分析或历史。
- 具体方案：在 `AGENTS.md` 增加清晰导航与默认“开发者记忆卡”交付规则；新增 `AI_WORKFLOW/README.md`、四份状态文档及 FEATURE、BUGFIX、REVIEW、LEARN、ARCHITECTURE、FRONTEND 六种模式；按当前 3.7A/3.7A.1 源码状态初始化内容。
- 实际改动：仅修改 `AGENTS.md`、新增 `AI_WORKFLOW/` 下 11 个 Markdown 文件，并追加本记录；未修改业务代码、配置、数据库、迁移或前后端源码。
- 验证：核对新增文件结构、Markdown 标题和链接引用；检查 `git diff --check`；复核变更文件均为允许范围内的 Markdown。
- 风险与后续：工作流文件是协作导航而非真相副本；代码任务仍需以当前源码和 `newModify/latest-project-analysis.md` 为准，并继续按规则写入完整修改历史。

## 2026-07-21 18:50:00 +08:00

- 会话 ID：当前环境未暴露；本地追踪标识 `ai-workflow-export-20260721`。
- 分支/Git 状态：当前分支 `master`；工作树已有业务、文档、迁移、测试和图件改动，本次全部保留。
- 用户请求：将协作体系按既定层级复制到 `D:\ProfileManage`，作为将来可复用或迁移到其他项目的资料。
- 修改前阅读：`AGENTS.md`、`PROJECT_MODIFICATION_RULES.md`、当前 Git 状态与目标目录状态。
- 修改思路：仅导出协作规则、工作流、当前项目状态、完整修改历史与长期架构资料；不复制业务源码、配置、数据库或敏感信息。
- 具体方案：建立 `D:\ProfileManage\YYS-Law-AI-Collaboration-Template`，保留 `AGENTS.md`、`CLAUDE.md`、`AI_WORKFLOW/`、`newModify/` 指定两份文档及完整 `raw/` 的相对层级。
- 实际改动：追加本记录；外部资料副本不属于当前 Git 仓库。
- 验证：复制后核对目标文件树、文件计数和关键 Markdown 文件存在性。
- 风险与后续：该副本包含当前项目的状态与历史，迁用到新项目时应保留规则与模式，替换项目状态、历史和 `raw/` 架构资料。

## 2026-07-21 21:24:29 +08:00

- 会话 ID：`019f84d2-0fd1-7812-85f9-027376a7c162`。
- 分支/Git 状态：当前分支 `master`；工作树已有业务、迁移、测试、前端、图件和输出物等未提交或未跟踪改动，本次全部保留，仅修改 `AI_WORKFLOW/` 与本日志中的 Markdown。
- 用户请求：进入 FEATURE 模式并执行 `CURRENT_TASK`。
- 修改前阅读：`AGENTS.md`、`CLAUDE.md`、项目上下文/修改规则、`AI_WORKFLOW` 入口、当前任务、下一步、FEATURE 模式、关键决策、开发者记忆卡、总体规划、最新项目分析、相关修改历史和当前 Git 状态。
- 修改思路：当前任务限定为协作体系整理，且六种模式、导航、决策和记忆卡已经落地；因此完成正式收尾并把唯一当前任务推进到已完成架构分析的阶段 3.7B，不越权修改业务代码。
- 具体方案：将 `CURRENT_TASK.md` 覆盖为 3.7B 的目标、范围、禁止项和验收；将 `NEXT_STEP.md` 更新为“3.7B 当前、3.7C 下一步”；补充组合式 Plan 的长期决策与 3.7B 接力定位。
- 实际改动：`AI_WORKFLOW/CURRENT_TASK.md`、`AI_WORKFLOW/NEXT_STEP.md`、`AI_WORKFLOW/DECISIONS.md`、`AI_WORKFLOW/DEVELOPER_MEMORY.md`、`newModify/modification-log.md`。
- 验证：核对六种模式文件、工作流标题和相对链接；执行限定范围 `git diff --check`；确认未修改业务代码、配置、数据库、迁移或前后端源码。
- 风险与后续：3.7B 现在是唯一当前任务，但业务实现仍未开始；下一次执行应按代码任务检查点重新核对脏工作树和真实源码，并保持唯一 Runtime Graph 边界。

## 2026-07-21 21:44:38 +08:00

- 会话 ID：`019f84d2-0fd1-7812-85f9-027376a7c162`。
- 分支/Git 状态：当前分支 `master`；修改前工作树已有阶段 3.7A/3.7A.1、前端工作台、迁移、测试、图件、上传材料和输出物等未提交或未跟踪改动，本次全部保留，仅增量修改 3.7B 核心模块、契约、测试和规定文档。
- 用户请求：进入 FEATURE 模式，按已确认的“主 PlanTemplate + dispute_tags + 白名单可选步骤”实现阶段 3.7B；不得复制 Runtime Graph，不得进入 3.7C。
- 修改前阅读：`AGENTS.md`、`CLAUDE.md`、项目上下文/修改规则、FEATURE 模式、`CURRENT_TASK.md`、`NEXT_STEP.md`、总体规划、实际 Agent 流程、最新项目分析、3.6/3.7A 相关历史，以及当前能力契约、Planner、Registry、劳动 Domain Package/Adapter/Verifier、劳动 Service/Tool、Runtime、持久化和专项测试。
- 修改思路：按交付目的保留 `labor_case_analysis` 与 `labor_arbitration_application` 两个主模板；欠薪、解除、经济补偿只作为模板内固定白名单步骤。Planner 只启用或跳过已声明步骤，Adapter 定制后由 Registry 再次核验，Runtime Graph 拓扑保持不变。
- 具体方案：新增三个稳定争议标签及中文归一化；新增三个只输出初步结果并保留人工复核标记的问题分析工具；公共证据、统一期限/法源分析、审批和草稿步骤去重；Plan 保存标签、组合版本和步骤触发标签；未知标签及插步、换工具、改依赖、削弱审批统一失败关闭；补充事实后在同一 Run 创建新 revision。
- 实际改动：能力契约/Planner/Registry；劳动 `package.py`、Adapter、Verifier、Facade、Schema、工具；新增 `labor_disputes/dispute_tags.py` 与 `issue_analysis.py`；Runtime 失败关闭、错误码和快照；前端快照类型；新增阶段 3.7B 测试并更新受模板版本影响的阶段 3.1/3.4 断言；同步 Agent README、实际流程、总体规划、最新项目分析与 `AI_WORKFLOW` 状态。
- 验证：系统默认 Python 因缺少 SQLAlchemy 未用于项目测试；改用项目既有 Anaconda Runtime。阶段 3.6+3.7A+3.7B 专项 16/16 通过；完整数字人 Agent 回归 49/49 通过；Python `compileall` 通过；前端 `npx tsc --noEmit` 通过；最终执行 `git diff --check` 和限定文件复核。
- 风险与后续：三个问题步骤当前是可审计的初步结构化分析，经济补偿沿用项目既有估算公式，尚未覆盖工资上限、完整解除规则或真实金标；这些属于 3.7C，本次明确未进入。未新增数据库表或列，因此无需 Alembic migration。

## 2026-07-21 22:10:00 +08:00

- 会话 ID：当前环境未暴露；本地追踪标识 `ai-workflow-handoff-fix-20260721`。
- 分支/Git 状态：当前分支 `master`；工作树已有阶段 3.7A/3.7A.1、业务、迁移、测试、前端和图件改动，本次全部保留，仅修改协作工作流 Markdown。
- 用户请求：修复 AI_WORKFLOW 的任务状态流转与模式交接，防止 ARCHITECTURE 分析目标被旧 CURRENT_TASK 截断；同步对应资料到 `D:\ProfileManage\HKC-Law-AI-Collaboration-Template`。
- 修改前阅读：仓库入口、硬约束、上下文/修改规则、AI_WORKFLOW 全部文件、总体规划、当前项目分析、相关修改历史、当前 Git 状态和外部模板目录。
- 修改思路：不创建第二套工作流；在既有导航、状态文件和六种模式中补上目标一致性、显式 Promote、任务状态语义、Architecture Handoff、Review 实物验收和结束路由。
- 具体方案：AGENTS 仅增加导航；README 定义状态、Promote、主状态流和常用指令；CURRENT_TASK 按完整字段重写且将 3.7B 标为 PLANNED；各模式加入最小的目标一致性和交接规则；DECISIONS 记录长期原则。
- 实际改动：仅修改 `AGENTS.md`、`AI_WORKFLOW/README.md`、`CURRENT_TASK.md`、`NEXT_STEP.md`、`DECISIONS.md`、六种模式文档，并追加本日志；未修改业务代码、配置、数据库、迁移、测试或 3.7B 实现。
- 规则级模拟：3.7B 分析与旧任务不一致时标记 CURRENT_TASK_MISMATCH；“方案确认并实施”先初始化 3.7B CURRENT_TASK 再进 FEATURE；若无 3.7B 业务代码，REVIEW 必须为 FAILED_REVIEW 并退回 FEATURE。
- 验证：检查必需状态、Promote、Architecture Handoff、FEATURE 启动检查和 REVIEW 未通过规则均存在；执行 Markdown 文件范围复核与 `git diff --check`。
- 风险与后续：流程规则依赖 Agent 严格遵守，非自动化状态机；3.7B 仍是 PLANNED，必须等用户明确确认实施后再改业务代码。

## 2026-07-21 23:00:00 +08:00

- 会话 ID：当前环境未暴露；本地追踪标识 `markdown-governance-20260721`。
- 分支/Git 状态：当前分支 `master`；工作树已有 3.7B 业务、测试、前端、迁移和图件改动，本次全部保留，仅治理 Markdown。
- 用户请求：统一协作体系、项目状态和规划资料，归档被替代资料，不修改任何业务代码。
- 修改前阅读：入口、硬约束、现有工作流、最新项目分析、总体规划、历史规则、相关历史日志、Markdown 引用与当前源码文件存在性。
- 发现：旧 PROJECT 规则仍被入口引用；CLAUDE 含旧 Runtime 和固定行数；状态流缺少 READY_FOR_ACCEPTANCE；最新解析同时存在“普通聊天未接入”和劳动入口已接入的歧义；三份 raw 文档已过时。
- 实际改动：收敛入口和硬约束；完善工作流状态、决策表、记忆卡和 LEARN；更新当前状态为 3.7B `VERIFYING`；修正最新解析与总体规划；将三份旧方案及两份 PROJECT 规则移至 `raw/archive/` 并标注状态。
- 验证：检查有效规则不再依赖 PROJECT 文件、旧 Runtime 不在当前规则中、归档资料带状态声明、3.7B/3.7A.1/3.7C 状态一致，并执行 `git diff --check`。
- 风险与后续：3.7B 尚待 REVIEW；archive 中历史描述可能与当前源码不同，只能用于演进追溯；工作流是语义规则，仍需要 Agent 遵守。

## 2026-07-21 23:20:00 +08:00

- 会话 ID：当前环境未暴露；本地追踪标识 `workflow-consolidation-20260721`。
- 分支/Git 状态：当前分支 `master`；已有业务、测试、迁移、前端和图件改动全部保留，本次只修改 Markdown 协作文件。
- 用户请求：集中工作流规则到 `AI_WORKFLOW/`，压缩根入口，合并 Mode，并支持自然语言自动路由和不满意后的最小返工。
- 修改前阅读：根入口、当前工作流、模式文件、状态文件、旧规则归档、Git 状态，以及 `.agents` / `.claude` 的只读目录检查。
- 实际改动：新增 `WORKFLOW.md`、`CODE_RULES.md`、`MODES.md`；将 AGENTS/CLAUDE 改为 Bootstrap；将六份 modes 文件合并并删除空目录；README 改为人类自然语言使用说明；修正归档资料的模式引用；追加本记录。
- 验证：检查无失效 `modes/` 引用、目录结构、Markdown 路径、`.agents`/`.claude` 未改动和 `git diff --check`。
- 风险与后续：自动路由是文档规则，仍依赖 Agent 解释用户意图；3.7B 当前状态未因本次整理推进。

## 2026-07-21 23:35:00 +08:00

- 会话 ID：当前环境未暴露；本地追踪标识 `workflow-intake-20260721`。
- 分支/Git 状态：当前分支 `master`；既有业务、测试、迁移、前端和图件改动全部保留，本次只修改 Markdown 工作流规则。
- 用户请求：在 WORKFLOW 中加入任务自动澄清，使自然语言需求可先调查、必要时少量提问、自动结构化 CURRENT_TASK 并选择 Mode。
- 修改前阅读：根 Bootstrap、README、WORKFLOW、MODES、CURRENT_TASK 和当前 Git 状态。
- 实际改动：在 `WORKFLOW.md` 新增 TASK INTAKE / CLARIFY 统一入口、调查优先、提问阈值与数量限制、低风险默认假设、自动任务结构化及与返工/架构的边界；README 增加无需完整 Prompt 的说明；MODES 补充前端已有视觉信息时直接实施规则。
- 验证：规则级检查五个 Intake 场景、关键词和 Markdown 差异检查；未修改业务代码或推进阶段。
- 风险与后续：澄清质量仍依赖 Agent 对上下文和风险的判断；本机制不替代高风险操作的用户确认。

## 2026-07-21 23:45:00 +08:00

- 会话 ID：当前环境未暴露；本地追踪标识 `learn-navigation-20260721`。
- 分支/Git 状态：工作树已有 3.7C 及其他用户业务改动，本次全部保留，仅修改工作流 Markdown。
- 用户请求：小幅完善 LEARN，不改变 MAP → TRACE → STOP → CHECK，补齐业务链、阅读顺序、上下游和真实 IDE 导航规则。
- 实际改动：更新 `AI_WORKFLOW/MODES.md` 的 LEARN 章节，明确完整业务链与实际阅读起点、极简上下游、Ctrl+B 与业务下一站的严格区别，以及每站输出和暂停要求；追加本记录。
- 验证：检查 MAP/TRACE/STOP/CHECK、当前位置、上游/下游和 Ctrl+B 限制均存在；未修改业务代码。
- 风险与后续：规则依赖实际符号引用核对，Agent 不应根据抽象业务流程臆造 IDE 跳转。

## 2026-07-21 21:46:00 +08:00（3.7B 最终验证补充）

- 会话 ID：`019f84d2-0fd1-7812-85f9-027376a7c162`。
- 分支/Git 状态：`master`；保留全部既有用户改动，3.7B 详细实施记录见本文件 `2026-07-21 21:44:38 +08:00`。
- 用户请求：完成阶段 3.7B 业务实现、测试和收尾，不进入后续阶段。
- 修改前阅读：同上述 3.7B 详细实施记录，并复核后续新增的 AI_WORKFLOW 交接规则。
- 修改思路：在最终交付前重新执行完整回归，并将任务状态停在 `IMPLEMENTED_AWAITING_REVIEW`。
- 具体方案：补强旧格式 Plan 快照兼容；复跑完整数字人 Agent 测试、TypeScript 检查和差异检查。
- 实际改动：`runtime/persistence.py` 兼容历史列表型 `plan_json`；AI_WORKFLOW 明确 3.7B 已实现待验收；未进入 3.7C。
- 验证：完整数字人 Agent 回归 49/49、`npx tsc --noEmit`、Python compileall、`git diff --check` 全部通过；仅有既有 CRLF 转换提示。
- 风险与后续：3.7B 等待 REVIEW 验收；实体规则深化继续保持暂缓。

## 2026-07-21 23:25:32 +08:00

- 会话 ID：当前环境未暴露；本地追踪标识 `stage37b-termination-date-fix-20260721`。
- 分支/Git 状态：当前分支 `master`；工作树已有 3.7B 业务、测试、前端、迁移、文档和图件等未提交或未跟踪改动，本次全部保留，仅增量修改解除事实建议、劳动表单、局部样式、专项测试和任务状态。
- 用户请求：修复材料已有解除日期，但 Runtime 仍提示缺少 `termination_date`，且步骤状态容易误解的问题。
- 根因：前端只采集入职日期和权利受损知悉日期；确定性材料建议没有提取解除日期/解除原因；采用建议时也未回填这两个字段。解除分析允许带缺失事实完成初步整理，而补偿步骤要求事实完整，因此页面同时出现 `completed` 与 `failed`。
- 实际改动：材料建议新增带原文出处的解除日期和解除原因提取；前端新增明确标注的入职、解除、知悉三个日期框及解除原因字段，并随新建/续跑 payload 提交；步骤文案区分“初步整理完成但仍缺事实”和“等待补充事实”；补充真实材料句式回归测试。
- 验证：Anaconda Runtime 下专项建议测试 1/1 通过；完整数字人 Agent 回归 49/49 通过；Python `py_compile` 通过；前端 `npx tsc --noEmit` 通过。
- 风险与后续：后端逻辑和类型验证已通过；日期标签和三列布局仍需用户在实际数字人窗口做视觉验收。未修改 Runtime Graph、数据库结构、法源、审批或人工复核边界。

## 2026-07-21 23:44:38 +08:00

- 会话 ID：当前环境未暴露；本地追踪标识 `stage37b-closeout-20260721`。
- 分支/Git 状态：当前分支 `master`；保留全部既有业务、测试、迁移、前端、文档和图件改动，本次仅修改阶段状态与交接 Markdown，未修改业务代码。
- 用户请求：进入 LEARN，确认当前阶段无问题，完成收尾并为下一阶段做准备。
- 验收依据：用户确认当前阶段无问题；3.7B 完整数字人 Agent 回归 49/49、解除事实专项测试、Python 编译和前端 TypeScript 检查均已通过。
- 实际改动：将 3.7B 标记为正式完成；把 3.7C 初始化为 `PLANNED`；同步 `CURRENT_TASK`、`NEXT_STEP`、开发者记忆卡、最新项目解析和长期总体规划中的阶段状态与接力入口。
- 下一阶段边界：3.7C 先进入 ARCHITECTURE，盘点材料适配、劳动实体规则、官网法源版本、规则金标和五类青年就业评测；未经用户确认不进入 FEATURE，不提前实施 3.7D。
- 验证：检查 3.7B/3.7C 状态在五份有效资料中一致，执行 Markdown 差异与 Git whitespace 检查。

## 2026-07-22 14:18:00 +08:00

- 会话 ID：当前环境未暴露；本地追踪标识 `stage37c-labor-rules-20260722`。
- 分支/Git 状态：当前分支 `master`；修改前已有3.7A/3.7B、前端、迁移、测试、文档和图件等大量未提交/未跟踪改动，本次全部保留，仅增量修改3.7C劳动领域代码、相关兼容测试和规定文档。
- 用户请求：进入 FEATURE 并执行 CURRENT_TASK，完成阶段3.7C事实、证据、法源、实体规则和青年就业旗舰评测；保持唯一Runtime Graph，不进入3.7D。
- 修改前阅读：工作流、CURRENT_TASK、代码规则、最新项目分析、总体规划、实际Agent流程、劳动材料/事实/规则/Domain/工具/Verifier、法源Provider与治理、既有30条评测及3.7A/3.7B测试。
- 实际改动：新增七类劳动材料适配器、证据矩阵、统一 `LaborRuleDecision` 契约；拆分欠薪、试用期、解除、补偿/赔偿版本化规则；劳动关系工具补齐事实/证据/法源引用；新增 `probation` 标签和白名单步骤；补入劳动合同法劳动关系与试用期条款；草稿指纹和引用覆盖实体规则版本与来源。
- 评测：新增正常、信息不足、非劳动关系、复合争议、高风险五类共25条旗舰金标，区分合成金标和官方公开案例改写；新增阶段3.7C材料、计算、追溯、法源阻断和数据集测试。
- 架构边界：继续只有一个 `CapabilityRuntimeGraph`；规则全部位于 `cn_labor`；复用现有 `LegalFact`、`MatterFactAssertion`、材料片段与Artifact引用，未新增表列或迁移；未修改前端。
- 验证：Anaconda Runtime 下阶段3.7C专项5/5、完整数字人Agent回归54/54通过；`compileall`通过；`git diff --check`无空白错误，仅有既有Windows换行提示。只读查询生产法源健康为 `unavailable`：预期4项、就绪0项、待复核4项。
- 风险与后续：规则输出仍明确不是最终法律结论，材料候选仍需用户确认；当地最低工资、当地平均工资、工会程序和特殊保护状态缺失时保留假设或补信息；4个官方版本必须由有权限复核人逐条批准，Agent不得冒充复核。当前状态 `READY_FOR_ACCEPTANCE`，3.7D未启动。

## 2026-07-22 14:31:00 +08:00（3.7C 验收返修）

- 会话 ID：当前环境未暴露；本地追踪标识 `stage37c-acceptance-fixes-20260722`。
- 用户请求：修复3.7C验收发现的经济补偿计算、失败关闭和旗舰评测覆盖缺陷。
- 根因：补偿规则只统计完整月份，导致不足一个月折算为0；当地平均工资缺失只记录假设而未阻断；旗舰评测直接调用分流规则，未经过 Runtime 与实体规则主链路。
- 实际改动：按完整年和剩余期间计算法定补偿月数，覆盖月末与闰日安全位移；缺当地平均工资时返回 `information_required`；旗舰评测强制注入 Runtime runner，25条全部经过关系分流 Runtime，5条复合争议继续经过材料、证据、实体规则和法源链路，并汇总七类材料覆盖。
- 验证：先新增失败测试稳定复现，再修复；阶段3.7C专项6/6、3.7B兼容专项4/4、完整数字人Agent回归55/55、Python `compileall` 和 `git diff --check` 全部通过，仅有既有CRLF提示。
- 风险与后续：生产法源健康仍为 `unavailable`，4/4版本处于 `review_required`；这是法律专业人员审批门槛，不得由Agent自动批准。任务保持 `READY_FOR_ACCEPTANCE`，不进入3.7D。

## 2026-07-22 15:43:00 +08:00（3.7C 开发测试批准）

- 用户请求：在当前测试阶段将4个待审核官方法源全部批准通过。
- 实际操作：严格核对待审核集合仅包含预期4项后，以复核标识 `dev_test_approval` 批量批准；备注明确“仅用于技术验收，不代表法律专业复核”。未删除法源或修改业务代码。
- 验证：待审核数量0，法源健康 `ready`，就绪4/4；完整数字人Agent回归55/55通过。
- 状态：阶段3.7C在开发测试环境标记 `COMPLETED`，不自动进入3.7D。正式环境不得复制当前批准记录，必须重新同步并完成真实法律专业复核。

## 2026-07-22 16:20:00 +08:00（3.7C 前端 Agent 闭环补齐）

- 用户请求：完善3.7C完整Agent闭环，解决前端无法补齐欠薪、试用期、解除、补偿/赔偿关键事实的问题。
- 实际改动：新增争议类型驱动的劳动事实表单和实体规则结果卡；扩充前端API类型与Matter事实恢复；材料建议可合并到完整事实；等待补充信息的仲裁Run通过 `provide_information` 续跑；聊天分析Run不会错误复用于文书流程；争议关键词统一映射为后端稳定标签。
- 自动化验证：新增复合前端事实经过审批生成仲裁草稿的后端测试；修复能力清单接口将列表直接展开到响应对象而恒定返回400的问题并新增端点测试；阶段3.7C专项7/7、完整数字人Agent回归57/57、`npx tsc --noEmit`、Next.js生产构建和 `git diff --check` 通过。
- 浏览器验收：实际完成创建Matter、确认中国法域、上传TXT、采用材料候选、触发缺失事实、补齐四类规则事实、查看4项规则和法源、批准高风险步骤并生成仲裁申请书草稿；页面资源与控制台无错误。
- 状态与边界：任务进入 `READY_FOR_ACCEPTANCE`，等待用户最终视觉/业务确认；未进入3.7D，未修改Runtime Graph、数据库结构或正式法源复核边界。

## 2026-07-22 16:46:00 +08:00（3.7C 加班费与字段可读性返修）

- 用户反馈：等待补充事实区域泄漏 `wage_arrears_amount_or_salary_and_months` 等内部字段名，且完整Agent闭环没有加班费。
- 根因：后端直接拼接缺失字段键，前端对持久化阻断原因和规则结果没有统一翻译；加班费此前只有分流关键词，没有稳定标签、事实契约、规则步骤、表单或《劳动法》第四十四条法源。
- 实际改动：新增统一中文字段标签和历史消息转换；新增加班费稳定标签、标准工时制事实、独立版本化核算规则、可选Runtime步骤、工具和Verifier接入；前端按争议类型显示工时制度、工资基数、三类加班时数、调休和已付金额；规则按工作日150%、休息日200%（扣除调休）、法定节假日300%计算并保留人工复核。法源补入《劳动法》第四十四条，版本身份改为提取法律正文而非动态网页原始哈希。
- 验证：先以失败测试复现法源版本不随提取条款变化的问题；最终完整数字人Agent回归57/57、3.7C专项9/9、法源Provider专项7/7、前端 `npx tsc --noEmit` 通过。真实浏览器以月工资8700元、工作日10小时、休息日8小时、法定节假日4小时、已付500元验证应付2150元、待付1650元，页面展示《劳动法》第四十四条且无内部字段名、资源或控制台错误。
- 法源与状态：最终4个版本按用户此前测试阶段授权以 `dev_test_approval` 批准，严格健康检查为 `ready`、4/4、待复核0；再次真实同步为4项全部 `unchanged`、无新待复核，证明动态网页外壳不会反复制造版本。正式环境必须重新同步并由专业法律人员复核。任务保持 `READY_FOR_ACCEPTANCE`，等待用户确认，不进入3.7D。

## 2026-07-22 17:05:00 +08:00（3.7C 合规测试文档）

- 用户请求：提供一份可执行、可留档的合规测试文档。
- 实际改动：新增 `newModify/阶段3.7C合规测试与验收文档.md`，包含文档控制、数据和法律边界、范围、环境、完整调用链、18项功能与合规用例、自动化命令、已执行结果、缺陷分级、退出标准和验收签字表。
- 合规边界：明确开发测试法源批准不等于法律专业复核；正式环境必须清理测试法源、重新同步并由有权限人员逐条批准；测试数据必须虚构或脱敏。
- 验证：对照当前加班费规则、事实Schema、Runtime步骤、前端字段、法源CLI、路由和阶段测试核对文档；执行Markdown链接、内部字段示例和差异空白检查。

## 2026-07-22 17:18:00 +08:00（真实场景智能体测试材料）

- 用户澄清：需要的是可直接上传给数字人智能体的真实场景测试材料，不是测试计划。
- 实际改动：新增 `output/doc/张晨劳动争议测试材料_全部虚构.txt`。材料模拟一名后端工程师的劳动合同、两个月欠薪、三类加班、部分加班补贴、不能胜任解除、企业微信沟通和证据清单，可验证欠薪、加班费、解除及赔偿金组合闭环。
- 数据边界：全部姓名、单位、日期、金额和证据均为虚构，文件内有醒目测试声明，不包含真实个人信息。
- 兼容性与验证：因当前前端只接受TXT，交付TXT而非DOCX；使用当前确定性候选提取器验证申请人、用人单位、工作地点、入职日期、月工资、争议类型、权利受损日期、解除日期、解除原因和仲裁请求均可识别，材料适配器归类为劳动合同。

## 2026-07-22（3.7C 工作台独占布局返修）

- 用户反馈：工作台与左侧聊天并排时表单过窄、阅读困难，希望进入工作台后覆盖聊天，同时保留随时切换能力。
- 实际改动：将数字人展开态改为“标题栏 + 全宽工作区”；工作台模式隐藏聊天和历史栏，顶部增加带文字的“案件工作台/返回对话”固定切换按钮，并同步调整桌面端和移动端间距。
- 回归修复：窄屏实测发现隐藏历史栏后仍保留空网格轨道，导致工作区高度不足；展开态面板改为两行网格，工作区现可占满标题栏以下全部高度。
- 验证：前端 `npx tsc --noEmit` 通过；真实浏览器验证1280×800桌面端与390×844窄屏，工作台宽高均与内容区一致，聊天和历史栏隐藏，顶部“返回对话”可恢复聊天，控制台无错误。任务回到 `READY_FOR_ACCEPTANCE`，等待用户视觉确认。

## 2026-07-22（3.7C 必填引导与调用预算返修）

- 用户反馈：劳动事实表单无法提前判断哪些项目必须填写，复杂任务补充两轮事实就达到工具调用上限。
- 根因：前端只展示后端运行后返回的缺失字段，首次填写没有动态必填规则；复杂仲裁模板最多包含8个工具步骤，但默认预算同为8次，补充事实触发重新核验后会累计消耗预算。
- 实际改动：前端按基础事实和争议类型实时计算必填项，显示“必填”、二选一、至少一项及当前缺项数量；缺项时按钮不调用后端。`PlanTemplate` 新增有界工具预算声明，复杂劳动仲裁和案件分析设为24次，通用Runtime仍执行原预算门禁，显式低预算不会被覆盖。

## 2026-07-22（3.7C 表单语义与布局二次返修）

- 用户反馈：“二选一必填”难以理解，表单被挤成三列且视觉效果差。
- 根因：全局规则 `.dh-labor-tool > div` 误命中劳动争议表单根节点，将引导、基础事实和欠薪事实强制排成三列；分组必填规则又把同一约束重复贴到多个输入框。
- 实际改动：将全局三列规则收窄到快速计算器专用容器；表单改为基础事实独占整行、其余事实两列卡片、窄屏单列；必填提示改为红色星号和紧凑说明；欠薪固定要求“欠薪总金额+欠薪开始日期”，其余字段明确选填；加班时数改为段落说明至少填写一种，不再给三个字段重复标记。
- 验证：前端 `npx tsc --noEmit` 通过；真实浏览器完成材料采用后的复合争议页面回归，确认“二选一”和字段级“至少一项”均为0处，基础事实宽度与表单内容区一致，欠薪/加班卡片两列排列且标签、说明、缺项提示可读。

## 2026-07-22（3.7C 会话、材料与草稿导出体验返修）

- 用户反馈：工作台顶部缺少新建会话；现有材料像开发者准备的测试文本；最终结果缺少 Word/PDF 导出。
- 实际改动：标题栏新增始终可见的“新建会话”，执行后取消在途聊天、清空当前上下文并返回对话；材料入口去掉“测试材料.txt”默认值，改为面向用户的真实材料说明，并明确测试版只支持 TXT/粘贴原文、正式版应接入 Word/PDF/图片识别；复用项目现有导出能力，为经审批生成的劳动仲裁申请书草稿增加 Word/PDF 下载及待复核提示。
- 验证：前端 `npx tsc --noEmit` 通过；真实浏览器验证工作台顶部可见新建会话且点击后返回空白对话；恢复案件后材料入口显示真实材料说明、不再出现默认测试文件名。导出按钮受 `laborDraft` 条件保护，只在草稿实际生成后出现。

## 2026-07-22（3.7C 案件导航与信息降噪返修）

- 用户纠正：上一轮把工作台“新建案件”误做成聊天“新建会话”；工作台展开后无法随时查看历史案件；Matter ID、模板名、Agent Run 和原始结果等内部信息没有用户价值。
- 实际改动：移除聊天标题栏新增的会话按钮，保留原历史会话区的“+”；工作台增加独立的“历史案件/新建案件”导航，案件列表可在创建、法域、材料和结果任意步骤展开，选择案件后自动收起；普通聊天页工作台摘要显示历史案件数量；内部运行信息替换为“当前案件+中文处理状态”的单行摘要。
- 验证：前端 `npx tsc --noEmit` 通过；真实浏览器验证聊天标题栏无新增会话按钮、历史会话仍存在，工作台可随时展开历史案件、新建案件保持在工作台内、恢复案件后导航仍可用；页面不再出现案件编号、`Agent Run`、内部模板名和原始最终结果。

## 2026-07-22（3.7C 工作台入口合并）

- 用户反馈：普通聊天顶部已有“案件工作台”，底部再次显示“查看案件”重复占用空间，导致消息区域过短。
- 实际改动：移除普通聊天底部工作台摘要卡及对应样式；案件工作台组件仅在展开态挂载，顶部按钮成为唯一入口，历史案件和新建案件继续留在展开后的工作台中。
- 验证：前端 `npx tsc --noEmit` 通过；真实浏览器确认顶部工作台入口存在、底部卡片 DOM 不存在、消息区获得释放空间；点击顶部入口后历史案件、新建案件和返回对话均正常。
- 验证：新增“两轮补充事实后进入审批”失败回归并修复；预算专项与阶段3.7B共9项通过，完整数字人阶段回归58/58通过，Python `compileall`、前端 `npx tsc --noEmit` 通过。浏览器联调期间发现本地3000与临时3001共用 `.next` 导致临时实例脚本加载失败，已停止临时实例且未改动原3000服务；任务回到 `READY_FOR_ACCEPTANCE`，等待用户刷新服务后视觉确认。

## 2026-07-22（3.7C 多格式材料整理闭环）

- 用户确认产品边界：通用“纠纷管理”继续提供维权注意事项、路径和评估；案件工作台专注青年就业欠薪、劳动仲裁、证据与法源，不合并两套案件数据。
- 实际改动：抽取共享材料识别服务，支持 TXT、PDF、DOCX、PNG/JPG、MP3/WAV/M4A、MP4/MOV/AVI，限制单文件25MB；旧纠纷整理与新工作台共用图片、音频和视频识别实现。工作台新增四类格式选择，先生成可编辑整理稿，用户确认后才按原文件媒体类型保存到当前 Matter 并继续事实定位、证据和仲裁分析。
- 安全边界：识别预览不落库，无法识别时明确失败，不再用“文件名占位符”冒充材料内容；不保存上传二进制，不引入实时语音会话，也不改变法源、审批或人工复核门禁。
- 验证：材料识别与预览接口测试4/4、与阶段3.7C规则回归合计13项及13个子测试通过；前端 `npx tsc --noEmit` 与差异空白检查通过。当前 `law` 环境已补齐 Tesseract 与 Whisper base 模型，代码可自动发现 Conda 内的 Tesseract、中文数据和 FFmpeg；使用真实PNG经运行中的8001接口识别出663字，临时Matter随即删除。任务保持 `READY_FOR_ACCEPTANCE`，等待用户完成多格式文件的实际环境体验验收。

## 2026-07-27（数字人 Agent 目录与完整流程导读）

- 用户请求：按 `flask_app/legal_agent_system` 路径分层说明每个包和每个 `.py` 文件，并提供一个可直观看懂的完整流程案例。
- 实际改动：新增 `flask_app/legal_agent_system/数字人Agent目录与完整流程导读.md`，覆盖当前8个主要职责包、71个Python文件；按根目录、能力、领域、Runtime、工具、案件、法域、劳动业务、材料适配器和实体规则逐层解释。
- 完整案例：使用“加班费劳动仲裁”串联数字人聊天、劳动初筛、Matter、法域、材料、候选事实、Capability Registry、Plan revision、Runtime单步循环、加班费规则、法源验证、三类暂停、用户审批和仲裁草稿。
- 可发现性：在 `legal_agent_system/README.md` 增加新导读入口；未修改任何业务代码、数据库结构或当前任务状态。

## 2026-07-27（阶段3.7D进入ARCHITECTURE）

- 用户请求：进入ARCHITECTURE模式并开始阶段3.7D。
- 状态推进：用户新目标覆盖3.7C待验收任务；3.7C开发测试成果视为阶段基线，正式环境法源重新同步和法律专业复核要求继续保留。`CURRENT_TASK`已初始化为阶段3.7D并进入 `DESIGNING`。
- 架构结论：按最新总体规划，3.7D仅建设Conversation Foundation，不包含流式、实时取消和语音；新增独立Conversation服务包，建立Raw Messages、Token Budget Recent Window、Structured Memory、ContextBuilder、Rolling Summary、单一Router与Conversation Orchestrator。
- 安全边界：Conversation Memory不等于Matter正式事实；Assistant内容不得成为案件事实；Router只决策，Orchestrator只经现有Matter/Triage/Agent Facade执行；不修改Runtime Graph、劳动Domain、Plan、Tool、Verifier、法源或审批协议。
- 文档改动：新增 `newModify/阶段3.7D架构设计.md`，同步更新 `AI_WORKFLOW/CURRENT_TASK.md`、`NEXT_STEP.md`、`DECISIONS.md` 和最新项目分析。当前只完成架构设计，未修改业务代码、数据库或API。

## 2026-07-27（3.7D Rolling Summary冲突治理补充）

- 用户指出：若Rolling Summary仅保存大段自然语言，无法安全处理“工资6500更正为7200”等局部事实冲突。
- 架构调整：Rolling Summary明确拆为可读 `summary_text` 与结构化 `summary_items`；重要事实、目标、决定和待办条目保存类型、来源消息、状态和替代关系。
- 冲突规则：ContextBuilder只按结构化条目判断冲突；旧条目标记 `superseded`，新条目引用当前用户消息并指向旧条目，再由有效条目重建 `summary_text`。禁止通过自然语言字符串切片治理事实。
- 状态与范围：同步更新3.7D架构、CURRENT_TASK和关键决策；任务保持 `DESIGNING`，未修改业务代码或数据库。

## 2026-07-27（阶段3.7D方案批准并进入FEATURE）

- 用户确认阶段3.7D架构方案，可以进入FEATURE实施。
- 状态推进：任务由 `DESIGNING` 经 `APPROVED` 进入 `IMPLEMENTING`。
- 实施顺序：会话存储与Token Budget → Structured Memory/ContextBuilder → 双层Rolling Summary → Router/Orchestrator → 前端单入口与完整回归。

## 2026-07-27（阶段3.7D Conversation Foundation实现）

- 后端结构：新增独立 `services/conversation/`，拆分契约、Token预算、Repository、Memory、ContextBuilder、Router、Actions、Orchestrator和跨进程Session锁；`DigitalHumanService`改为兼容Facade并删除固定最近6条与重复持久化代码。
- 数据与迁移：`digital_human_messages`新增 `request_id`、`estimated_tokens` 和请求角色唯一约束；新增 `conversation_memories` 保存版本化Structured Memory及 `summary_text + summary_items`；Alembic `20260727_0009`已应用到本地实库。
- 摘要治理：重要事实和目标保存类型、来源消息、状态及替代关系；旧值通过 `superseded` 失效后重建摘要文本。修复专项测试发现的“目标原句夹带旧工资6500”问题，目标现只保存非事实语义，金额只能进入可治理fact条目。
- 单一入口：Router使用确定性高风险/劳动/当前Matter规则与封闭Schema LLM回退；Orchestrator统一执行受控动作。普通咨询不创建Matter，明确案件请求才创建；同一Session串行，同一请求重试返回缓存，失败重试复用已有Matter。
- 冲突与安全：Matter正式事实优先；聊天候选冲突时排除并引导工作台确认。高风险、`blocked_authority`、人工接管和审批状态均不能由会话层绕过；Assistant内容不能进入用户事实。
- 前端：聊天提交移除 `isLaborQuestion → laborTriage.start` 双入口，改为消费后端 `decision/action/context` 并同步当前Matter/Run缓存；工作台事实补录能力保持不变。
- 验证：阶段3.7D专项8项和架构边界4项通过；完整数字人回归70/70通过；Python `compileall`、前端 `npx tsc --noEmit`、Alembic current/heads（均为 `20260727_0009`）及 `git diff --check` 通过。任务进入 `READY_FOR_ACCEPTANCE`。

## 2026-07-27（阶段3.7D REVIEW 三项P1修复）

- 路由授权：`labor_triage`新增服务端确定性副作用授权；LLM强制建议但当前输入无明确建案意图时降级普通对话。Actions执行前再次校验授权；用户Structured Memory和Rolling Summary改为不可信user上下文。
- 锁与并发：会话advisory lock缩短为request领取、检查点和完成写入三个数据库临界区，LLM与业务执行期间不持有锁连接；request租约令牌保持跨进程同会话互斥并阻止失效执行者覆盖。
- 恢复幂等：新增迁移 `20260727_0010`，在原request表记录动作、Matter/Run资源、检查点及租约。Matter支持指定ID幂等创建；Run在执行前记录实际ID；动作、assistant或request完成失败后使用相同request_id恢复，禁止重新创建Matter/Run。
- 验证：新增LLM越权、咨询误建案、慢LLM锁释放、同会话并发、Run预留后中断、Run完成后assistant/request失败及assistant已保存恢复测试。3.7D专项12/12、数字人阶段回归70/70、完整后端测试78/78、Python语法检查通过。

## 2026-07-27（阶段3.7D验收收尾）

- 用户确认进行3.7D收尾，任务状态由 `READY_FOR_ACCEPTANCE` 更新为 `COMPLETED`。
- 收尾依据：Conversation Foundation功能已完成；REVIEW三个P1全部关闭；3.7D专项12/12、数字人阶段回归70/70、完整后端测试78/78通过。
- 下一阶段未自动启动；3.7E仅保留为候选，等待用户明确指令。生产部署仍需执行Alembic `20260727_0010`。

## 2026-07-27（阶段3.7E ARCHITECTURE启动）

- 用户明确进入下一阶段并指定ARCHITECTURE模式；CURRENT_TASK由已完成的3.7D切换为3.7E Conversation × Workspace，状态推进到 `ARCHITECTURE`，未修改业务代码。
- 现状缺口：`loadSession()`只恢复消息，Matter/Triage/Run依赖localStorage中的 `laborContextBySession`；Session与Matter一对多但缺少当前Matter权威指针；工作台没有确定性Conversation Presenter和侧边陪伴模式。
- 推荐方案：新增每Session一行的Workspace State、服务端Workspace Context聚合接口、无LLM的Presenter和前端原子Hydration；聊天与陪伴模式复用同一Session、Store、消息线程和发送动作。
- 身份边界：现有匿名client_id也存于localStorage，清空后无法读取旧数据；推荐用HttpOnly匿名身份Cookie兼容现有请求头，仅解决同浏览器身份连续性，不扩展为完整账号系统。
- 新增 `newModify/阶段3.7E架构设计.md`，记录模块边界、数据结构、接口投影、实施切片和验收矩阵；等待用户批准后再进入FEATURE实现。

## 2026-07-27（阶段3.7E方案批准并进入LAW-DEV）

- 用户确认3.7E架构无问题并要求执行；任务由 `ARCHITECTURE` 经 `APPROVED` 进入 `IMPLEMENTING`。
- 批准D010/D011：服务端Workspace State维护当前Matter；HttpOnly匿名身份Cookie兼容现有请求头。
- 实施顺序保持为：身份与数据状态 → 聚合恢复/Presenter → 前端原子恢复 → 工作台侧边陪伴 → 回归与视觉验收。

## 2026-07-27（LAW-DEV / LAW-REVIEW 双工作流）

- 用户请求：建立 `LAW-DEV` 日常开发与 `LAW-REVIEW` 阶段验收两个独立工作流，分离实现和正式验收职责。
- 实际改动：新增两份工作流正文；`LAW-DEV` 固化最小修改、实际测试、Diff 和法律安全闭环，`LAW-REVIEW` 固化默认只读、阶段边界检查及 P0/P1/P2 证据要求。
- 路由接入：根 `AGENTS.md`、`AI_WORKFLOW/WORKFLOW.md` 和索引已接入自然语言路由；未修改业务源码、3.7E 架构方案或 Runtime 安全边界。

## 2026-07-27（数据库表中文注释脚本）

- 用户请求：为数据库表补充易于区分用途的中文注释，并明确可直接提供 Navicat 执行 SQL。
- 实际改动：新增 `sql/postgresql_table_comments.sql`，覆盖当前 72 张 ORM 业务表；默认操作 PostgreSQL `public` schema，不存在的表自动跳过，末尾附带表注释查询。
- 范围控制：未修改 ORM 模型、Alembic 迁移或业务代码，未直接持久化修改本地数据库。
- 验证：SQL 表名与 ORM 表名集合完全一致；脚本已在真实 PostgreSQL 事务内执行成功并回滚。
- 实库补充：根据 Navicat 截图和实库只读核对，补充 7 张仅存在于历史 SQL 的表及 `alembic_version`；最终脚本覆盖实库全部 80 张表。
## 2026-07-27（阶段 3.7E Conversation × Workspace 实现）

- 根据用户批准的架构执行 LAW-DEV：新增匿名身份兼容层、`ConversationWorkspaceState`、Workspace 聚合服务、确定性 Presenter 及 GET/PUT Workspace API。
- Conversation Repository、案件创建/恢复/删除接入服务端当前 Matter 指针；显式清空、多案件切换、跨客户隔离及旧请求头兼容均有专项测试。
- 前端改为消息与 Workspace Context 原子 Hydration，移除 localStorage 中 Matter/Triage/Run 权威缓存；聊天与工作台侧边数字人共享同一 Session、消息流和发送入口。
- 新增迁移 `20260727_0011` 并应用到本地数据库。全量后端测试 84/84、TypeScript、Python compileall、Alembic current/heads 和 `git diff --check` 通过。
- 真实浏览器完成桌面端与 375×812 移动端复核；修正无会话时 Presenter 持续显示“正在恢复”的空状态问题。任务进入 `READY_FOR_ACCEPTANCE`。
## 2026-07-27（阶段 3.7E LAW-REVIEW 返修启动）

- LAW-REVIEW 自动测试全部通过，但只读审查发现三类 P1：Matter/Workspace 部分提交、跨 Session 恢复错误 Matter、在途请求与快速选择响应倒灌。
- 用户确认进入 LAW-DEV 返修；任务由 `READY_FOR_ACCEPTANCE` 返回 `IMPLEMENTING`，不扩大到 Runtime、法源或审批协议。

## 2026-07-27（阶段 3.7E LAW-REVIEW 返修完成）

- 创建一致性：案件创建增加客户端稳定幂等键和服务端确定性 Matter ID；失败重试复用同一案件，创建响应直接携带权威 Workspace 快照，避免基于旧版本二次选择。
- 恢复与竞态：跨 Session 历史案件先加载目标会话再显式选择目标 Matter；聊天请求增加操作序列与取消保护；案件选择增加 Workspace 版本校验、Session 行锁和前端顺序队列。
- 生命周期：新增无 LLM 的空 Session 创建接口；当前 Matter 删除、回退选择和 Workspace 版本更新合并到同一事务，并与案件选择共享锁顺序。
- 验证：阶段 3.7E 专项 11/11、完整后端 95/95（另有 13 个子测试）、`npx tsc --noEmit`、Python `compileall`、Alembic current/heads `20260727_0011` 和 `git diff --check` 均通过。任务恢复为 `READY_FOR_ACCEPTANCE`。

## 2026-07-27（阶段 3.7E 第二轮 LAW-REVIEW 返修启动）

- 第二轮只读验收发现两项 P1：聊天后台建案未携带 Workspace 版本，可能晚到覆盖用户选择；Workspace Context 分两个事务读取 Matter 与版本，可能形成不一致快照。
- 用户批准进入 LAW-DEV 最小返修；范围仅限 Conversation Actions/Orchestrator、Workspace 聚合服务、前端选择取消保护及并发回归测试。

## 2026-07-27（阶段 3.7E 第二轮 LAW-REVIEW 返修完成）

- 后台动作版本保护：Conversation Orchestrator 在请求领取时读取 Workspace 版本并写入动作检查点；首次执行与恢复均复用该版本。重复选择同一 Matter 保持幂等，版本已变化且指针不同则不覆盖用户的新选择。
- 一致性快照：Workspace Context、当前 Matter 解析和版本读取统一使用 Session 行锁；指针、版本、Matter、Triage 与 Run ID 在同一事务内完成投影。
- 前端保护：同 Session 案件选择会使在途聊天操作失效并清理 loading 状态，防止已失效响应短暂覆盖当前案件。
- 验证：新增后台动作 CAS 和真实线程交错快照测试；3.7D/3.7E 联合回归 25/25、3.7E 专项 13/13、完整后端 97/97（另有 13 个子测试）、TypeScript、Python compileall、Alembic current/heads `20260727_0011` 均通过。

## 2026-07-27（新增验收导读模式）

- 用户希望把“完整故事 + LAW-DEV验收报告结构”的只读讲解固化到工作流，避免 `REVIEW / LEARN` 被路由成简短结论或逐函数拆解。
- 新增 `ACCEPTANCE_GUIDE`：先执行 LAW-REVIEW 核实事实，再一次讲完目标、完整业务故事、状态/数据库变化、Before → After、安全边界、测试证据、人工验收表和关键文件入口。
- 自动路由已接入“验收导读、讲清最终效果、怎么人工验收、完整故事一次讲完”等自然语言；该模式保持只读，REVIEW 失败时必须先报告阻断问题。

## 2026-08-14（阶段 3.7F 第一部分：SSE增量呈现）

- 用户确认 3.7E 技术验收 PASS（已提交 `e00e578`）并批准 3.7F 架构决定：保留 `POST /chat`、新增 `POST /chat/stream`、SSE 只呈现服务端完成解析/路由/安全校验/持久化后的已验证回复、不宣称原始 LLM Token 流式输出、不做语音口型、不修改仲裁业务。
- 后端：新增 `services/conversation/sse.py`（事件编码、按字符分块、稳定错误映射：中文错误 + 错误码 + 是否可重试）；`DigitalHumanService.chat_stream` 生成器复用同一 Orchestrator，事件顺序 accepted → thinking → delta* → completed，异常以 error 事件收尾；路由设置 `Cache-Control: no-cache, no-transform` 与 `X-Accel-Buffering: no`，校验失败仍返回 JSON 400。
- 前端：`sendDigitalHumanMessageStream` 用 fetch + ReadableStream 解析 SSE（不用 EventSource）；不支持流式读取时降级普通请求并显示明确中文提示；Zustand 只维护一条 `streamingMessage` 临时消息，completed 后才确认最终消息与 Workspace；主对话与工作台侧边陪伴共用同一 `sendMessage`，两侧均渲染增量气泡。
- 幂等与恢复：同一 request_id 重试复用现有请求缓存，不重复创建 Matter/Run；流中断后服务端已完成消息仍可通过历史恢复，前端不写半条正式 assistant 消息。AbortController 仅停止前端读取，服务端取消留待 3.7F 第二部分。
- 验证：3.7F 专项 12/12、3.7D + 3.7E 联合回归 25/25、`npx tsc --noEmit`、Python `compileall`、`git diff --check` 均通过；未修改数据库结构、迁移、Runtime Graph、劳动规则或审批协议。

## 2026-08-14（阶段 3.7F 返修：真实模型结构化输出解析可靠性）

- 用户浏览器验收发现：明确劳动咨询偶发返回"我还不太确定你的需求……"固定兜底句；自动测试使用固定 Fake LLM 无法覆盖。真实模型探针定位失败类型：多轮会话中 DeepSeek 偶发返回纯文本（含 Markdown 加粗、无 JSON），解析失败后固定兜底句被作为 assistant 消息写入历史，后续轮次模型逐字复读兜底句形成永久污染循环。
- 修复（仅 `digital_human_service.py`）：首次响应非 JSON 时追加"严格只返回 JSON"指令重试一次；解析链增强为清理围栏 → 直接解析 → 平衡括号提取 → 字符串内裸换行/制表符与尾逗号修复；全部失败时降级为模型纯文本回复（剔除 Markdown 加粗，含花括号或超长则拒绝），路由仍由服务端确定性规则决定，固定兜底句仅作为最后手段，不再污染会话历史。
- 失败类型记录：日志现在记录失败阶段与截断的原始响应头部，便于后续真实环境继续观测。
- 验证：新增可靠性专项 14/14（含纯文本降级、重试、修复、兜底隔离与真实链路集成）；3.7F 流式专项 12/12、3.7D + 3.7E 联合回归 25/25；真实模型复验 6/6 轮无兜底句、重试全部拉回合法 JSON；Python compileall 与 `git diff --check` 通过。

## 2026-08-14（阶段 3.7F 前端呈现返修：Markdown 正文统一渲染）

- 用户浏览器验收发现：数字人回复中的 `**加粗**` 被原样显示、编号列表与段落换行拥挤、主聊天与工作台侧边呈现不一致。
- 新增 `frontend/src/components/DigitalHuman/ConversationMessageContent.tsx` 共享正文组件：复用项目已有 react-markdown + remark-gfm，仅 assistant 消息渲染 Markdown，用户消息保持纯文本；未启用 rehypeRaw，未使用 dangerouslySetInnerHTML。
- `DigitalHumanChat` 与 `DigitalHumanCompanion` 共用该组件（禁止各写一套解析逻辑）；流式临时消息走同一渲染路径，光标动画移入组件局部样式；为 p/ol/ul/li/strong/code 设置局部样式，紧凑模式匹配侧边 11px 排版，避免影响全局页面。
- 验证：`npx tsc --noEmit` 通过、3.7F 专项 26/26、`git diff --check` 通过；未修改后端、SSE 协议、Store 状态结构与业务逻辑，未执行任何 git 写操作。

## 2026-08-14（阶段 3.7F 浏览器呈现第二轮返修）

- 用户复验发现：发送后先出现只有光标的空白气泡；真实模型回复携带双重转义排版符时，Markdown 正文显示字面量 `\\n`，列表仍无法成形。
- Store 改为发送时不预建空 `streamingMessage`，继续显示既有打字动画；首个非空 delta 到达后才创建并追加唯一流式消息。
- `DigitalHumanService` 在结构化结果校验后统一规范 reply：仅恢复单层字面量 `\\r\\n`、`\\n`、`\\t`，双反斜杠文本保持不变；SSE、持久化与历史恢复共享同一规范化结果。
- 验证：可靠性 + SSE 专项 28/28、`npx tsc --noEmit`、`git diff --check` 通过；未修改 Runtime、劳动规则、审批、数据库结构或迁移。

## 2026-08-14（阶段 3.7F 第一部分验收通过并收尾）

- 用户完成真实浏览器验收并确认无问题：增量呈现、结构化输出可靠性、Markdown 正文渲染与主聊天/侧边一致性全部通过。
- 收尾期间补充：解析后的 reply 对单层字面量 `\n`、`\r\n`、`\t` 做受控反转义（保留双反斜杠文本），恢复 Markdown 段落与列表排版；等待阶段保留打字动画，收到首个非空 delta 后才创建流式气泡，消除空白光标气泡；对应新增双转义排版符与转义保留专项测试。
- 最终验证：可靠性专项 16/16、3.7F 流式专项 12/12、3.7F + 3.7D + 3.7E 全量回归 53/53、`npx tsc --noEmit`、Python `compileall`、`git diff --check` 均通过。
- 任务状态更新为 `COMPLETED`；工作区改动未提交，由用户自行决定提交时机。服务端取消、语音与口型动画留待后续部分。

## 2026-08-14（阶段 3.7F 第二部分：服务端取消）

- 用户确认完成整个 3.7F（第二部分范围仅服务端取消，语音/口型继续暂缓）。实施：新增 `services/conversation/cancel.py`（进程级取消注册表 15min TTL + 0.5s 节流 DB 轮询双通道、`ConversationCancelled` 不继承 RuntimeError）；`digital_human_requests` 增加 cancelling/cancelled 状态（自由字符串，无迁移）；`mark_cancelling` 保留租约与检查点、`mark_cancelled` 租约断言后清租约保留 checkpoint/resources；`begin_request` 取消重试分支（有检查点幂等恢复 / 无检查点重跑 / cancelling 有效租约拒绝穿透）与会话活跃冲突计入 cancelling。
- Orchestrator 最小接入：arm/disarm、begin_request 前后双检查、`_ensure_not_cancelled` 四个检查点（动作快路径前、动作执行前、动作执行后、完成前）；except 分支按取消分流到 mark_cancelled。LLM 分块循环每 chunk 检查取消 → break + 显式 close() 中止 httpx 模型流（经 GeneratorExit → openai Stream.close → httpx 关闭链，已查证）；重试第二次 stream 同样检查。动作执行中不强制中断，副作用幂等保留。
- 新增 `POST /api/digital-human/chat/cancel`（幂等；404/403/400）；非流式 /chat 映射 409 CANCELLED；SSE 复用 error 事件（code=CANCELLED, retryable=true）。前端：`cancelDigitalHumanChatRequest`、在途 `activeRequestId`、停止按钮先通知服务端再本地 abort、CANCELLED 特判（不追加错误气泡，提示"已停止回复"）。
- 验证：取消专项 23/23（注册表、仓库状态机、LLM 阶段/动作前/动作中/完成窗口取消、重试恢复、路由与前端守卫）；3.7F 流式 12/12、可靠性 16/16、3.7D/3.7E 25/25 合计 76/76；`npx tsc --noEmit`、Python compileall、`git diff --check` 通过。未修改数据库结构、迁移、Runtime Graph、劳动规则或审批协议。

## 2026-08-15（阶段 3.7F 第二部分返修：完成窗口竞态与停止提示）

- 用户验收反馈两项：P1 状态竞态 —— `mark_action_completed()` 与 `complete_request()` 之间到达的取消会被覆盖写成 completed；P2 停止提示 —— `cancelRequest()` 清空 `streamFallbackNotice` 后，异步 CANCELLED 分支因操作序列已失效被跳过，提示不显示。
- P1 修复（仅 `repository.py` + `orchestrator.py`）：`_execute_recoverable_action` 在 `mark_action_completed` 后、`complete_request` 前增加一次 `_ensure_not_cancelled`；`complete_request` 增加允许完成状态白名单 `ALLOWED_COMPLETE_STATUSES`（processing/action_completed），发现 cancelling/cancelled 抛 `ConversationCancelled` 拒绝写 completed（由 orchestrator except 分流落 cancelled 终态），其余状态抛 RequestInProgress。动作副作用仍幂等保留，检查点不丢。
- P2 修复（仅 `digitalHumanStore.ts`）：`cancelRequest` 点击即同步设置 `streamFallbackNotice: '已停止回复'` 且不再清空；保留 sendMessage 的 CANCELLED 特判分支覆盖非本端发起的取消；下一次发送/加载会话/新会话仍按既有逻辑清空提示。
- 测试：新增仓库单测 `test_complete_request_rejects_cancelled_statuses`（cancelling/cancelled 拒绝完成、无 assistant 消息、租约与 response_json 不变）；集成测试 `test_cancel_landing_between_action_completed_and_complete_request`（动作完成瞬间取消 → CANCELLED、检查点保留、同 request_id 重试幂等恢复、Matter 不重复）；前端守卫 `test_frontend_stop_notice_synchronous_without_error_bubble`（提示同步给出、不清空、不追加错误气泡）。
- 验证：取消专项 26/26；3.7F 流式 12/12、可靠性 16/16、3.7D 12/12、3.7E 13/13，合计 79/79；`npx tsc --noEmit`、Python `compileall`、`git diff --check` 通过。未修改数据库结构、迁移、Runtime Graph、劳动规则或审批协议。

## 2026-08-15（阶段 3.7F 第二部分验收通过并整体收尾）

- 用户对返修（完成窗口竞态 + 停止提示）验收通过，3.7F 第二部分与 3.7F 整体收尾：`CURRENT_TASK` 状态更新为 `COMPLETED`，`NEXT_STEP` 更新为 3.7G → 3.7H 依赖顺序，不自动启动后续阶段。
- 最终验证基线：取消专项 26/26、3.7F 流式 12/12、可靠性 16/16、3.7D 12/12、3.7E 13/13，合计 79/79；`npx tsc --noEmit`、Python `compileall`、`git diff --check` 通过。
- 工作区改动未提交，由用户自行决定提交时机。

## 2026-08-15（3.7F 提交 + 3.7G 初始化）

- 3.7F 全部改动提交 `1b2f6ac`（21 个文件，+3196/-101）：提交前复验 79/79（取消 26 + 流式 12 + 可靠性 16 + 3.7D 12 + 3.7E 13）、`npx tsc --noEmit`、compileall、`git diff --check` 全部通过；`法律AI/` 目录与 3.7F 无关，未纳入提交。
- 3.7G 初始化：`CURRENT_TASK` 切换为 3.7G（`DESIGNING`），产出 `newModify/阶段3.7G架构设计.md`（纯前端语音闭环：`frontend/src/lib/voice/` 独立 STT/TTS 控制器、Store 集成、Composer 麦克风/播报开关、气泡朗读按钮、talk_normal 说话状态图；后端零改动），待用户审批。
- 未修改任何代码、数据库结构或迁移；未执行语音实现。

## 2026-08-15（阶段 3.7G Voice Interaction：基础语音闭环实现）

- 架构设计获用户批准后实施（纯前端，后端零改动）：
  - 新增 `frontend/src/lib/voice/` 独立轻量控制器：`ttsController.ts`（中文 voice 优先、`filterSpeakableText` 清洗 Markdown/emoji、新朗读先 cancel 打断）、`sttController.ts`（continuous/interim zh-CN、onend 自动重启、not-allowed/network 降级提示）、`useVoiceReady.ts`（SSR 水合守卫）。
  - Store：`voiceEnabled`（默认关，partialize 持久化）、`voiceSpeaking`/`speakingMessageId`；`toggleVoice`/`speakMessage`/`stopSpeaking`；sendMessage 开头与成功路径、cancelRequest、close/loadSession/startNewConversation/reset/deleteSession 集成 TTS 取消。
  - `ConversationComposer`：麦克风按钮（interim 预览 + final 累积 + 发送前停识别）、播报开关、识别错误轻量提示；主聊天与工作台侧边共用。
  - `DigitalHumanChat`/`DigitalHumanCompanion`：assistant 气泡朗读/停止按钮、Avatar `voiceSpeaking → talk_normal` 说话状态图；`DigitalHumanFloat` styled-jsx 仅追加语音 class，既有 class 未动。
- 测试：新增 `test_digital_human_stage37g_voice.py` 前端源码守卫 30/30；3.7F 取消/流式/可靠性/3.7D/3.7E 全量回归 109/109；`npx tsc --noEmit`、compileall、`git diff --check` 通过。
- 附带修复（测试级）：3.7F 取消集成测试的动作路径会触发权威法源真实网络同步（每源 12s 超时，缓存过期后整组挂起），在 `CancelServiceIntegrationTest.setUp` 隔离 `_try_sync_authorities` 使取消竞态测试离线化；取消语义断言不变。
- 附带修复（仓库级）：`.gitignore` 的 Python 模板规则 `lib/` 误伤 `frontend/src/lib`，按最小范围放行 `frontend/src/lib/voice/`（既有 `frontend/src/lib/api.ts`、`exportUtils.ts` 仍未入库，属历史遗留，待用户决定）。
- 未修改后端路由/服务/模型、SSE 协议、数据库结构或迁移、Runtime Graph、劳动规则与审批流程。
- 状态：`READY_FOR_ACCEPTANCE`，待用户 Chrome/Edge 浏览器验收。

## 2026-08-15（修复：前端编译错误 e'use client'）

- 用户重启前端后报 `DigitalHumanCompanion.tsx` 语法错误（`GET / 500`）：第 1 行混入多余字符 `e`（`e'use client';`）。移除后 `npx tsc --noEmit` 通过、首页恢复 200。
- 该字符非 3.7G 实现引入（实现完成后 tsc 与 109 项回归均通过），疑似编辑器误触；其余 3.7G 文件首行均正常。
- 附注：截图气泡报错"生成回复失败: 读取请求体失败: 'NoneType' object has no attribute 'split'"的文本在本仓库任何代码（含 git 历史）中不存在，且 19:06 前后后端无对应请求日志；前端修复后待用户复测确认是否复现。

## 2026-08-15（修复：STT 停止时识别文本重复）

- 用户验收反馈：说"我要仲裁"后停止，最终文本变成"我要仲裁我要仲裁"。
- 原因：停止录音时 Chrome 会重放已确认的最终结果，控制器未按结果下标去重；且中间结果只在非空时上报，停止合并时把已固化的预览又并入一次。
- 修复（仅 `sttController.ts`）：新增 `lastFinalIndex` 游标跳过已上报的最终结果（开始识别与 60s 自动重启时复位）；`onInterim` 无条件上报（空值清空预览）。
- 验证：`npx tsc --noEmit` 通过；3.7G 专项 31/31（新增去重守卫断言）。

## 2026-08-15（阶段 3.7G 验收通过并收尾）

- 用户浏览器验收通过：中文语音转文字进入同一 Session、回复朗读与打断、talk_normal 说话状态图、不支持语音的浏览器文字聊天不受影响。
- 验收期间修复两处：`DigitalHumanCompanion.tsx` 首行多余字符 `e`（编辑器误触导致编译失败）；STT 停止时识别文本重复（Chrome 重放最终结果 + 中间结果未清空，控制器按结果下标去重并始终上报中间结果）。
- 最终基线：3.7G 专项 31/31；`npx tsc --noEmit` 通过；历史回归 109/109 保持全绿。工作区改动未提交，由用户自行决定提交时机。
- 后端零改动：未修改路由、服务、模型、数据库、迁移、Runtime Graph、劳动规则与审批流程。

## 2026-08-15（数字人语音 Phase 1：AI 回复 → 句级 TTS → 连续播放）

- 新增后端独立语音层 `flask_app/services/voice/`（聊天/Agent/工作台逻辑零改动）：
  - `speech_text_normalizer.py`：展示文本→朗读文本，只变形式不变法律含义（Markdown 符号、URL→"链接"、括号去符号留内容、千分位 12,500→12500、百分比 30%→百分之30、emoji、空白归一）；法条编号/书名号/日期/金额保持原文；
  - `sentence_segmenter.py`：。！？；成句即产出；短碎片缓冲（防"根据""你的"级 TTS）；超长无标点按 80 字兜底截断；
  - `voice_profile.py`：法小助固定配置，仅环境变量 `VOICE_PROFILE_JSON`，密钥/ID 不硬编码；
  - `tts_provider.py`：TtsProvider 抽象（synthesize/cancel）+ 注册表，环境变量 `VOICE_TTS_PROVIDER` 启用；业务不依赖供应商 SDK；当前未接入任何第三方 Provider；
  - `voice_orchestrator.py`：按 requestId 隔离的句缓冲与 seq、primary/fallback 明确标记（Provider 异常→fallback 不拖垮聊天）、cancel 丢缓冲并联动 provider.cancel。
- SSE：`sse.py` 新增 `voice` 事件（seq/text/tts_mode/audio_b64/mime_type）；`digital_human_service.chat_stream` 新增 `voice` 参数，呈现层按句合成下发（delta 与 voice 交错，取消信号即停并 CANCELLED 收尾）；`cancel_request` 联动语音编排器；路由接受 `voice` 布尔字段。
- 前端：新增 `streamingAudioPlayer.ts`（队列播放、IDLE/BUFFERING/PLAYING/PAUSED/STOPPED/ERROR 状态机、onSpeechStart/End/Pause/Resume/Cancelled 事件预留、requestId 隔离丢弃迟到片段、单条错误跳过不卡队列）；`digitalHumanApi` 解析 voice 事件并构造 data URL；Store 接入播放器：发送即切换请求作用域、onVoice 双重开关守卫、停止/关闭/切会话清队列；`speechSynthesis` 保留为明确标注的 FALLBACK_TTS（voiceMode 字段区分，不静默混用）；气泡回放走播放器 fallback。
- 测试：新增 `test_digital_human_voice_phase1.py` 25/25（normalizer/segmenter/orchestrator 取消与降级/voice 事件序与 fallback 标记/呈现层取消/前端守卫）；3.7G 测试同步新契约（onVoice 入队守卫）；3.7F 取消与流式测试因契约扩展（voice 参数、cancel 联动）做兼容更新（假服务签名、注入 voice orchestrator）。
- 验证：`npx tsc --noEmit`、compileall、`git diff --check` 通过；全量回归 135 项复跑中。
- 边界：本阶段不实现 ASR、口型/Viseme、动画、聊天窗口重构；语音失败不影响文字/Agent/工作台。当前缺少正式 TTS Provider/API 凭证，语音以 fallback 模式运行，待用户确认候选 Provider 后再接入。

## 2026-08-15（语音 Phase 1：接入 Qwen DashScope TTS Provider）

- 用户提供 DashScope 工作区密钥与参数后接入正式 Provider（密钥未写入代码/.env，仅环境变量读取）：
  - `core/config.py` 新增语音 TTS 配置字段（DASHSCOPE_API_KEY/WORKSPACE_ID、TTS_PROVIDER/MODEL/VOICE/FORMAT/SAMPLE_RATE/RATE/VOLUME/TTS_WS_URL）；
  - 新增 `services/voice/provider/qwen_provider.py`：经查证 qwen-audio-3.0-tts-flash 不走 HTTP 接口，改用官方 dashscope SDK `SpeechSynthesizer`（WebSocket 协议，CosyVoice 同族）；format 按 TTS_FORMAT+TTS_SAMPLE_RATE 映射 AudioFormat 枚举，语速参数为 speech_rate；取消为迟到结果丢弃语义；
  - `requirements.txt` 新增 `dashscope>=1.26.0`（已安装到 law 环境）；`tts_provider.get_active_provider` 按 TTS_PROVIDER 环境变量激活；
  - orchestrator：多句合成之间检查取消（发现即停）；Provider 失败按请求锁存，该回复其余句子直接 fallback，不反复调用/刷日志。
- 真实 API 验证：默认全局 WS 地址合成成功（约 17KB mp3/句）；北京区域 MaaS 地址不通、multimodal-generation HTTP 接口 403/400（该模型不使用），最终采用 SDK 默认地址；端到端 orchestrator 产出 primary 模式语音片段。
- 测试：QwenProviderTest 以 sys.modules 注入假 SDK（参数映射/缺 Key 前置失败/空音频/取消丢弃/注册激活）；Phase 1 专项 32/32；全量回归复跑中。
- 待办：用户在 flask_app/.env 添加 DASHSCOPE 相关环境变量并重启后端后，浏览器验收 primary 语音链路。

## 2026-08-15（模块地图文档更新：数字人语音 + 相关扩展）

- 新增 `法律AI/模块地图/数字人语音.md`：3.7G 基础语音闭环 + Phase 1 句级神经 TTS 的完整模块地图（一级调用链/目的/调用链/关键状态/判断点/测试），顶部标注阶段状态与日期。
- 更新 `数字人对话.md`：一级调用链与调用链补入 voice=true 时的句级 voice 事件支线，交叉引用《数字人语音》。
- 更新 `服务端取消.md`：新增"Phase 1 语音取消扩展"小节（voice_orchestrator.cancel、呈现循环取消即停、前端 player.clear 与 requestId 双重隔离）；3.7F 取消测试数修正为 26 项并标注法源同步离线化。
- 工作流沉淀：`AI_WORKFLOW/WORKFLOW.md` 收尾规则新增"模块实现完成后更新 法律AI/模块地图 对应文档"。

## 2026-08-15（数字人最小全链路 Trace：trace_id 串联 会话→路由→案件→Agent）

- 用户裁定范围：3.7H 只做 Trace 链路追踪；Guardrails 与固定评测集不做。
- 新增 `services/conversation/tracing.py`：trace(event, trace_id, **fields) 以 JSONL 写 logs/trace.jsonl 并镜像 app.log（[trace] 前缀）；写入失败绝不抛异常；link_run/trace_for_run 维护 run_id↔trace_id 映射（Agent 步骤回溯，不侵入 Runtime）。
- 挂点：digital_human_service（request_start/question 30 字预览、request_error、request_cancelled）、orchestrator（request_replayed、route_decision、action_executed、request_completed、request_failed、request_cancelled）、actions（matter_created、run_started + link_run；execute 新增可选 request_id 参数，3.7F 测试 patch 兼容）。
- 过程中修复：ConversationAction 字段名是 action 而非 type（to_dict 才映射 "type"），挂点最初误用 action.type 致 AttributeError，已改为 action.action。
- 测试：新增 `test_digital_human_trace.py` 10/10（JSONL 写入与容错、run 关联、同 trace_id 全链事件序、取消事件、劳动动作 matter/run 事件与关联、三处挂点源码守卫）；全量回归 152/152；compileall、diff-check 通过。
- 模块文档：新增 `法律AI/模块地图/链路追踪.md`（按功能段模板，一级调用链可点击）。
- 边界：前端零改动；不改 Agent 业务逻辑；步骤级明细仍以 DB AgentRun.steps 为准。

## 2026-08-15（法小助前端布局重构 P1：视图骨架 + store 纯 UI 状态 + chat↔workspace 切换）

- 用户规格：普通聊天态（384×650 悬浮）保持不变，案件工作台从"聊天面板 920×760 展开态"改为独立全屏办理空间（顶部为原站导航留出 80px）；本 Patch 只搭骨架，不拆 MatterWorkspace、不改业务逻辑。
- `digitalHumanStore.ts`：新增纯 UI 状态 `workspaceOpen`（不持久化）与动作 `openWorkspace`/`closeWorkspace`——纯视图切换，**不 abort 在途 SSE、不清语音队列、不动 sessionId**；`close()` 同时复位 `workspaceOpen`（收起面板后重开回到聊天态）。
- 新增 `CaseWorkspaceShell.tsx`：全屏 Shell（`.dh-workspace-shell`，fixed 覆盖、top 80px 避开 TopNavbar z-50），头部"劳动纠纷办理中心 + 返回对话 + 收起"，中间区整体承载现有 `DigitalHumanMatterWorkspace`（max-width 960 居中，不复刻旧 920×760 布局）。
- `DigitalHumanFloat.tsx`：三态编排（launcher / 聊天 / 工作台）；聊天与工作台**双挂载、CSS 切换可见性**（`.dh-chat-hidden`）——工作台首次打开后常驻挂载，返回对话不卸载，MatterWorkspace 本地草稿（约 20 项 state）、在途上传（organize 180s）与聊天滚动位置不丢失；styled-jsx 只追加新 class（dh-chat-hidden/dh-workspace-shell-*/dh-workspace-in），已有 class 未删未改。
- `DigitalHumanChat.tsx`：删除本地 `workspaceExpanded` 与内嵌工作台/陪伴渲染；"案件工作台"按钮改调 `openWorkspace`；`dh-panel-expanded` 相关 CSS 保留未用（按 CODE_RULES 不删除已有 class）。`DigitalHumanCompanion` 暂无人渲染（P3 将演化为案件上下文助手）。
- 验证：`npx tsc --noEmit` 通过、`git diff --check` 通过；浏览器人工验收步骤已交付待用户执行。
- 边界：P2/P3/P4 未启动；`dh-panel-expanded` 死样式、工作台内部标题与 Shell 标题重复等收尾项留到 P4 处理。

## 2026-08-15（法小助前端布局重构 P2+P3+P4：阶段工作台 / 侧栏 / 案件上下文助手 / 移动端，一次完成）

- 用户确认追加约束并批准一次性完成全部 Patch：P2 只拆 UI/展示职责（业务 state 与跨阶段动作保留统一逻辑容器）；keep-mounted 非强制、按真实生命周期取舍；侧栏案件状态优先复用已有 API 字段、避免 N+1。
- `digitalHumanStore.ts`：新增纯前端 UI 状态（不持久化，partialize 不变）——`activeStage`（四阶段，类型 CaseStage + CASE_STAGE_LABELS）、`sidebarTab`、`assistantCollapsed`、`workspaceGoalDraft`（聊天"从当前对话创建案件"预填目标，用后即清）、`currentMatter`（matter_id/title/goal 简报，随 loadSession/applyWorkspaceContext/selectCurrentMatter 同步，供聊天入口卡片）。
- 新增 `useMatterWorkspace.ts` 统一逻辑容器：原 DigitalHumanMatterWorkspace 全部业务 state 与动作原样搬移（createMatter/confirmJurisdiction/organizeFile/analyze/runLaborWorkflow/approveLaborDraft/exportLaborDraft/restoreMatter/startNewMatter/removeMatter 等），新增 switchMaterialKind（原 UI 内联的格式切换逻辑收进容器）、`deriveCaseStage` 阶段推导（案件变化/恢复时按 workflow 状态：未确认法域→①、awaiting_information→③、awaiting_draft_approval/completed/blocked_authority→④、其余→②；用户手动切换优先）、侧栏案件状态批量补齐（getLaborDisputeWorkflow 并行 + 按 matterId 缓存 + 只补缺失，无逐行 N+1；matters 列表接口确认无 status 字段后采用）。
- 新增四个 Stage 纯展示组件（只接收 props，无业务逻辑）：`JurisdictionStage`（建案/目标/中国法域）、`MaterialStage`（上传/整理稿/已有与缺失材料）、`FactEvidenceStage`（候选与确认事实/时间线/原文出处/证据缺口/正式事实表单 + 启动分析）、`AnalysisDocumentStage`（规则分析/官方法源/期限/补偿估算/Agent 状态/**用户审批只在这里**/草稿/Word/PDF 导出）。
- 新增 `CaseWorkspaceShell`（重写 P1 壳）：桌面 = WorkspaceHeader + WorkspaceSidebar(250px，[会话][案件] Tab，会话≠案件文案 + 关联案件标注) + CaseStageNav(四阶段，顶部只展示进度) + CaseStageContent(只渲染当前 Stage) + 底部风险/人工复核/草稿声明 + DigitalHumanCaseAssistant(320px↔64px 可收起；只展示当前案件/阶段上下文；快捷操作经 Composer preset 预填、发送前用户确认，不代审批；返回对话)。
- `DigitalHumanChat.tsx`：`MatterEntryCard` 轻量案件入口——有关联案件显示状态卡片 + [继续办理→]；无当前案件时"案件工作台"按钮只展开轻量入口（从当前对话创建案件=预填最近一条用户问题/打开历史案件=侧栏案件页），不直接进完整工作台（用户规格）。
- `ConversationComposer.tsx`：新增可选 `preset`/`onPresetConsumed`/`focusSignal` props（助手快捷操作与"继续提问"聚焦），聊天入口原行为不变。
- 删除 `DigitalHumanMatterWorkspace.tsx`、`DigitalHumanCompanion.tsx`（逻辑已搬入容器/Stage/助手）；`DigitalHumanFloat.tsx` 的 styled-jsx 只保留 `dh-chat-hidden`（P1 临时 shell class 移入 Workspace.module.css），既有 class 未删未改；新增 `Workspace.module.css` 承载全部新组件样式 + ≤640px 移动端（侧栏抽屉、助手 Bottom Sheet/圆形入口、阶段横滚、底部声明隐藏）。
- 验证：`npx tsc --noEmit` 通过、`git diff --check` 通过；模块地图《工作台.md》重写前端信息架构并标日期、《数字人对话.md》补视图状态与入口说明。
- 遗留（待用户浏览器验收后按需处理）：`dh-panel-expanded` 等旧样式类与部分 dh-matter-* 全局类已无引用（按 CODE_RULES 保留未删）；工作台 Shell top 偏移写死 80px；焦点管理未做陷阱；移动端底部声明隐藏。

## 2026-08-16（布局重构返修：chat→workspace→minimize→chat 状态恢复修复）

- 复现链路逐段比较（Float 渲染分支 / isOpen / workspaceOpen / workspaceMounted / 挂载 / scrollTop）发现两处残留状态：
  1. `DigitalHumanFloat.workspaceMounted` 只置 true 从不复位：收起面板后重开，隐藏的工作台 Shell 永久驻留 DOM（多一个隐藏 role="dialog"），且每次重开白跑 matters/detail/workflow/法源库 4 个请求；
  2. 聊天消息视口在工作台打开期间被 display:none 隐藏，SSE 到达时滚动 effect 仍执行 scrollTo(0)（scrollHeight=0），返回对话后依赖不变不再重滚，聊天停在最旧消息。
- 只修状态恢复（未重构聊天/工作台/Agent Runtime）：
  - `DigitalHumanFloat.tsx`：workspaceMounted 生命周期改为 isOpen=false 时复位（工作台随面板卸载，与重构前行为一致；聊天↔工作台切换仍双挂载保草稿）；
  - `DigitalHumanChat.tsx`：滚动 effect 依赖增加 workspaceOpen，并在隐藏期间跳过滚动（scrollHeight=0 不再把 scrollTop 置 0），返回对话时恢复到底部。
- 附带发现（按用户"只修状态恢复"范围未修，记录待批）：助手面板 `dh-companion-messages` 缺 flex:1，消息较多时助手输入框可能被裁切（一行 CSS 可修）。
- 验证：`npx tsc --noEmit`、`git diff --check` 通过；浏览器回归场景见 CURRENT_TASK。

## 2026-08-16（局部修复：返回对话后聊天布局被压缩 / 内容横向裁切）

- 根因：MatterEntryCard 位于 .dh-messages 之外，返回对话后 currentMatterId 有值时案件卡成为 .dh-chat-column 的额外 Grid 行，持续挤占消息区高度；分流卡内长字符串（labor_case_analysis / awaiting_jurisdiction 等）在窄容器内无法换行导致横向撑开。
- 修复（仅两处，未动 Store/API/工作台业务/案件关联逻辑；保留 workspaceMounted 生命周期修复与 workspaceOpen 滚动保护）：
  - `DigitalHumanChat.tsx`：MatterEntryCard 移入 .dh-messages 滚动容器末尾（判断条件 currentMatterId || caseEntryExpanded 不变），案件卡随消息区滚动，不再占聊天主布局固定高度；
  - `LaborTriageCard.module.css`：.card 增加 min-width:0 / max-width:100% / box-sizing:border-box；.next p 增加 overflow-wrap:anywhere（最小防溢出，未用全局 overflow:hidden）。
- 尺寸：聊天窗 384×650 与移动端尺寸未动。
- 验证：`npx tsc --noEmit`、`git diff --check` 通过；浏览器验收（消息区高度恢复 / 入口卡在滚动区内可点击 / 长字符串换行 / 连续切换与收起重开无残留布局）待用户执行。

## 2026-08-16（案件工作台 UI 布局与信息层级优化：最小范围视觉收敛）

- 用户规格：不重新设计，在现有工作台上做视觉收敛；禁改业务逻辑/Agent/SSE/案件状态机/表单数据结构/接口协议；保持蓝白政务风。
- 阶段四重构（用户已完成部分，本条目合并记录）：`AnalysisDocumentStage.tsx` 改为工作台式信息层级（案件分析结论/争议焦点/风险待确认、可主张金额测算 details、仲裁申请草稿卡、已验证依据、运行详情折叠），配套 `Workspace.module.css` 新样式；`LaborRuleResults.tsx` 导出 `LABOR_ISSUE_LABELS`。
- 助手摘要化（用户已完成部分）：`DigitalHumanCaseAssistant.tsx` 新增导出 `buildCaseAssistantSummary`（判断/下一步/缺失待确认，只压缩既有案件结果不产生新判断），右栏改工作摘要 + 可折叠"最近上下文"；删除重复"返回对话"（统一保留顶部右上角）。
- 侧栏降噪（用户已完成部分 + 本次补齐）：当前会话独立分组、最近会话默认 4 条 + "查看全部会话（N）"、删除钮 hover/focus 显隐、案件列表当前案件置顶。
- 本次补齐（Claude）：
  - 三栏比例：左侧 250→200px、右侧 320→360px（收起 64px 不变）、中间 flex 剩余；shellBody 增加 12px 间距让三张卡片分离（移动端复位为 0）；
  - 侧栏新增"当前案件"置顶块（标题摘要 + 当前阶段 + 状态，读 store currentMatter/activeStage + matterStatuses）；会话/案件条目去卡片化（透明底、hover 高亮、标题 2 行 clamp）；
  - 阶段条主次层级：非当前阶段透明降权、当前阶段保持实心蓝、徽标弱化（"执行中"不再抢主阶段视觉）；
  - 表单橙色门控：`LaborDisputeForm` 新增 `highlightMissing` prop（默认 false）——未填写必填项只显示红色 *，橙色边框/黄底只在校验触发后点亮（用户点击"检查证据、期限和法源"且有缺失、或 Agent 处于 awaiting_information）；`FactEvidenceStage` 新增本地 UI 状态 validationAttempted，点击有缺失时只点亮定位、**绝不启动分析**（业务安全边界不变：loading/blocked_authority/awaiting_approval 仍按原条件禁用）；
  - 助手快捷操作补"相关法律依据"（preset 问题、发送前用户确认，2×2 排布）；助手身份区压缩（头像 34px、padding 收紧）；
- 验证：`npx tsc --noEmit`、`git diff --check` 通过；1920/1600/1440/1366 与移动端视觉验收待用户浏览器确认。

## 2026-09-03（开学演示：隐藏后续数字人及 Agent 工作台入口）

- 用户目标：继续使用当前完整项目演示，但不向他人展示后来新增的数字人及其内部 Agent/案件工作台，也不能从页面点击触发。
- 最小修改：移除 `frontend/src/app/layout.tsx` 对 `DigitalHumanFloat` 的 import 与全站挂载；数字人聊天、案件工作台和劳动争议 Agent 的前端触发链因此不进入 React 组件树。
- 保留边界：未删除数字人/Agent 源码，未修改后端、API、数据库、Store、SSE/TTS；原始项目在初始化提交中已有的 `/agents` 页面保持不变。
- 验证：`npx tsc --noEmit`、`npm run build` 与 `git diff --check` 全部通过；待浏览器人工确认全站不再显示数字人入口。

## 2026-09-04（演示部署配置）

- 用户目标：为快速演示准备最小部署配置，不连接服务器、不扩展生产架构。
- 实际修改：前端后端请求统一使用同源 `/api`；模拟法庭 WebSocket 根据当前页面协议生成 `ws://`/`wss://`；补齐 Flask、SQLAlchemy、PostgreSQL 驱动和 Gunicorn 依赖；新增前后端 Dockerfile、Docker Compose、Nginx 配置。
- 部署边界：后端固定单 worker 以保持进程内模拟法庭会话；PostgreSQL、上传文件、日志和 Chroma 使用 Docker volume 持久化；Nginx 转发 API、SSE 与 WebSocket。
- 验证：前端 `npx tsc --noEmit`、`npm run build` 通过；后端 `python -m compileall -q flask_app` 执行；`git diff --check` 需在提交前复核。

## 2026-09-07（恢复全站数字人入口）

- 用户目标：撤销开学演示期间的临时隐藏，恢复当前完整项目的数字人功能入口。
- 最小修改：在 `frontend/src/app/layout.tsx` 恢复 `DigitalHumanFloat` 的 import 与根布局挂载；点击行为继续复用原数字人聊天、劳动争议 Agent 和案件工作台链路。
- 保留边界：未修改数字人内部实现、Store、API、SSE/TTS、后端、数据库和原项目 `/agents` 页面；未触碰未跟踪的数字人素材目录。
- 验证：`npx tsc --noEmit`、`npm run build`、首页 HTTP 200 且“有法律问题？问问法小助”已渲染、`git diff --check` 全部通过；开发服务已重新启动在 3000 端口。

## 2026-09-07（数字人 Rive 可组合素材规范化）

- 用户目标：修正原数字人组件画布尺寸、坐标和锚点不一致，产出可在同一 Rive Artboard 直接叠加的透明 PNG 图层；保留原素材不覆盖。
- 新增 `frontend/digital-human/tools/build_rig_v2.py`：只使用原始带 Alpha 的 PNG 做确定性缩放、镜像、定位和表情切片，不再用生成式模型分别重绘组件。
- 新增 `frontend/digital-human/lvxiaozhi_rig_v2/`：统一为 `2000×2400` RGBA 画布，包含头壳、面屏、身体、双臂、双手、7 个眼睛状态、8 个嘴部状态、透明/浅色组合预览及 Rive 导入说明。
- Rive 统一参数：Artboard `2000×2400`；所有图层 `Position X=1000, Y=1200`、`Scale=100%`、`Rotation=0`，只切换一组眼睛与一组嘴部图层可见性。
- 验证：共 24 个 PNG，尺寸均为 `2000×2400`、模式均为 RGBA；除浅色预览外均检测到 `0–255` Alpha 范围；组合预览已人工检查。原始素材未修改。

## 2026-09-08（律小智新角色 AI 拆分源素材）

- 用户确认新的蓝白金法务制服 Q 版青年角色形象后，新增 `frontend/digital-human/law_xiaozhi/`，保留原有数字人素材目录不覆盖。
- 素材包含全身正稿、头部近景、身体/裸头/前后发基础层、3 组眉毛、6 组眼睛和 6 组嘴型，共 21 个透明 PNG。
- 已逐文件检查 PNG Alpha：最终交付文件均为 `Format32bppArgb` 且角点 Alpha 为 0；生成过程中出现的假透明棋盘格文件未纳入交付。
- 边界：本次仅生成并整理 Rive 输入源素材，未生成 `.riv`，未修改前端组件、Store、SSE、TTS、后端、API 或数据库；独立生成图层仍需在 Rive 中统一画布并人工校准锚点与边缘。

## 2026-09-08（修正律小智头身连接素材）

- 根据 Rive 拼装截图确认原 `head_base.png` 的脖子过长且下端外扩，单纯移动层级无法获得自然的衣领衔接。
- 新增 `frontend/digital-human/law_xiaozhi/head_base_v2.png`：保留原头型、耳朵、肤色和空白表情区域，只将脖子缩短、收窄并取消下端外扩；原图未覆盖。
- 验证：新旧头部素材均为 `1254×1254`；修正版为 `Format32bppArgb`，角点 Alpha 为 0，可作为透明 PNG 导入 Rive。
- 边界：未生成 `.riv`，未修改前端运行组件、Store、SSE、TTS、后端、API 或数据库。

## 2026-09-08（改为鼻子与脸底图一体素材）

- 独立鼻子层方案经拼装检查后被用户否决；此前生成的 `nose.png` 已移除，不再作为交付素材。
- 按用户要求改为鼻子与脸底图一体生成：新增 `frontend/digital-human/law_xiaozhi/head_base_v3.png`，基于短脖子的 `head_base_v2.png`，只在脸中央融合低对比度暖肤色短弧阴影，不含白色圆形高光、圆点、豆状块或独立竖线。
- `head_base_v3.png` 保持 `1254×1254` 透明画布、原头型、耳朵和短窄脖子；原 `head_base.png` 与 `head_base_v2.png` 均未覆盖。
- 边界：仅调整 Rive 输入源素材与说明，未修改前端运行逻辑或 `.riv` 配置。

## 2026-09-09（法小助 Rive 数字人最终接入）

- 将 `law-xiaozhi.riv` 与匹配的 `rive.wasm` 放入前端公共资源，接入 `@rive-app/react-webgl2@4.34.1`。
- 新增 `RiveDigitalHuman`，通过 `expression`、`speaking`、`blink` 绑定现有头像状态；PNG 仅用于加载期或失败回退。
- 悬浮入口、聊天和工作台使用 launcher / portrait / compact 矩形视口，移除正常 Rive 展示的圆形裁切、白色描边和旧光圈；隐藏视图不保留活跃 Rive Canvas。
- 主项目验证：`npx tsc --noEmit`、`git diff --check` 通过；桌面页面为 1 个 Rive Canvas、0 个 PNG，控制台无错误，悬浮入口与聊天面板均显示 `.riv` 蓝发人物。当前深色矩形背板来自 `.riv` 素材本身，移动端真实视口待验收。

## 2026-09-09（法小助无背景 Rive 正式资源替换）

- 资源：保留 `frontend/digital-human/law_xiaozhi/无背景.riv` 源文件，将其复制覆盖正式运行资源 `frontend/public/digital-human/law-xiaozhi/law-xiaozhi.riv`；已有旧资源副本 `untitled.riv` 未删除。源文件、运行文件和本地 Next 服务实际响应均为 5,150,645 bytes，SHA-256 为 `FE1EFD70967A31A1C9D83DF8E903E8B255300E2F173C6038ED55942E7EA7AAF8`。
- 可见性：`DigitalHumanAvatar` 在 `visible=false` 时不再挂载 PNG 回退节点，避免聊天与工作台双挂载时隐藏视图残留 PNG；重新可见时的加载期与 Rive 失败回退不变。未修改 `@rive-app/react-webgl2`、`rive.wasm`、Artboard/StateMachine/ViewModel 合同、`expression`/`speaking`/`blink` 映射、后端、API、SSE、TTS 或案件业务。
- 浏览器：重启 Next 开发服务后，右下角、聊天和工作台分别确认 1 个 Rive Canvas、0 个数字人 PNG；外层背景透明、无边框、无圆角裁切和旧光圈，控制台 0 error。
- 验证：`npx tsc --noEmit`、`git diff --check` 通过；`GET /digital-human/law-xiaozhi/law-xiaozhi.riv` 经本地 Next 服务返回 200 且哈希匹配。移动端真实视口仍待人工验收。

## 2026-09-09（拆分数字人咨询入口与案件工作台入口）

- 用户目标：数字人保持咨询助手心智，案件工作台不再依附于点击数字人后的内部入口。
- 入口调整：`TopNavbar` 在现有导航宽度内将“纠纷管理”整理为“案件与纠纷”，下拉菜单新增“案件工作台”独立入口；数字人聊天标题栏原“案件工作台”改为上下文动作“转入办理/继续办理”。
- 状态复用：`openWorkspace` 支持从关闭态初始化共享会话并直接打开工作台；聊天与工作台继续双挂载，Session、Matter、SSE、TTS、草稿、上传与滚动状态不拆分。
- 即时渲染：从顶栏直接进入时立即挂载 `CaseWorkspaceShell`，避免等待 effect 的空白帧。
- 边界：未修改后端、API、数据库、Agent Runtime、案件流程、审批或法律安全边界。
- 验证：`npx tsc --noEmit`、`git diff --check` 通过；浏览器确认独立入口、返回对话、数字人只开咨询和聊天转办文案。`npm run build` 受已有 Next 进程占用 `.next/trace` 阻塞，未停止用户进程，待空闲时补跑。

### 返工：跨页面跳转后工作台持续覆盖

- 复现证据：工作台打开时点击“合同审查”，URL 已切换到 `/contract`，合同页面 DOM 已加载，但根布局中的固定定位工作台仍保持可见，造成“卡住且跳转失败”的表象。
- 根因：`DigitalHumanFloat` 挂载在根布局，路由切换不会卸载；`workspaceOpen` 未随 `pathname` 变化复位。
- 最小修复：`DigitalHumanFloat` 记录上一条 `pathname`，检测到跨页面导航后调用现有 `close()`，统一复位 `isOpen/workspaceOpen`；不重复实现清理逻辑。
- 回归：重复“打开工作台 → 点击合同审查”，工作台自动收起，`/contract` 页面完整显示，数字人恢复为悬浮入口，浏览器控制台 0 error；`npx tsc --noEmit`、`git diff --check` 通过。
