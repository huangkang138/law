"""从叙述式材料补充可定位的劳动争议表单候选，不作法律判断。"""

import re

from .common import DATE, MONEY, first, iso_date


class NarrativeSummaryAdapter:
    document_type = "narrative_summary"

    def extract(self, text: str):
        candidates = []

        def add(field, pattern, transform=lambda match: match.group(1), confidence=0.85):
            item = first(text, field, pattern, self.document_type, transform, confidence)
            if item is not None:
                candidates.append(item)

        add("employee_name", r"申请人\s*([\u4e00-\u9fa5·]{2,10})(?=于|在|系|，|。)")
        add(
            "termination_date",
            rf"{DATE}\s*[，,]?\s*公司[^。；\n]{{0,100}}解除劳动合同",
            lambda match: iso_date(match),
            0.8,
        )
        add(
            "termination_reason",
            r"公司以[“\"']?([^”\"'，。；\n]{2,80})[”\"']?为由[^。；\n]{0,60}解除劳动合同",
            confidence=0.87,
        )
        add(
            "termination_initiator",
            r"公司[^。；\n]{0,80}(?:通知|决定)[^。；\n]{0,40}解除劳动合同",
            lambda _match: "employer",
        )
        add("employment_active", r"劳动关系(?:现已|已经|已)(?:解除|终止)", lambda _match: "false")
        add(
            "wages_paid_through",
            rf"(?:已支付工资至|工资已支付至)\s*{DATE}",
            lambda match: iso_date(match),
            0.92,
        )
        add(
            "wage_arrears_start_date",
            r"(20\d{2})年(\d{1,2})月工资(?:(?!已支付)[^。；\n]){0,80}(?:尚未支付|未支付|拖欠)",
            lambda match: f"{int(match.group(1)):04d}-{int(match.group(2)):02d}-01",
            0.7,
        )
        add(
            "wage_arrears_amount",
            rf"(?:尚未支付|未支付|欠付|拖欠)[^。；\n]{{0,20}}(?:合计|共计|总计)\s*{MONEY}",
            lambda match: float(match.group(1)),
            0.9,
        )
        add(
            "wage_payment_day",
            r"每月\s*(\d{1,2})\s*日[^。；\n]{0,12}(?:发放|支付)[^。；\n]{0,8}工资",
            lambda match: int(match.group(1)),
        )
        add("working_hours_system", r"(?<!未)(?:实行|采用|约定)[^。；\n]{0,8}标准工时制", lambda _match: "standard")
        for field, day_type in (
            ("overtime_workday_hours", "工作日"),
            ("overtime_rest_day_hours", "休息日"),
            ("overtime_statutory_holiday_hours", "法定节假日"),
        ):
            add(
                field,
                rf"{day_type}加班\s*(\d+(?:\.\d+)?)\s*小时",
                lambda match: float(match.group(1)),
                0.9,
            )
        add("rest_day_compensatory_leave_hours", r"(?:未安排|没有安排|未给予)补休", lambda _match: 0)
        add("overtime_paid_amount", r"(?:未支付|没有支付)加班费", lambda _match: 0)
        add(
            "compensation_kind",
            r"(?:拟请求|仲裁请求|请求|主张)[^。；\n]{0,80}违法解除[^。；\n]{0,30}赔偿金",
            lambda _match: "damages",
        )
        add("demands", r"(?:拟请求|仲裁请求)[：:]\s*([^。\n]+)")
        return candidates
