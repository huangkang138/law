"""劳动争议标签的稳定契约与用户输入归一化。"""

from typing import Iterable, List


WAGE_ARREARS = "wage_arrears"
TERMINATION = "termination"
ECONOMIC_COMPENSATION = "economic_compensation"
PROBATION = "probation"

ALLOWED_DISPUTE_TAGS = (
    WAGE_ARREARS,
    TERMINATION,
    ECONOMIC_COMPENSATION,
    PROBATION,
)

_TAG_ALIASES = {
    WAGE_ARREARS: WAGE_ARREARS,
    "欠薪": WAGE_ARREARS,
    "拖欠工资": WAGE_ARREARS,
    "工资支付": WAGE_ARREARS,
    "劳动报酬": WAGE_ARREARS,
    TERMINATION: TERMINATION,
    "unlawful_termination": TERMINATION,
    "解除": TERMINATION,
    "违法解除": TERMINATION,
    "辞退": TERMINATION,
    "解雇": TERMINATION,
    ECONOMIC_COMPENSATION: ECONOMIC_COMPENSATION,
    "compensation": ECONOMIC_COMPENSATION,
    "经济补偿": ECONOMIC_COMPENSATION,
    "补偿金": ECONOMIC_COMPENSATION,
    "赔偿金": ECONOMIC_COMPENSATION,
    PROBATION: PROBATION,
    "probation_period": PROBATION,
    "试用期": PROBATION,
    "试用期工资": PROBATION,
    "试用期解除": PROBATION,
}


def normalize_dispute_tags(values: Iterable[str]) -> List[str]:
    """转为稳定标签；任何未知值都失败关闭，禁止静默丢失争议。"""
    normalized = set()
    unknown = []
    for raw in values:
        value = str(raw).strip()
        if not value:
            continue
        tag = _TAG_ALIASES.get(value)
        if tag is None:
            unknown.append(value)
        else:
            normalized.add(tag)
    if unknown:
        raise ValueError(f"未注册的劳动争议标签: {', '.join(sorted(set(unknown)))}")
    return [tag for tag in ALLOWED_DISPUTE_TAGS if tag in normalized]


def dispute_tags_from_facts(facts: dict) -> List[str]:
    """显式标签优先；未提供时兼容现有中文 claim_types。"""
    explicit = list(facts.get("dispute_tags") or [])
    claims = list(facts.get("claim_types") or [])
    return normalize_dispute_tags([*explicit, *claims] if explicit else claims)
