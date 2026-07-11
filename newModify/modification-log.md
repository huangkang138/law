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
