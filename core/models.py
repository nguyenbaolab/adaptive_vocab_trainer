from dataclasses import dataclass
from typing import List, Optional


@dataclass
class VocabItem:
    fi: str
    en: str
    error_count: int = 0


@dataclass
class Question:
    qtype: str
    prompt: str
    options: Optional[List[str]] = None
    correct_index: Optional[int] = None
    accepted_answers: Optional[List[str]] = None