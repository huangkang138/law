"""劳动纠纷离线评测。离线考卷：检查 Agent 的判断是否符合预期"""


def load_cases(*args, **kwargs):
    from .runner import load_cases as _load_cases
    return _load_cases(*args, **kwargs)


def run_dataset(*args, **kwargs):
    from .runner import run_dataset as _run_dataset
    return _run_dataset(*args, **kwargs)


__all__ = ["load_cases", "run_dataset"]
