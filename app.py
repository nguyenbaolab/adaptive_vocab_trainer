import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox

from ui.setup_screen import SetupScreen
from ui.quiz_screen import QuizScreen
from ui.summary_screen import SummaryScreen

from core.loader import load_vocab_files
from core.engine import QuizEngine
from core.hardcore_engine import HardcoreQuizEngine
from core.session_stats import SessionStats


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Adaptive Vocabulary Trainer")
        self.setMinimumSize(900, 600)

        self.engine = None
        self.stats = SessionStats()
        self.last_settings = None  # for restart

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.setup_screen = SetupScreen(self)
        self.quiz_screen = QuizScreen(self)
        self.summary_screen = SummaryScreen(self)

        self.stack.addWidget(self.setup_screen)
        self.stack.addWidget(self.quiz_screen)
        self.stack.addWidget(self.summary_screen)

        self.stack.setCurrentWidget(self.setup_screen)

    def go_to_setup(self):
        self.stack.setCurrentWidget(self.setup_screen)

    def go_to_quiz(self):
        self.stack.setCurrentWidget(self.quiz_screen)

    def go_to_summary(self):
        self.stack.setCurrentWidget(self.summary_screen)

    def start_session(self, file_paths, enabled_types, session_total: int, hardcore: bool = False):
        vocab = load_vocab_files(file_paths)
        if len(vocab) < 4:
            QMessageBox.warning(
                self,
                "Not enough data",
                "You need at least 4 vocabulary items for multiple-choice questions."
            )
            return

        # ❌ REMOVE: session-only => don't load previous wrong.txt
        # error_map = load_error_counts()
        # for v in vocab:
        #     v.error_count = error_map.get((v.fi, v.en), 0)

        if hardcore:
            self.engine = HardcoreQuizEngine(
                vocab,
                enabled_types=enabled_types,
                session_total=session_total
            )
        else:
            self.engine = QuizEngine(
                vocab,
                enabled_types=enabled_types,
                session_total=session_total
            )

        # ✅ New stats: no fixed max total, just track answered/correct/wrong/time
        self.stats.start()

        self.last_settings = {
            "file_paths": list(file_paths),
            "enabled_types": list(enabled_types),
            "session_total": int(session_total),
            "hardcore": hardcore
        }

        self.quiz_screen.start_quiz()
        self.go_to_quiz()

    def restart_last_session(self):
        if not self.last_settings:
            self.go_to_setup()
            return
        s = self.last_settings
        self.start_session(
            s["file_paths"],
            s["enabled_types"],
            s["session_total"],
            s.get("hardcore", False)
        )

    def finish_session(self):
        # Stop timer and refresh summary UI
        self.stats.stop()
        self.summary_screen.refresh()
        self.go_to_summary()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())