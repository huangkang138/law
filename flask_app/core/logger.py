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

def _add_sink(sink, **kwargs):
    """优先使用异步日志队列；受限 Windows 环境无法建管道时同步降级。"""
    try:
        return logger.add(sink, enqueue=True, **kwargs)
    except PermissionError:
        return logger.add(sink, enqueue=False, **kwargs)


# 添加文件输出
_add_sink(
    settings.LOG_FILE,
    rotation=settings.LOG_ROTATION,
    retention=settings.LOG_RETENTION,
    level=settings.LOG_LEVEL,
    backtrace=True,
    diagnose=False,
)

# 添加控制台输出
_add_sink(
    sink=lambda msg: print(msg, end=""),
    level=settings.LOG_LEVEL,
    backtrace=True,
    diagnose=False,
)

# 应用日志实例
app_logger = logger
