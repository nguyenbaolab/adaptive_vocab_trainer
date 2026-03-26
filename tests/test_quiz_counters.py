import os
import random
import tempfile
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from core.engine import QType, QuizEngine
from core.hardcore_engine import HardcoreQuizEngine
from core.models import VocabItem
from core.session_stats import SessionStats
from ui.quiz_screen import QuizScreen


@contextmanager
def temporary_cwd(path: str):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


class DummyMainWindow:
    def __init__(self, engine):
        self.engine = engine
        self.stats = SessionStats()
        self.stats.start()
        self.finished = False

    def finish_session(self):
        self.stats.stop()
        self.finished = True

    def go_to_setup(self):
        self.finished = True


class QuizCounterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_vocab(self, n_words: int):
        return [VocabItem(fi=f"fi_{i}", en=f"en_{i}") for i in range(n_words)]

    def _expected_total_from_engine_and_ui(self, engine, screen):
        remaining_debt = sum(v for v in engine.repeats_left.values() if v > 0)
        if hasattr(engine, "tasks"):
            remaining_work = len(engine.tasks) + remaining_debt
        else:
            remaining_work = (len(engine.session_words) - engine._new_index) + remaining_debt
        return screen.q_answered + max(0, remaining_work)

    def _simulate_one_session(self, n_words: int, seed: int, hardcore: bool):
        random.seed(seed)
        vocab = self._make_vocab(n_words)
        enabled = [QType.MC_FI_TO_EN, QType.MC_EN_TO_FI, QType.TYPE_EN_TO_FI]

        engine_cls = HardcoreQuizEngine if hardcore else QuizEngine

        with patch("core.engine.save_error_counts", return_value=None), patch(
            "core.hardcore_engine.save_error_counts", return_value=None
        ):
            engine = engine_cls(vocab, enabled_types=enabled, session_total=n_words)

            main = DummyMainWindow(engine)
            screen = QuizScreen(main)
            screen.start_quiz()

            session_keys = {(it.fi, it.en) for it in engine.session_words}

            steps = 0
            max_steps = 700
            while not main.finished:
                steps += 1
                if steps > max_steps:
                    break

                q = screen.current_q
                self.assertIsNotNone(q, "Current question should be available during session.")

                key = (q.item.fi, q.item.en)

            # Heavy random mistakes to stress counters (~45% wrong)
                force_correct = random.random() < 0.55

                if q.qtype in (QType.MC_FI_TO_EN, QType.MC_EN_TO_FI):
                    if force_correct:
                        chosen = q.correct_index
                    else:
                        wrong_options = [i for i in range(len(q.options)) if i != q.correct_index]
                        chosen = random.choice(wrong_options) if wrong_options else q.correct_index
                    screen.on_choose_mc(chosen)
                else:
                    if force_correct:
                        user_text = q.accepted_answers[0]
                    else:
                        user_text = "__definitely_wrong__"
                    screen.typing_input.setText(user_text)
                    screen.on_submit_typing()

            # Core counter invariants
                self.assertEqual(screen.q_answered, engine.total)
                self.assertEqual(screen.q_answered, main.stats.answered_total)
                self.assertEqual(
                    screen.q_total,
                    self._expected_total_from_engine_and_ui(engine, screen),
                    f"q_total drift vs engine state (words={n_words}, seed={seed}, hardcore={hardcore})",
                )
                self.assertGreaterEqual(screen.q_total, screen.q_answered)

            # words_left invariants
                self.assertEqual(screen.words_left, len(engine.session_words) - len(screen.words_left_seen))
                self.assertGreaterEqual(screen.words_left, 0)
                self.assertTrue(screen.words_left_seen.issubset(session_keys))

                if main.finished:
                    break
                screen.load_question()

            # If session ended within stress window, final counters must reconcile
            if main.finished:
                self.assertEqual(
                    screen.q_answered,
                    screen.q_total,
                    f"answered/total mismatch at end (words={n_words}, seed={seed}, hardcore={hardcore})",
                )
                self.assertEqual(main.stats.answered_total, engine.total)
                self.assertEqual(screen.words_left, 0)

    def test_large_random_sessions_normal_mode(self):
        with tempfile.TemporaryDirectory() as tmp, temporary_cwd(tmp):
            for n_words, seed in ((40, 11),):
                with self.subTest(mode="normal", words=n_words, seed=seed):
                    self._simulate_one_session(n_words=n_words, seed=seed, hardcore=False)

    def test_large_random_sessions_hardcore_mode(self):
        with tempfile.TemporaryDirectory() as tmp, temporary_cwd(tmp):
            for n_words, seed in ((40, 44),):
                with self.subTest(mode="hardcore", words=n_words, seed=seed):
                    self._simulate_one_session(n_words=n_words, seed=seed, hardcore=True)


if __name__ == "__main__":
    unittest.main()
