import random
from collections import deque
from typing import Deque, Dict, List, Set, Tuple

from .engine import QuizEngine, QType
from .models import Question, VocabItem
from .storage import save_error_counts


class HardcoreQuizEngine(QuizEngine):
    """
    Hardcore mode — stricter debt clearance:

    First pass (tasks queue):
      - Every session word gets exactly 2 tasks: 1 MC (random direction) + 1 Typing.
      - Tasks are shuffled. New tasks and debt reviews are interleaved
        probabilistically (same logic as normal engine: low early, rises later).
      - Spacing (next_due) is enforced so debt words don't reappear immediately.

    Debt clearance rule (hardcore-specific):
      - A correct answer only reduces debt by 1 when BOTH MC and Typing have
        been answered correctly at least once for that word.
      - Until both are done, correct answers update the flags but don't reduce debt.
      - This means a word with debt requires demonstrating mastery in both
        question types before it is cleared.

    After first pass:
      - Debt-only phase, same spacing/probabilistic logic as normal engine.
      - If only one debt word remains, repeat consecutively until cleared.
    """

    def reset_session(self):
        super().reset_session()  # sets up vocab, spacing, next_due, repeats_left, etc.

        # Task queue: each session word gets 1 MC + 1 Typing task
        tasks: List[Tuple[VocabItem, str]] = []
        for item in self.session_words:
            mc_type = random.choice([QType.MC_FI_TO_EN, QType.MC_EN_TO_FI])
            tasks.append((item, mc_type))
            tasks.append((item, QType.TYPE_EN_TO_FI))
        random.shuffle(tasks)
        self.tasks: Deque[Tuple[VocabItem, str]] = deque(tasks)

        # Words that have been fully cleared (debt == 0 after hardcore rule met).
        # UI uses this to decrement "Words left" display.
        self.fully_cleared: Set[Tuple[str, str]] = set()

        # Tracks whether MC and Typing have each been answered correctly
        # for a given word (required before debt can decrease).
        # Initialised for all session words; debt words added on demand.
        self.min_tests_done: Dict[Tuple[str, str], Dict[str, bool]] = {
            (item.fi, item.en): {"MC_done": False, "Typing_done": False}
            for item in self.session_words
        }

    # -------------------------
    # Stop condition
    # -------------------------
    def _is_session_done(self) -> bool:
        if self.tasks:
            return False
        return self._total_debt() == 0

    # -------------------------
    # Next question
    # -------------------------
    def next_question(self) -> Question:
        if self._is_session_done():
            raise StopIteration("Session finished.")

        item, qtype = self._choose_item_and_type_for_next()

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
        else:
            accepted = self._split_answers(item.fi)
            q = Question(qtype=qtype, prompt=item.en, accepted_answers=accepted)
            q.item = item

        self.current = q
        return q

    # -------------------------
    # Selection
    # -------------------------
    def _choose_item_and_type_for_next(self) -> Tuple[VocabItem, str]:
        """
        Mirrors the probabilistic interleave logic of the normal engine,
        adapted for the (item, qtype) task queue instead of a new-word index.

        Phase 1 — tasks remain:
          P(review debt) rises from ~15% early to ~50% near end of task queue,
          plus a small bonus per eligible debt word. Spacing is respected.

        Phase 2 — tasks exhausted:
          Debt-only with spacing. If one debt word left, repeat consecutively.
        """
        next_q_num = self.total + 1
        debt_keys = self._debt_keys()
        tasks_left = bool(self.tasks)

        # ── Phase 1: tasks remain ─────────────────────────────────────────────
        if tasks_left:
            eligible = [
                k for k in debt_keys
                if next_q_num >= self.next_due.get(k, 0)
            ]

            if eligible:
                total_tasks = len(self.session_words) * 2
                tasks_done = total_tasks - len(self.tasks)
                progress = tasks_done / total_tasks  # 0.0 → 1.0

                base = 0.15 + 0.35 * progress
                debt_bonus = min(0.15, len(eligible) * 0.04)
                p_review = min(base + debt_bonus, 0.65)

                if random.random() < p_review:
                    return self._pick_debt_item_and_type(eligible, next_q_num)

            # Default: next task from queue
            item, qtype = self.tasks.popleft()
            self.recent.append(item)
            return item, qtype

        # ── Phase 2: tasks exhausted → debt only ─────────────────────────────
        if not debt_keys:
            # Shouldn't happen if _is_session_done() is correct
            item = random.choice(self.session_words)
            return item, random.choice(self.enabled_types)

        if len(debt_keys) == 1:
            key = debt_keys[0]
            item = self._find_item_by_key(key) or random.choice(self.session_words)
            self.recent.append(item)
            return item, self._pick_qtype_for_debt(key)

        eligible = [k for k in debt_keys if next_q_num >= self.next_due.get(k, 0)]
        if eligible:
            return self._pick_debt_item_and_type(eligible, next_q_num)

        # None eligible yet → pick soonest due (soft spacing)
        debt_keys.sort(key=lambda k: self.next_due.get(k, 0))
        key = debt_keys[0]
        item = self._find_item_by_key(key) or random.choice(self.session_words)
        self.recent.append(item)
        return item, self._pick_qtype_for_debt(key)

    def _pick_debt_item_and_type(
        self, eligible: List[Tuple[str, str]], next_q_num: int
    ) -> Tuple[VocabItem, str]:
        eligible.sort(key=lambda k: self.next_due.get(k, 0))
        key = eligible[0]
        item = self._find_item_by_key(key) or random.choice(self.session_words)
        self.recent.append(item)
        return item, self._pick_qtype_for_debt(key)

    def _pick_qtype_for_debt(self, key: Tuple[str, str]) -> str:
        """
        For debt reviews, prefer the question type not yet done correctly,
        so the word moves toward fulfilling both MC_done and Typing_done.
        Falls back to a random enabled type if both are already done.
        """
        flags = self.min_tests_done.get(key, {"MC_done": True, "Typing_done": True})
        mc_types = [QType.MC_FI_TO_EN, QType.MC_EN_TO_FI]

        mc_enabled = any(t in self.enabled_types for t in mc_types)
        typing_enabled = QType.TYPE_EN_TO_FI in self.enabled_types

        if not flags["MC_done"] and mc_enabled:
            return random.choice([t for t in mc_types if t in self.enabled_types])
        if not flags["Typing_done"] and typing_enabled:
            return QType.TYPE_EN_TO_FI

        return random.choice(self.enabled_types)

    # -------------------------
    # Apply result (hardcore)
    # -------------------------
    def _apply_result(self, item: VocabItem, is_correct: bool):
        """
        Hardcore debt rule:
          Correct answer updates MC_done / Typing_done flags.
          Debt only decreases by 1 when BOTH flags are True.
          Wrong answer adds debt (same diminishing policy as normal engine)
          and resets both flags so mastery must be re-demonstrated.
        """
        self.total += 1
        key = (item.fi, item.en)
        next_q_num = self.total + 1
        qtype = self.current.qtype

        # Ensure key exists in min_tests_done (may be a debt word added mid-session)
        if key not in self.min_tests_done:
            self.min_tests_done[key] = {"MC_done": False, "Typing_done": False}

        if is_correct:
            self.correct += 1

            # Update mastery flags (used only for first-pass requirement)
            if qtype in (QType.MC_FI_TO_EN, QType.MC_EN_TO_FI):
                self.min_tests_done[key]["MC_done"] = True
            elif qtype == QType.TYPE_EN_TO_FI:
                self.min_tests_done[key]["Typing_done"] = True

            # Debt phase: reduce debt by 1 on any correct answer (same as normal)
            if self.repeats_left.get(key, 0) > 0:
                self.repeats_left[key] = max(0, self.repeats_left[key] - 1)

            # Mark fully cleared when:
            # (a) debt == 0 after paying off, OR
            # (b) passed first pass cleanly (both MC + Typing done, no debt)
            mc_done = self.min_tests_done[key]["MC_done"]
            typing_done = self.min_tests_done[key]["Typing_done"]
            if self.repeats_left.get(key, 0) == 0 and mc_done and typing_done:
                self.fully_cleared.add(key)

            item.error_count = self.repeats_left.get(key, 0)

            if self.repeats_left.get(key, 0) > 0:
                self.next_due[key] = next_q_num + self.spacing
            else:
                self.next_due.pop(key, None)

        else:
            wcount = self.session_wrong_count.get(key, 0) + 1
            self.session_wrong_count[key] = wcount

            # Diminishing debt penalty (same as normal engine)
            if wcount == 1:
                add = 3
            elif wcount == 2:
                add = 2
            else:
                add = 1

            self.repeats_left[key] = self.repeats_left.get(key, 0) + add
            item.error_count = self.repeats_left[key]
            self.next_due[key] = next_q_num + self.spacing

            # Reset mastery flags: wrong answer means must re-demonstrate both
            self.min_tests_done[key] = {"MC_done": False, "Typing_done": False}

        save_error_counts(self.vocab)