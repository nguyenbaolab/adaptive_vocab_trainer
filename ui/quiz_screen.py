# ui/quiz_screen.py
from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSizePolicy, QMessageBox
)
from core.engine import QType


class QuizScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.current_q = None
        self.answered = False

        # ---------------------------
        # Words left tracking
        # ---------------------------
        self.words_left = 0
        self.words_left_seen = set()  # lưu key của từ đã cleared để giảm chỉ 1 lần

        # ---------------------------
        # Questions progress tracking
        # answered / total_expected
        # total_expected tăng mỗi khi có câu sai (debt thêm vào)
        # ---------------------------
        self.q_answered = 0
        self.q_total = 0

        # ---------------------------
        # Layout root
        # ---------------------------
        root = QVBoxLayout()
        root.setSpacing(18)
        root.setContentsMargins(80, 40, 80, 40)

        # ---------------------------
        # Row 1: Answered / Correct / Wrong / Time  +  Mode (right)
        # ---------------------------
        row1 = QHBoxLayout()

        self.progress_label = QLabel("Answered: 0")
        self.progress_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        self.score_label = QLabel("Correct: 0")
        self.score_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        self.wrong_label = QLabel("Wrong: 0")
        self.wrong_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        self.time_label = QLabel("Time: 00:00")
        self.time_label.setStyleSheet("font-size: 14px; font-weight: 600;")

        row1.addWidget(self.progress_label)
        row1.addSpacing(16)
        row1.addWidget(self.score_label)
        row1.addSpacing(16)
        row1.addWidget(self.wrong_label)
        row1.addSpacing(16)
        row1.addWidget(self.time_label)
        row1.addStretch()

        self.mode_label = QLabel("Mode")
        self.mode_label.setAlignment(Qt.AlignRight)
        self.mode_label.setStyleSheet("font-size: 13px; color: #bdbdbd;")
        row1.addWidget(self.mode_label)

        root.addLayout(row1)

        # ---------------------------
        # Row 2: Words left  +  Questions progress
        # ---------------------------
        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)

        self.words_left_label = QLabel("Words left: 0")
        self.words_left_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #bdbdbd;")
        self.questions_label = QLabel("Questions: 0/0")
        self.questions_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #bdbdbd;")

        row2.addWidget(self.words_left_label)
        row2.addSpacing(16)
        row2.addWidget(self.questions_label)
        row2.addStretch()

        root.addLayout(row2)

        # ---------------------------
        # Prompt
        # ---------------------------
        self.prompt = QLabel("—")
        self.prompt.setAlignment(Qt.AlignCenter)
        self.prompt.setWordWrap(True)
        self.prompt.setStyleSheet("font-size: 44px; font-weight: 800;")
        root.addWidget(self.prompt)

        # ---------------------------
        # Answer area
        # ---------------------------
        self.answer_area = QVBoxLayout()
        self.answer_area.setSpacing(10)
        root.addLayout(self.answer_area)

        # Typing widgets
        self.typing_input = QLineEdit()
        self.typing_input.setPlaceholderText("Type the Finnish word…")
        self.typing_input.setMinimumHeight(42)
        self.typing_input.installEventFilter(self)

        self.submit_typing_btn = QPushButton("Submit")
        self.submit_typing_btn.setMinimumHeight(42)
        self.submit_typing_btn.clicked.connect(self.on_submit_typing)

        # MC buttons
        self.mc_buttons = []
        for i in range(4):
            btn = QPushButton(f"{chr(65+i)}.")
            btn.setMinimumHeight(46)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(lambda _, idx=i: self.on_choose_mc(idx))
            self.mc_buttons.append(btn)

        # Feedback
        self.feedback = QLabel("")
        self.feedback.setAlignment(Qt.AlignCenter)
        self.feedback.setWordWrap(True)
        self.feedback.setStyleSheet("font-size: 14px;")
        root.addWidget(self.feedback)

        # Bottom controls
        bottom = QHBoxLayout()
        self.end_btn = QPushButton("End Session")
        self.end_btn.clicked.connect(self.end_session)

        self.next_btn = QPushButton("Next")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.load_question)

        bottom.addWidget(self.end_btn)
        bottom.addStretch()
        bottom.addWidget(self.next_btn)
        root.addLayout(bottom)

        self.setLayout(root)

        # ---------------------------
        # Timer
        # ---------------------------
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self.update_header)

    # ---------------------------
    # Event handling
    # ---------------------------
    def lock_inputs(self):
        for b in self.mc_buttons:
            b.setEnabled(False)
        self.typing_input.setEnabled(False)
        self.submit_typing_btn.setEnabled(False)

    def clear_answer_area(self):
        while self.answer_area.count():
            item = self.answer_area.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

    def eventFilter(self, obj, event):
        if obj is self.typing_input and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if self.current_q and self.current_q.qtype == QType.TYPE_EN_TO_FI:
                    if not self.answered:
                        self.on_submit_typing()
                        event.accept()
                        return True
                    if self.next_btn.isEnabled():
                        self.load_question()
                        event.accept()
                        return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.current_q and self.current_q.qtype == QType.TYPE_EN_TO_FI:
                if self.focusWidget() is self.typing_input:
                    event.accept()
                    return
            if self.answered and self.next_btn.isEnabled():
                self.load_question()
                event.accept()
                return
            event.accept()
            return
        super().keyPressEvent(event)

    # ---------------------------
    # Quiz flow
    # ---------------------------
    def start_quiz(self):
        engine = getattr(self.main_window, "engine", None)
        if not engine:
            QMessageBox.warning(self, "Missing Engine", "Engine not initialized. Go back and start again.")
            self.main_window.go_to_setup()
            return

        engine.reset_session()

        # Words left: tổng số từ thực tế trong session
        self.words_left = len(engine.session_words)
        self.words_left_seen.clear()
        self.words_left_label.setText(f"Words left: {self.words_left}")

        # Questions progress
        self.q_answered = 0
        self._recompute_questions_total()

        if not self._timer.isActive():
            self._timer.start()
        self.update_header()
        self.load_question()

    def load_question(self):
        engine = self.main_window.engine
        try:
            q = engine.next_question()
        except StopIteration:
            self.end_session()
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.main_window.go_to_setup()
            return

        self.current_q = q
        self.answered = False
        self.feedback.setText("")
        self.next_btn.setEnabled(False)
        self.update_header()

        # Mode label
        mode_map = {
            QType.MC_FI_TO_EN: "Finnish → English (Multiple Choice)",
            QType.MC_EN_TO_FI: "English → Finnish (Multiple Choice)",
            QType.TYPE_EN_TO_FI: "English → Finnish (Typing)",
        }
        self.mode_label.setText(mode_map.get(q.qtype, "Mode"))
        self.prompt.setText(q.prompt)
        self.clear_answer_area()

        if q.qtype in (QType.MC_FI_TO_EN, QType.MC_EN_TO_FI):
            # Safety: only show as many buttons as there are options
            num_options = len(q.options)
            for i, btn in enumerate(self.mc_buttons):
                if i < num_options:
                    btn.setEnabled(True)
                    btn.setText(f"{chr(65+i)}. {q.options[i]}")
                    btn.setVisible(True)
                    self.answer_area.addWidget(btn)
                else:
                    btn.setVisible(False)
        else:
            self.typing_input.setEnabled(True)
            self.submit_typing_btn.setEnabled(True)
            self.typing_input.clear()
            self.answer_area.addWidget(self.typing_input)
            self.answer_area.addWidget(self.submit_typing_btn)
            self.typing_input.setFocus()

    def end_session(self):
        if hasattr(self, "_timer") and self._timer.isActive():
            self._timer.stop()
        self.main_window.finish_session()

    # ---------------------------
    # Helper: cập nhật words left
    # ---------------------------
    def _update_words_left(self, key):
        engine = self.main_window.engine
        if key in self.words_left_seen:
            return

        if getattr(engine, "fully_cleared", None) is not None:
            # Hardcore mode: chỉ pass khi engine đã xác nhận fully cleared
            cleared = key in engine.fully_cleared
        else:
            # Normal mode: hết debt là pass
            cleared = engine.repeats_left.get(key, 0) == 0

        if cleared:
            self.words_left -= 1
            self.words_left_seen.add(key)
            self.words_left = max(0, self.words_left)
            self.words_left_label.setText(f"Words left: {self.words_left}")

    # ---------------------------
    # Helper: cập nhật questions progress
    # ---------------------------
    def _remaining_questions_from_engine(self) -> int:
        """
        Remaining question workload based on engine state.
        This avoids hard-coded debt math and stays correct for both modes.
        """
        engine = self.main_window.engine

        # Remaining debt questions (shared by normal + hardcore)
        remaining_debt = sum(v for v in engine.repeats_left.values() if v > 0)

        if hasattr(engine, "tasks"):
            # Hardcore: tasks queue + debt
            remaining_tasks = len(engine.tasks)
            return max(0, remaining_tasks + remaining_debt)

        # Normal: unseen new words + debt
        remaining_new = len(engine.session_words) - engine._new_index
        return max(0, remaining_new + remaining_debt)

    def _recompute_questions_total(self):
        # q_total is the current expected final answered count.
        self.q_total = self.q_answered + self._remaining_questions_from_engine()
        self._update_questions_label()

    def _update_questions_progress(self):
        """
        q_answered tăng 1 mỗi khi trả lời (bất kể đúng sai),
        sau đó q_total được recompute trực tiếp từ state engine.
        """
        self.q_answered += 1
        self._recompute_questions_total()

    def _update_questions_label(self):
        self.questions_label.setText(f"Questions: {self.q_answered}/{self.q_total}")

    # ---------------------------
    # Submit answers
    # ---------------------------
    def on_choose_mc(self, idx: int):
        if self.answered or not self.current_q:
            return

        engine = self.main_window.engine
        ok, msg, _ = engine.submit_mc(idx)
        item = self.current_q.item
        key = (item.fi, item.en)

        self.main_window.stats.record_answer(self.current_q.qtype, item.fi, item.en, ok)

        self.answered = True
        self.lock_inputs()
        self.feedback.setText(msg)
        self.update_header()

        self._update_words_left(key)
        self._update_questions_progress()
        self.next_btn.setEnabled(True)

    def on_submit_typing(self):
        if self.answered or not self.current_q:
            return

        engine = self.main_window.engine
        text = self.typing_input.text()
        ok, msg, _ = engine.submit_typing(text)
        item = self.current_q.item
        key = (item.fi, item.en)

        self.main_window.stats.record_answer(self.current_q.qtype, item.fi, item.en, ok)

        self.answered = True
        self.lock_inputs()
        self.feedback.setText(msg)
        self.update_header()

        self._update_words_left(key)
        self._update_questions_progress()

        self.next_btn.setEnabled(True)
        self.typing_input.clearFocus()
        self.next_btn.setFocus()

    # ---------------------------
    # Header
    # ---------------------------
    def update_header(self):
        s = self.main_window.stats
        self.progress_label.setText(f"Answered: {s.answered_total}")
        self.score_label.setText(f"Correct: {s.correct_total}")
        self.wrong_label.setText(f"Wrong: {s.wrong_total}")
        self.time_label.setText(f"Time: {s.elapsed_mmss()}")

    def update_words_left(self):
        engine = getattr(self.main_window, "engine", None)
        if not engine:
            self.words_left_label.setText("Words left: 0")
            return

        for item in engine.session_words:
            key = (item.fi, item.en)
            self._update_words_left(key)