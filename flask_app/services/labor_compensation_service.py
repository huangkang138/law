"""劳动经济补偿估算服务。

该服务从 legal_tools Router 下沉而来，供原计算器和法律 Agent 共同复用。
当前保持项目既有公式：月工资 ×（工作年限 + 额外月份 / 12）。
"""

import uuid
from typing import Dict

from core.database import SessionLocal
from models.db_models import LaborCompensation


class LaborCompensationService:
    """执行参数校验、补偿估算和历史记录持久化。"""

    @staticmethod
    def calculate(monthly_salary: float, years: int, months: int, save_record: bool = True) -> Dict:
        """按项目既有公式估算经济补偿，并返回可审计计算过程。"""
        monthly_salary = float(monthly_salary)
        years = int(years)
        months = int(months)
        if monthly_salary <= 0:
            raise ValueError("月工资必须大于 0")
        if years < 0 or months < 0 or months > 11:
            raise ValueError("工作年限不能为负数，额外月份应为 0 到 11")

        total_years = years + months / 12
        compensation = round(monthly_salary * total_years, 2)
        record_id = None
        if save_record:
            db = SessionLocal()
            try:
                record = LaborCompensation(
                    id=str(uuid.uuid4()), monthly_salary=f"{monthly_salary:.2f}",
                    years=years, months=months, compensation=f"{compensation:.2f}",
                )
                db.add(record)
                db.commit()
                record_id = record.id
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

        return {
            "record_id": record_id, "monthly_salary": monthly_salary,
            "years": years, "months": months, "total_years": round(total_years, 4),
            "compensation": compensation,
            "formula": "月工资 ×（工作年限 + 额外月份 ÷ 12）",
            "calculation": f"{monthly_salary:.2f} × ({years} + {months} ÷ 12) = {compensation:.2f}",
            "warning": "结果仅为基于当前项目既有公式的初步估算，未考虑工资上限、解除原因等具体法律条件。",
        }


_service = LaborCompensationService()


def get_labor_compensation_service() -> LaborCompensationService:
    """获取劳动补偿估算服务。"""
    return _service
