# YYS-Law 最新项目解析

更新时间：2026-07-09 11:01:58 +08:00

本文件是后续项目解析和项目修改前需要优先阅读的最新汇总。它基于 `D:\项目\law\raw\项目解析报告.md` 与当前仓库只读检查生成。后续远程仓库更新或用户要求重新解析时，覆盖更新本文件，不再生成多个解析副本。

## 解析来源

- `D:\项目\law\raw\项目解析报告.md`
- `D:\项目\law\flask_app\app.py`
- `D:\项目\law\flask_app\routers\__init__.py`
- `D:\项目\law\flask_app\core\config.py`
- `D:\项目\law\flask_app\core\database.py`
- `D:\项目\law\requirements.txt`
- `flask_app/routers`、`flask_app/services`、`flask_app/models` 的结构扫描

## 当前项目定位

本项目是一个智能法务服务平台，主要包含法律咨询、合同审查、模拟法庭、案情分析、相似案例/文书、纠纷处理、法律文书起草、法律工具计算、知识图谱和智能体管理等功能。

当前技术栈概览：

- 前端：Next.js、React、TypeScript、Tailwind CSS、Zustand。
- 后端：Flask、Flask-CORS、Flask-Sock、SQLAlchemy、Loguru、LangChain、OpenAI-compatible Chat API。
- 数据库：PostgreSQL。
- AI：通过 OpenAI-compatible 接口调用 DeepSeek 类模型。
- 实时能力：合同审查使用 SSE，模拟法庭/语音庭审使用 WebSocket。

## 后端怎么看

后端入口是 `flask_app/app.py`，不是 FastAPI 入口。阅读后端建议按以下顺序：

1. `flask_app/app.py`
   - 创建 Flask app。
   - 配置 CORS。
   - 初始化 Flask-Sock。
   - 调用 `Base.metadata.create_all(bind=engine)` 检查/创建数据库表。
   - 注册各业务 Blueprint。
   - 注册 `/api/courtroom/ws/<session_id>` WebSocket。
   - 默认监听 `0.0.0.0:8001`。

2. `flask_app/routers/__init__.py`
   - 汇总导出 `analysis_bp`、`case_bp`、`dispute_bp`、`document_bp`、`document_drafting_bp`、`health_bp`、`knowledge_graph_bp`、`legal_bp`、`legal_tools_bp`、`favorites_bp`、`agent_bp`。

3. `flask_app/routers`
   - `health.py`：健康检查。
   - `legal.py`：法律咨询、会话查询、删除、重命名。
   - `document.py`：合同上传、合同审查、合同历史、SSE 流式审查。
   - `analysis.py`：模拟法庭、案情分析、相似文书、历史记录。
   - `dispute.py`：纠纷整理、取证、维权路径、文书生成、预测、提醒、风险预警。
   - `case.py`：相似案例搜索和历史。
   - `knowledge_graph.py`：知识图谱、节点、关系、结构、搜索和构建。
   - `document_drafting.py`：法律文书、合同、法律意见起草记录。
   - `legal_tools.py`：利息、劳动、交通事故、诉讼费、工伤、律师费、日历、时效、违约金、保全费、执行费、遗嘱、公证/公告、鉴定、仲裁、UML 等工具。
   - `favorites.py`：收藏。
   - `agent.py`：智能体 CRUD、聊天、使用统计、预设初始化。

4. `flask_app/services`
   - `legal_agent.py`：普法问答、会话上下文、LLM 调用、文书草拟。
   - `llm_factory.py`：LangChain ChatOpenAI 实例创建和 LLM 配置读取。
   - `courtroom_engine.py`：模拟法庭核心流程。
   - `courtroom_websocket_service.py`：WebSocket 庭审实时流程。
   - `case_service.py`：案例搜索、历史和详情。
   - `web_search_service.py`：当前更像内置模拟案例服务，不应直接理解为真实联网搜索。
   - `rag_service.py`：当前更像内存检索示例，不是真正落地的向量数据库检索。
   - `document_parser.py`、`contract_reviewer.py`、`debate_agent.py`：部分是简化或早期实现。

5. `flask_app/models`
   - `db_models.py`：主要 SQLAlchemy 表模型。
   - `knowledge_graph.py`：知识图谱相关模型和枚举。
   - `request.py`、`response.py`：Pydantic 请求和响应模型。

6. `flask_app/core`
   - `config.py`：从 `.env` 读取应用、LLM、CORS、日志配置。
   - `database.py`：创建 SQLAlchemy engine 和 session。
   - `logger.py`：Loguru 日志配置。

7. `sql/public.sql`
   - 用于核对 PostgreSQL 表结构、外键、索引和样例数据。

## 运行方式推断

后端：

```powershell
python flask_app/app.py
```

默认端口：`8001`

前端：

```powershell
cd frontend
npm run dev
```

默认端口：`3000`

前端 `next.config.js` 中存在 `/api/:path*` 到 `http://localhost:8001/api/:path*` 的 rewrite，但项目里仍可能存在直接写死 `localhost:8001` 的请求。

## 数字人智能助手现状

项目已新增全局数字人智能助手“法小助”的第一版前后端闭环，定位为全局导航、简单问答和专业功能分流，不属于复杂的工具调用型 Agent。

后端：

- `flask_app/routers/digital_human.py`：提供 `POST /api/digital-human/chat` 与 `POST /api/digital-human/reset`。
- `flask_app/services/digital_human_service.py`：复用 `LLMFactory` 调用 DeepSeek，拼接系统提示词、最近 6 条历史和当前问题，聚合流式输出并解析 `reply`、`intent`、`emotion`、`confidence`。
- 意图只允许从后端白名单中选择；后端根据意图补充 `route` 与 `route_label`，置信度低于 0.6 时不返回跳转地址。
- `flask_app/routers/__init__.py` 和 `flask_app/app.py` 已导出并注册数字人 Blueprint。
- `flask_app/models/db_models.py` 中已有 `DigitalHumanSession` 与 `DigitalHumanMessage` 模型，并补充了 `Float` 类型供 `confidence` 字段使用。
- 当前 `DigitalHumanService` 仍使用内存字典保存会话上下文，数据库模型尚未接入聊天、查询、重置和删除流程。

前端：

- `frontend/src/components/DigitalHuman/`：包含悬浮入口、聊天面板和状态头像组件。
- `frontend/src/store/digitalHumanStore.ts`：使用 Zustand 持久化当前 `session_id` 与消息。
- `frontend/src/services/digitalHumanApi.ts`：封装数字人聊天和重置请求。
- `frontend/src/app/layout.tsx`：全局挂载数字人悬浮组件。
- `frontend/public/digital-human/first-gen/`：存放 8 张数字人状态图；当前通过状态图切换、呼吸、浮动、淡入和思考脉冲形成动态效果，不是逐帧或骨骼动画。

本地联调注意：Windows 环境可能将 `localhost` 优先解析为 IPv6 回环地址 `::1`，而 Flask 当前监听 `0.0.0.0:8001`（IPv4）。如果 Next.js 代理出现 `ECONNREFUSED ::1:8001`，应让代理明确使用 `127.0.0.1:8001`，并重启前端开发服务器。

## 当前重要风险点

1. `requirements.txt` 标题和部分依赖仍偏 FastAPI，但当前主入口是 Flask。依赖清单需要与真实后端同步。
2. `flask_app/core/database.py` 存在硬编码数据库连接信息。后续文档和提交不要泄露具体密码，应迁移到环境变量。
3. 多个业务模块复用 `/document/...` 路径，合同审查、纠纷文书、文书起草之间存在命名混淆风险。
4. `document.py`、`analysis.py`、`dispute.py`、`legal_tools.py` 文件较大，业务逻辑、LLM 调用、数据库操作混在 router 中，后续维护可以逐步下沉到 service 层。
5. 状态来源混合使用浏览器 localStorage、后端内存字典和 PostgreSQL。服务重启、多实例部署或历史同步时可能出现不一致。
6. `raw` 中旧报告提到当前目录不是 Git 仓库，但现在 `D:\项目\law` 已识别为 Git 仓库，当前分支为 `master`。后续应以当前 Git 状态为准。
7. 数字人会话目前同时存在后端内存和浏览器 Zustand 两个状态源；数据库模型已经定义但尚未接入，因此后端重启后无法依靠数据库恢复上下文。
8. 数字人匿名会话尚未实现用户或浏览器级归属隔离；开放后端历史会话列表前必须补充 `user_id`/客户端标识过滤，避免不同匿名用户互相读取记录。

## 后续解析和修改规则

- 每次项目解析或修改前，先读 `D:\项目\law\raw`，再读本文件。
- 每次远程仓库更新后，覆盖刷新本文件。
- 每次修改后，追加更新 `D:\项目\law\newModify\modification-log.md`。
- 涉及后端时，优先从 `flask_app/app.py` 和 `flask_app/routers` 进入，再追踪到 `services`、`models`、`core` 和 `sql`。
