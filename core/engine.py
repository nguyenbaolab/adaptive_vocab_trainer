import random
import re
from collections import deque
from typing import Dict, List, Optional, Tuple

from .models import VocabItem, Question
from .storage import save_error_counts


class QType:
    MC_FI_TO_EN = "MC_FI_TO_EN"
    MC_EN_TO_FI = "MC_EN_TO_FI"
    TYPE_EN_TO_FI = "TYPE_EN_TO_FI"


class QuizEngine:
    """
    Session-based engine (no history):
    - Each session starts fresh: wrong.txt overwritten (session-state only).
    - First pass: new words are the priority. Debt words are interleaved
      probabilistically — NOT immediately when eligible.
      - Probability of reviewing a debt word increases as session progresses
        and as debt accumulates, but new words always stay dominant early on.
      - If correct on first pass: never repeated in this session.
      - If wrong: adds debt. Spacing (min gap) still applies before eligible.
    - After first pass ends: debt-only until debt = 0.
      - Special case: if only ONE debt word remains, repeat consecutively until cleared.
    - wrong.txt stores remaining debt per word (session-only, not lifetime).
    """

    def __init__(
        self,
        vocab: List[VocabItem],
        enabled_types: Optional[List[str]] = None,
        session_total: int = 30,
        recent_limit: int = 15,
        ignore_case: bool = True,
        ignore_punct: bool = True,
        spacing: int = 4,  # increased: min gap before same debt word can reappear
    ):
        if len(vocab) < 4:
            raise ValueError("Need at least 4 vocabulary items for multiple-choice questions.")

        self.vocab = vocab
        self.enabled_types = enabled_types or [
            QType.MC_FI_TO_EN,
            QType.MC_EN_TO_FI,
            QType.TYPE_EN_TO_FI,
        ]
        if not self.enabled_types:
            raise ValueError("At least one question type must be enabled.")

        self.target_words = max(1, int(session_total))
        self.target_words = min(self.target_words, len(self.vocab))

        # Safety cap only
        self.max_questions = max(200, self.target_words * 50)

        self.recent = deque(maxlen=int(recent_limit))
        self.ignore_case = bool(ignore_case)
        self.ignore_punct = bool(ignore_punct)
        self.spacing = max(0, int(spacing))

        # scoreboard
        self.correct = 0
        self.total = 0
        self.current: Optional[Question] = None

        # session pool
        self.session_words: List[VocabItem] = []
        self._new_index: int = 0  # how many new words already introduced

        # debt system (session-only)
        self.repeats_left: Dict[Tuple[str, str], int] = {}
        self.session_wrong_count: Dict[Tuple[str, str], int] = {}
        self.next_due: Dict[Tuple[str, str], int] = {}

        # qtype bag
        self._bag: List[str] = []
        self._bag_index = 0

        self.reset_session()

    # ---------------------------
    # Public
    # ---------------------------
    def reset_session(self):
        self.correct = 0
        self.total = 0
        self.current = None
        self.recent.clear()

        # fixed pool for session
        self.session_words = random.sample(self.vocab, self.target_words)
        random.shuffle(self.session_words)
        self._new_index = 0

        # reset debt (session-only)
        self.repeats_left.clear()
        self.session_wrong_count.clear()
        self.next_due.clear()

        # refresh wrong.txt (session-only)
        for it in self.vocab:
            it.error_count = 0
        save_error_counts(self.vocab)

        self._refill_bag()

    def next_question(self) -> Question:
        if self.total >= self.max_questions:
            raise StopIteration("Session finished (safety cap reached).")

        if self._is_session_done():
            raise StopIteration("Session finished.")

        qtype = self._next_qtype()
        item = self._choose_item_for_next()

        if qtype == QType.MC_FI_TO_EN:
            q = self._make_mc_question(
                qtype=qtype,
                item=item,
                prompt=item.fi,
                correct_value=item.en,
                distractor_field="en",
            )
        elif qtype == QType.MC_EN_TO_FI:
            q = self._make_mc_question(
                qtype=qtype,
                item=item,
                prompt=item.en,
                correct_value=item.fi,
                distractor_field="fi",
            )
        elif qtype == QType.TYPE_EN_TO_FI:
            accepted = self._split_answers(item.fi)
            q = Question(
                qtype=qtype,
                prompt=item.en,
                accepted_answers=accepted,
            )
            q.item = item
        else:
            raise ValueError(f"Unknown question type: {qtype}")

        self.current = q
        return q

    def submit_mc(self, chosen_index: int):
        q = self._require_current()
        if q.options is None or q.correct_index is None:
            raise RuntimeError("Current question is not multiple-choice.")

        is_correct = (chosen_index == q.correct_index)
        correct_answer = q.options[q.correct_index]

        self._apply_result(q.item, is_correct)

        if is_correct:
            return True, "Correct ✅", correct_answer
        return False, f"Not quite 🙂  Correct answer: {correct_answer}", correct_answer

    def submit_typing(self, user_text: str):
        q = self._require_current()
        if not q.accepted_answers:
            raise RuntimeError("Current question is not typing.")

        user_norm = self._normalize(user_text)
        accepted_norm = [self._normalize(a) for a in q.accepted_answers]
        is_correct = (user_norm in accepted_norm)

        correct_answer = q.accepted_answers[0]
        self._apply_result(q.item, is_correct)

        if is_correct:
            return True, "Correct ✅", correct_answer
        return False, f"Not quite 🙂  Correct answer: {correct_answer}", correct_answer

    # ---------------------------
    # Bag
    # ---------------------------
    def _refill_bag(self):
        repeats = 6
        bag = []
        for _ in range(repeats):
            bag.extend(self.enabled_types)
        random.shuffle(bag)
        self._bag = bag
        self._bag_index = 0

    def _next_qtype(self) -> str:
        if self._bag_index >= len(self._bag):
            self._refill_bag()
        t = self._bag[self._bag_index]
        self._bag_index += 1
        return t

    # ---------------------------
    # Stop condition
    # ---------------------------
    def _is_session_done(self) -> bool:
        if self._new_index < len(self.session_words):
            return False
        return self._total_debt() == 0

    def _total_debt(self) -> int:
        return sum(v for v in self.repeats_left.values() if v > 0)

    def _debt_keys(self) -> List[Tuple[str, str]]:
        return [k for k, v in self.repeats_left.items() if v > 0]

    # ---------------------------
    # Selection (PROBABILISTIC INTERLEAVE)
    # ---------------------------
    def _choose_item_for_next(self) -> VocabItem:
        """
        Phase 1 — new words remain:
          Debt words are reviewed probabilistically, NOT greedily.
          P(review debt) is computed dynamically:
            - Starts low (~15%) early in session → rises toward ~50% near end.
            - Increases slightly when many debt words are accumulating.
            - Debt words must still satisfy spacing before they are eligible.
          This ensures new words stay dominant throughout phase 1, while
          debt words are spread out naturally rather than bunched up.

        Phase 2 — all new words introduced:
          Pure debt-clearing with spacing. If only one debt word remains,
          it is repeated consecutively until cleared (no other words to space with).
        """
        next_q_num = self.total + 1
        debt_keys = self._debt_keys()
        new_words_left = self._new_index < len(self.session_words)

        # ── Phase 1: still have new words ────────────────────────────────────
        if new_words_left:
            eligible = [
                k for k in debt_keys
                if next_q_num >= self.next_due.get(k, 0)
            ]

            if eligible:
                # Dynamic probability: how likely are we to review debt now?
                #   progress:     0.0 (start) → 1.0 (all new words introduced)
                #   debt_count:   how many distinct debt words are eligible
                #
                # Formula: p_review = base + debt_bonus
                #   base       = 0.15 + 0.35 * progress  (0.15 early → 0.50 late)
                #   debt_bonus = min(0.15, eligible_count * 0.04)
                #
                # Result range: ~0.15 (start, 1 debt word) → ~0.65 (end, many debt)
                # New words are still favored for the majority of phase 1.
                progress = self._new_index / len(self.session_words)
                base = 0.15 + 0.35 * progress
                debt_bonus = min(0.15, len(eligible) * 0.04)
                p_review = min(base + debt_bonus, 0.65)

                if random.random() < p_review:
                    return self._pick_debt_word(eligible, next_q_num)

            # Default: introduce the next new word
            return self._pick_new_word()

        # ── Phase 2: no new words left → debt-only ───────────────────────────
        if not debt_keys:
            # Fallback — should not happen if _is_session_done() is correct
            return random.choice(self.session_words)

        # Only one debt word left: repeat it consecutively (no one else to space with)
        if len(debt_keys) == 1:
            item = self._find_item_by_key(debt_keys[0])
            return self._return_item(item or random.choice(self.session_words))

        # Multiple debt words: respect spacing
        eligible = [k for k in debt_keys if next_q_num >= self.next_due.get(k, 0)]
        if eligible:
            return self._pick_debt_word(eligible, next_q_num)

        # None eligible yet → pick soonest due (soft spacing: never block forever)
        debt_keys.sort(key=lambda k: self.next_due.get(k, 0))
        item = self._find_item_by_key(debt_keys[0])
        return self._return_item(item or random.choice(self.session_words))

    # ---------------------------
    # Selection helpers
    # ---------------------------
    def _pick_new_word(self) -> VocabItem:
        item = self.session_words[self._new_index]
        self._new_index += 1
        return self._return_item(item)

    def _pick_debt_word(self, eligible: List[Tuple[str, str]], next_q_num: int) -> VocabItem:
        # Among eligible debt words, pick the one that has been waiting longest
        eligible.sort(key=lambda k: self.next_due.get(k, 0))
        item = self._find_item_by_key(eligible[0])
        return self._return_item(item or self.session_words[self._new_index - 1])

    def _return_item(self, item: VocabItem) -> VocabItem:
        self.recent.append(item)
        return item

    def _find_item_by_key(self, key: Tuple[str, str]) -> Optional[VocabItem]:
        fi, en = key
        for it in self.session_words:
            if it.fi == fi and it.en == en:
                return it
        return None

    # ---------------------------
    # Question building
    # ---------------------------
    def _make_mc_question(
        self,
        qtype: str,
        item: VocabItem,
        prompt: str,
        correct_value: str,
        distractor_field: str,
    ) -> Question:
        distractors = self._distractors(correct_value, distractor_field, k=3)
        options = distractors + [correct_value]
        random.shuffle(options)
        correct_index = options.index(correct_value)
        q = Question(qtype=qtype, prompt=prompt, options=options, correct_index=correct_index)
        q.item = item
        return q

    def _distractors(self, correct_value: str, field: str, k: int) -> List[str]:
        candidates = list({
            getattr(it, field)
            for it in self.vocab
            if getattr(it, field) != correct_value
        })
        random.shuffle(candidates)
        return candidates[:k] if len(candidates) >= k else candidates

    # ---------------------------
    # Apply result + persistence
    # ---------------------------
    def _apply_result(self, item: VocabItem, is_correct: bool):
        self.total += 1
        key = (item.fi, item.en)
        next_q_num = self.total + 1

        if is_correct:
            self.correct += 1

            if self.repeats_left.get(key, 0) > 0:
                self.repeats_left[key] = max(0, self.repeats_left[key] - 1)

            item.error_count = self.repeats_left.get(key, 0)

            if self.repeats_left.get(key, 0) > 0:
                self.next_due[key] = next_q_num + self.spacing
            else:
                self.next_due.pop(key, None)

        else:
            wcount = self.session_wrong_count.get(key, 0) + 1
            self.session_wrong_count[key] = wcount

            # Debt added per wrong attempt (diminishing):
            #   wrong #1 → +3
            #   wrong #2 → +2
            #   wrong #3+ → +1
            if wcount == 1:
                add = 3
            elif wcount == 2:
                add = 2
            else:
                add = 1

            self.repeats_left[key] = self.repeats_left.get(key, 0) + add
            item.error_count = self.repeats_left[key]
            self.next_due[key] = next_q_num + self.spacing

        save_error_counts(self.vocab)

    # ---------------------------
    # Typing normalization
    # ---------------------------
    def _normalize(self, s: str) -> str:
        s = (s or "").strip()
        s = re.sub(r"\s+", " ", s)
        if self.ignore_case:
            s = s.lower()
        if self.ignore_punct:
            s = re.sub(r"[!\"#$%&'()*+,\-./:;<=>?@\[\]^_`{|}~]", "", s)
            s = re.sub(r"\s+", " ", s).strip()
        return s

    def _split_answers(self, fi: str) -> List[str]:
        parts = [p.strip() for p in (fi or "").split("|")]
        parts = [p for p in parts if p]
        return parts if parts else ([fi] if fi else [])

    def _require_current(self) -> Question:
        if not self.current:
            raise RuntimeError("No active question. Call next_question() first.")
        if not hasattr(self.current, "item"):
            raise RuntimeError("Internal error: question has no item attached.")
        return self.current