# core/session_stats.py
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional
import time


@dataclass
class SessionStats:
    start_ts: float = 0.0
    end_ts: float = 0.0

    # Optional: session doesn't have a fixed total anymore
    target_total: int = 0

    answered_total: int = 0
    correct_total: int = 0
    wrong_total: int = 0  # ✅ NEW

    asked_by_type: Dict[str, int] = field(default_factory=dict)
    correct_by_type: Dict[str, int] = field(default_factory=dict)

    # (fi, en) -> mistakes in THIS session
    mistakes_map: Dict[Tuple[str, str], int] = field(default_factory=dict)

    def start(self, target_total: Optional[int] = None):
        """
        Start a new session (RAM-only).
        New behavior: target_total is optional (session ends when engine stops).
        Still keeps target_total for backward compatibility / UI display if needed.
        """
        self.start_ts = time.time()
        self.end_ts = 0.0

        self.target_total = int(target_total) if target_total is not None else 0

        self.answered_total = 0
        self.correct_total = 0
        self.wrong_total = 0  # ✅ NEW reset

        self.asked_by_type.clear()
        self.correct_by_type.clear()
        self.mistakes_map.clear()

    def stop(self):
        self.end_ts = time.time()

    def record_answer(self, qtype: str, fi: str, en: str, is_correct: bool):
        """
        Track:
        - answered_total
        - correct_total
        - wrong_total
        - mistakes_map (per word, this session only)
        - asked/correct by question type
        """
        self.answered_total += 1
        self.asked_by_type[qtype] = self.asked_by_type.get(qtype, 0) + 1

        if is_correct:
            self.correct_total += 1
            self.correct_by_type[qtype] = self.correct_by_type.get(qtype, 0) + 1
        else:
            self.wrong_total += 1  # ✅ NEW
            key = (fi, en)
            self.mistakes_map[key] = self.mistakes_map.get(key, 0) + 1

    def elapsed_mmss(self) -> str:
        if self.start_ts <= 0:
            return "00:00"
        end = self.end_ts if self.end_ts > 0 else time.time()
        secs = max(0, int(end - self.start_ts))
        mm = secs // 60
        ss = secs % 60
        return f"{mm:02d}:{ss:02d}"

    def accuracy_pct(self) -> float:
        if self.answered_total == 0:
            return 0.0
        return (self.correct_total / self.answered_total) * 100.0