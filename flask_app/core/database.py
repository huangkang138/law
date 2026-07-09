"""
数据库连接配置
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import settings

# 数据库连接字符串
DATABASE_URL = f"postgresql://postgres:hkc20060606*@localhost:5432/sparklaw?client_encoding=utf8&application_name=sparklaw"

# 创建数据库引擎
engine = create_engine(DATABASE_URL, connect_args={'options': '-c client_encoding=utf8 -c standard_conforming_strings=on'})

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db():
    """
    获取数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
