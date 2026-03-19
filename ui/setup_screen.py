from core.engine import QuizEngine, QType
from core.loader import load_vocab_files
from core.storage import load_error_counts
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QListWidget, QCheckBox,
    QSpinBox, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt


class SetupScreen(QWidget):

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.selected_files = []

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(80, 40, 80, 40)

        title = QLabel("Session Setup")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title)

        # Browse files
        self.browse_button = QPushButton("Browse Vocabulary Files")
        self.browse_button.clicked.connect(self.browse_files)
        layout.addWidget(self.browse_button)

        self.file_list = QListWidget()
        layout.addWidget(self.file_list)

        # Question types
        self.cb_fi_en = QCheckBox("Finnish → English (Multiple Choice)")
        self.cb_en_fi = QCheckBox("English → Finnish (Multiple Choice)")
        self.cb_typing = QCheckBox("English → Finnish (Typing)")

        self.cb_fi_en.setChecked(True)
        self.cb_en_fi.setChecked(True)
        self.cb_typing.setChecked(True)

        layout.addWidget(self.cb_fi_en)
        layout.addWidget(self.cb_en_fi)
        layout.addWidget(self.cb_typing)

        # HARDCORE MODE
        self.cb_hardcore = QCheckBox("Hardcore Mode (Each word must pass MC + Typing)")
        layout.addWidget(self.cb_hardcore)

        # Session length
        row = QHBoxLayout()
        label = QLabel("Number of questions:")
        self.question_count = QSpinBox()
        self.question_count.setRange(1, 999)
        self.question_count.setValue(30)

        row.addWidget(label)
        row.addWidget(self.question_count)
        layout.addLayout(row)

        # Start button
        self.start_button = QPushButton("Start Session")
        self.start_button.clicked.connect(self.start_session)
        layout.addWidget(self.start_button)

        layout.addStretch()

        self.setLayout(layout)

    def browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Vocabulary Files",
            "",
            "Text Files (*.txt)"
        )

        if files:
            self.selected_files = files
            self.file_list.clear()
            self.file_list.addItems(files)

    def start_session(self):

        if not self.selected_files:
            QMessageBox.warning(self, "No files selected", "Please select at least one vocabulary file.")
            return

        # Commit typed text if user is editing
        self.question_count.interpretText()
        question_total = self.question_count.value()

        # Validate 5..200
        if question_total < 5 or question_total > 200:
            QMessageBox.warning(
                self,
                "Invalid Number of Questions",
                "Number of questions must be between 5 and 200."
            )
            return

        enabled = []

        if self.cb_fi_en.isChecked():
            enabled.append(QType.MC_FI_TO_EN)

        if self.cb_en_fi.isChecked():
            enabled.append(QType.MC_EN_TO_FI)

        if self.cb_typing.isChecked():
            enabled.append(QType.TYPE_EN_TO_FI)

        if not enabled:
            QMessageBox.warning(self, "No question type selected", "Please enable at least one question type.")
            return

        # Hardcore validation
        hardcore = self.cb_hardcore.isChecked()

        if hardcore:
            if QType.TYPE_EN_TO_FI not in enabled:
                QMessageBox.warning(
                    self,
                    "Hardcore Mode Requirement",
                    "Hardcore mode requires Typing to be enabled."
                )
                return

            if not (QType.MC_FI_TO_EN in enabled or QType.MC_EN_TO_FI in enabled):
                QMessageBox.warning(
                    self,
                    "Hardcore Mode Requirement",
                    "Hardcore mode requires at least one Multiple Choice type."
                )
                return

        # Delegate session creation to MainWindow
        self.main_window.start_session(
            file_paths=self.selected_files,
            enabled_types=enabled,
            session_total=question_total,
            hardcore=hardcore
        )