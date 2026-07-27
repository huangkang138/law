# Agent 数据库迁移基线

当前仓库已有长期运行的 PostgreSQL 结构，因此首个 revision 是“接管基线”，不重复创建或删除旧表。

现有数据库首次接入：

```powershell
cd flask_app
alembic stamp 20260713_0001
alembic current
```

之后所有结构变更必须新增 revision，并通过 `alembic upgrade head` 验证。首个基线不负责初始化空数据库；在生成可审计的完整初始迁移前，空库仍沿用现有初始化流程。
