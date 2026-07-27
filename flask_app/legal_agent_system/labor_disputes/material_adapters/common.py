import re
from typing import Any

from .contracts import MaterialCandidate


DATE = r"(20\d{2})[年/-](\d{1,2})[月/-](\d{1,2})日?"
MONEY = r"(\d+(?:\.\d+)?)\s*元"


def iso_date(match: re.Match, offset: int = 1) -> str:
    return f"{int(match.group(offset)):04d}-{int(match.group(offset + 1)):02d}-{int(match.group(offset + 2)):02d}"


def candidate(field: str, value: Any, confidence: float, match: re.Match, document_type: str) -> MaterialCandidate:
    return MaterialCandidate(
        field=field,
        value=value,
        confidence=confidence,
        quote=match.group(0).strip(),
        start_offset=match.start(),
        end_offset=match.end(),
        document_type=document_type,
    )


def first(text: str, field: str, pattern: str, document_type: str, transform=lambda m: m.group(1).strip(), confidence: float = 0.9):
    match = re.search(pattern, text, re.I)
    return candidate(field, transform(match), confidence, match, document_type) if match else None


def collect(*items):
    return [item for item in items if item is not None]
