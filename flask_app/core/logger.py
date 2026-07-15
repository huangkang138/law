"""
日志配置模块
"""

import os
from loguru import logger
from core.config import settings

# 确保日志目录存在
log_dir = os.path.dirname(settings.LOG_FILE)
if log_dir:
    os.makedirs(log_dir, exist_ok=True)

# 配置日志
logger.remove()  # 移除默认配置

# 添加文件输出
logger.add(
    settings.LOG_FILE,
    rotation=settings.LOG_ROTATION,
    retention=settings.LOG_RETENTION,
    level=settings.LOG_LEVEL,
    enqueue=True,
    backtrace=True,
    diagnose=False
)

# 添加控制台输出
logger.add(
    sink=lambda msg: print(msg, end=""),
    level=settings.LOG_LEVEL,
    enqueue=True,
    backtrace=True,
    diagnose=False
)

# 应用日志实例
app_logger = logger
