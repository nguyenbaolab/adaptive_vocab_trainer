# ui/summary_screen.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt

from core.engine import QType


class SummaryScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        root = QVBoxLayout()
        root.setSpacing(18)
        root.setContentsMargins(80, 40, 80, 40)

        # --- KPI Header (big) ---
        self.kpi_title = QLabel("Session Summary")
        self.kpi_title.setAlignment(Qt.AlignCenter)
        self.kpi_title.setStyleSheet("font-size: 26px; font-weight: 800;")
        root.addWidget(self.kpi_title)

        self.kpi_main = QLabel("0 / 0 Correct")
        self.kpi_main.setAlignment(Qt.AlignCenter)
        self.kpi_main.setStyleSheet("font-size: 40px; font-weight: 900;")
        root.addWidget(self.kpi_main)

        self.kpi_sub = QLabel("Accuracy: 0%   •   Time spent: 00:00")
        self.kpi_sub.setAlignment(Qt.AlignCenter)
        self.kpi_sub.setStyleSheet("font-size: 14px; color: #bdbdbd;")
        root.addWidget(self.kpi_sub)

        # --- Breakdown table (small) ---
        self.breakdown_title = QLabel("Performance by Question Type")
        self.breakdown_title.setStyleSheet("font-size: 14px; font-weight: 700;")
        root.addWidget(self.breakdown_title)

        self.breakdown = QTableWidget(0, 4)
        self.breakdown.setHorizontalHeaderLabels(["Question Type", "Correct", "Total", "Accuracy"])
        self.breakdown.verticalHeader().setVisible(False)
        self.breakdown.setEditTriggers(QTableWidget.NoEditTriggers)
        self.breakdown.setSelectionMode(QTableWidget.NoSelection)
        self.breakdown.setFocusPolicy(Qt.NoFocus)
        self.breakdown.setMinimumHeight(140)

        header = self.breakdown.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        root.addWidget(self.breakdown)

        # --- Weak words list (scrollable) ---
        self.weak_title = QLabel("Mistakes in This Session")
        self.weak_title.setStyleSheet("font-size: 14px; font-weight: 700;")
        root.addWidget(self.weak_title)

        self.no_mistakes_label = QLabel("No mistakes this session 🎉")
        self.no_mistakes_label.setAlignment(Qt.AlignCenter)
        self.no_mistakes_label.setStyleSheet("font-size: 14px; color: #bdbdbd;")
        root.addWidget(self.no_mistakes_label)

        self.weak_table = QTableWidget(0, 3)
        self.weak_table.setHorizontalHeaderLabels(["Finnish", "English", "Mistakes"])
        self.weak_table.verticalHeader().setVisible(False)
        self.weak_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.weak_table.setSelectionMode(QTableWidget.NoSelection)
        self.weak_table.setFocusPolicy(Qt.NoFocus)

        header2 = self.weak_table.horizontalHeader()
        header2.setSectionResizeMode(0, QHeaderView.Stretch)
        header2.setSectionResizeMode(1, QHeaderView.Stretch)
        header2.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        root.addWidget(self.weak_table)

        # --- Buttons ---
        btn_row = QHBoxLayout()
        self.back_btn = QPushButton("Back to Setup")
        self.back_btn.clicked.connect(self.main_window.go_to_setup)

        self.restart_btn = QPushButton("Restart (same settings)")
        self.restart_btn.clicked.connect(self.main_window.restart_last_session)

        btn_row.addWidget(self.back_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.restart_btn)
        root.addLayout(btn_row)

        self.setLayout(root)

        # Start with tables hidden appropriately
        self.no_mistakes_label.hide()

    def refresh(self):
        stats = self.main_window.stats

        # KPI
        self.kpi_main.setText(f"{stats.correct_total} / {stats.answered_total} Correct")
        self.kpi_sub.setText(f"Accuracy: {stats.accuracy_pct():.0f}%   •   Time spent: {stats.elapsed_mmss()}")

        # Breakdown
        self._render_breakdown()

        # Weak words list
        self._render_weak_words()

    def _render_breakdown(self):
        stats = self.main_window.stats

        def label_for(qtype: str) -> str:
            return {
                QType.MC_FI_TO_EN: "Finnish → English (MC)",
                QType.MC_EN_TO_FI: "English → Finnish (MC)",
                QType.TYPE_EN_TO_FI: "English → Finnish (Typing)",
            }.get(qtype, qtype)

        rows = []
        for qtype, asked in stats.asked_by_type.items():
            if asked <= 0:
                continue
            correct = stats.correct_by_type.get(qtype, 0)
            acc = (correct / asked * 100.0) if asked else 0.0
            rows.append((label_for(qtype), correct, asked, f"{acc:.0f}%"))

        # Keep stable order (nice UX)
        order = [QType.MC_FI_TO_EN, QType.MC_EN_TO_FI, QType.TYPE_EN_TO_FI]
        rows_sorted = []
        for qt in order:
            for r in rows:
                if r[0] == label_for(qt):
                    rows_sorted.append(r)
        # add any unknown types at end
        for r in rows:
            if r not in rows_sorted:
                rows_sorted.append(r)

        self.breakdown.setRowCount(len(rows_sorted))
        for i, (qt_label, correct, asked, acc_str) in enumerate(rows_sorted):
            self.breakdown.setItem(i, 0, QTableWidgetItem(qt_label))

            item_c = QTableWidgetItem(str(correct))
            item_c.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.breakdown.setItem(i, 1, item_c)

            item_a = QTableWidgetItem(str(asked))
            item_a.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.breakdown.setItem(i, 2, item_a)

            item_acc = QTableWidgetItem(acc_str)
            item_acc.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.breakdown.setItem(i, 3, item_acc)

    def _render_weak_words(self):
        stats = self.main_window.stats
        mistakes = stats.mistakes_map  # (fi,en)->count

        if not mistakes:
            self.weak_table.hide()
            self.no_mistakes_label.show()
            return

        self.no_mistakes_label.hide()
        self.weak_table.show()

        # Sort by mistakes desc, then fi asc
        rows = sorted(
            [(fi, en, cnt) for (fi, en), cnt in mistakes.items()],
            key=lambda x: (-x[2], x[0].lower())
        )

        self.weak_table.setRowCount(len(rows))
        for i, (fi, en, cnt) in enumerate(rows):
            self.weak_table.setItem(i, 0, QTableWidgetItem(fi))
            self.weak_table.setItem(i, 1, QTableWidgetItem(en))

            item_m = QTableWidgetItem(str(cnt))
            item_m.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.weak_table.setItem(i, 2, item_m)