"""展示文本 → 朗读文本：只改变朗读形式，不改变法律含义。

处理：Markdown 符号（#、**、列表符、代码围栏）、URL、括号、金额千分位、
百分比、emoji 与多余空白。法条编号（第 30 条）、书名号引用（《劳动合同法》）、
日期与数字保持原文，交给 TTS 引擎自然朗读。
"""

import re


class SpeechTextNormalizer:
    URL_PATTERN = re.compile(r"https?://[^\s，。！？；、）】]+", re.IGNORECASE)
    PERCENT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%")
    THOUSANDS_PATTERN = re.compile(r"(?<=\d),(?=\d{3}(?:\D|$))")
    EMOJI_PATTERN = re.compile(
        "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0000FE0F\U0000200D"
        "\U00002B00-\U00002BFF\U00002190-\U000021FF\U00002300-\U000023FF"
        "\U00002696]+"
    )

    @classmethod
    def normalize(cls, text: str) -> str:
        if not text:
            return ""
        # 展示层的 Markdown 语法符号一律不读出来。
        text = text.replace("**", "").replace("`", "").replace("~~", "")
        text = re.sub(r"^[#>\s]+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+[.、)]\s*", "", text, flags=re.MULTILINE)
        # URL 读出无意义，统一为"链接"；括号去掉但保留内容。
        text = cls.URL_PATTERN.sub("链接", text)
        for opening, closing in (("（", "）"), ("(", ")"), ("【", "】"), ("[", "]")):
            text = text.replace(opening, "").replace(closing, "")
        # 数字朗读形式：千分位去掉（12,500 → 12500）；百分比读"百分之30"。
        text = cls.THOUSANDS_PATTERN.sub("", text)
        text = cls.PERCENT_PATTERN.sub(r"百分之\1", text)
        # 字面量转义换行（若上游仍有残留）与多余空白。
        text = text.replace("\\n", " ").replace("\\t", " ").replace("\\r", " ")
        text = cls.EMOJI_PATTERN.sub("", text)
        return re.sub(r"\s+", " ", text).strip()
