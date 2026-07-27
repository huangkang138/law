"""YYS-Law Alembic 环境配置。"""

from logging.config import fileConfig

from alembic import context

from core.database import Base, engine
import models.db_models  # noqa: F401，注册业务表元数据
import models.knowledge_graph  # noqa: F401，注册知识图谱表元数据
import legal_agent_system.models  # noqa: F401，注册 Agent 版本、事件与法源同步表


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 连接信息只取自项目数据库配置，不写入 alembic.ini。
config.set_main_option("sqlalchemy.url", engine.url.render_as_string(hide_password=False).replace("%", "%%"))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
