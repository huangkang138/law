"""增量句级切分：完整句立即产出，短碎片先缓冲，超长无标点兜底截断。

避免"根据""你的""情况"这类碎片级 TTS：不成句的短文本留在缓冲里，
等下一个句末标点（。！？；）或达到最大长度时才切出一个可朗读片段。
"""

SENTENCE_ENDERS = "。！？；"
DEFAULT_MAX_SENTENCE_CHARS = 80
DEFAULT_MIN_SENTENCE_CHARS = 2


class SentenceSegmenter:
    def __init__(
        self,
        max_chars: int = DEFAULT_MAX_SENTENCE_CHARS,
        min_chars: int = DEFAULT_MIN_SENTENCE_CHARS,
    ) -> None:
        self.max_chars = max_chars
        self.min_chars = min_chars
        self._buffer = ""

    def push(self, text: str) -> list:
        """喂入增量文本，返回本次新完成的句子（可能为空列表）。"""
        if not text:
            return []
        self._buffer += text
        sentences = []
        while True:
            cut = self._find_cut()
            if cut < 0:
                break
            candidate = self._buffer[:cut].strip()
            self._buffer = self._buffer[cut:]
            if candidate and len(candidate) >= self.min_chars:
                sentences.append(candidate)
        return sentences

    def flush(self) -> list:
        """请求结束时取回缓冲区剩余文本（无句末标点的尾巴）。"""
        rest = self._buffer.strip()
        self._buffer = ""
        if not rest:
            return []
        return [rest]

    def _find_cut(self) -> int:
        for index, char in enumerate(self._buffer):
            if char in SENTENCE_ENDERS:
                return index + 1
        if len(self._buffer) >= self.max_chars:
            return self.max_chars
        return -1
