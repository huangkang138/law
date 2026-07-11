# 项目上下文读取规则

本文件用于约束后续每次项目解析、项目修改、后端排查和文档更新时的上下文读取顺序。处理本仓库时，应优先遵守这里的路径和流程。

## 固定上下文路径

- 原始项目解析资料：`D:\项目\law\raw`
- 最新项目解析汇总：`D:\项目\law\newModify\latest-project-analysis.md`
- 修改追溯记录：`D:\项目\law\newModify\modification-log.md`

## 每次解析或修改前必须先读

1. 先读取 `D:\项目\law\raw` 下的项目解析文档。
2. 如果 `D:\项目\law\newModify\latest-project-analysis.md` 存在，再读取这份最新解析。
3. 如果任务涉及已有改动、历史方案或追溯，再读取 `D:\项目\law\newModify\modification-log.md` 中相关记录。
4. 最后再读取实际源码、配置和日志。项目解析文档用于加速理解，但最终以当前代码为准。

## 远程仓库改动触发规则

当用户表达类似以下意思时，应识别为“需要刷新最新项目解析”：

- “我推送了远程仓库”
- “远程仓库有新改动”
- “我已经提交/推送了”
- “代码更新了”
- “拉取最新后重新解析”
- “重新生成项目解析”

触发后应执行：

1. 读取 `D:\项目\law\raw` 下的解析资料。
2. 结合当前仓库代码、目录结构、关键配置和后端/前端入口重新解析项目。
3. 覆盖更新 `D:\项目\law\newModify\latest-project-analysis.md`，不要生成多个项目解析副本。
4. 在 `D:\项目\law\newModify\modification-log.md` 追加本次刷新记录。

## 后端优先阅读路线

查看后端时，优先按这个顺序：

1. `flask_app/app.py`：应用创建、CORS、数据库表创建、Blueprint 注册、WebSocket 注册、启动端口。
2. `flask_app/routers/__init__.py`：确认每个业务路由模块如何被导出。
3. `flask_app/routers/*.py`：按业务域查看接口。重点看 `legal.py`、`document.py`、`analysis.py`、`dispute.py`、`legal_tools.py`。
4. `flask_app/services/*.py`：查看 LLM、模拟法庭、WebSocket、案例搜索、RAG、文档解析等服务实现。
5. `flask_app/models/*.py`：查看 SQLAlchemy 表模型和 Pydantic 请求/响应模型。
6. `flask_app/core/config.py`、`flask_app/core/database.py`、`flask_app/core/logger.py`：查看环境配置、数据库连接和日志。
7. `sql/public.sql`：核对真实数据库结构、外键、索引和样例数据。

## 注意事项

- 不要把 `.env`、数据库密码、API Key 或其他敏感值写入新文档。
- 如果解析文档与源码不一致，以源码为准，并在最新解析中标注差异。
- 修改业务代码前，应先确认是否已有未跟踪或用户改动的文件，避免覆盖用户工作。
- 每次修改后都要按 `PROJECT_MODIFICATION_RULES.md` 记录时间、会话 ID、思路、方案、改动文件和验证情况。
