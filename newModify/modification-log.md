# 项目修改记录

本文件用于持续记录每次项目解析、文档修改、代码修改和配置调整。后续默认追加到本文件，便于按时间和会话追溯。

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
