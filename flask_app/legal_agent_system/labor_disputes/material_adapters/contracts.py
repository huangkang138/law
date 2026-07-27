from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class MaterialCandidate:
    field: str
    value: Any
    confidence: float
    quote: str
    start_offset: int
    end_offset: int
    document_type: str


class LaborMaterialAdapter(Protocol):
    document_type: str
    keywords: tuple[str, ...]

    def extract(self, text: str) -> list[MaterialCandidate]: ...
