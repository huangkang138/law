"""劳动纠纷离线评测。离线考卷：检查 Agent 的判断是否符合预期"""


def load_cases(*args, **kwargs):
    from .runner import load_cases as _load_cases
    return _load_cases(*args, **kwargs)


def run_dataset(*args, **kwargs):
    from .runner import run_dataset as _run_dataset
    return _run_dataset(*args, **kwargs)


def load_flagship_cases(*args, **kwargs):
    from .flagship import load_flagship_cases as _load
    return _load(*args, **kwargs)


def run_flagship_dataset(*args, **kwargs):
    from .flagship import run_flagship_dataset as _run
    return _run(*args, **kwargs)


__all__ = ["load_cases", "run_dataset", "load_flagship_cases", "run_flagship_dataset"]
