"""Center panel for sentence review and manual candidate entry."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.change_guard import analyze_candidate


class RewritePanel(QWidget):
    accept_requested = Signal(str)
    unchanged_requested = Signal()
    review_requested = Signal()
    reject_requested = Signal()
    previous_requested = Signal()
    next_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.original = QTextEdit(readOnly=True)
        self.current = QTextEdit(readOnly=True)
        self.candidates: dict[str, QTextEdit] = {}
        self.scores: dict[str, QSpinBox] = {}
        self.reasons: dict[str, QLineEdit] = {}

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Original sentence"))
        layout.addWidget(self.original)
        layout.addWidget(QLabel("Current working sentence"))
        layout.addWidget(self.current)

        for label in ["A", "B", "C"]:
            group = QGroupBox(f"Rewrite candidate {label}")
            form = QFormLayout(group)
            editor = QTextEdit()
            score = QSpinBox()
            score.setRange(0, 100)
            reason = QLineEdit()
            form.addRow("Text", editor)
            form.addRow("Score", score)
            form.addRow("Reason", reason)
            self.candidates[label] = editor
            self.scores[label] = score
            self.reasons[label] = reason
            layout.addWidget(group)

        button_grid = QGridLayout()
        for column, label in enumerate(["A", "B", "C"]):
            button = QPushButton(f"Accept {label}")
            button.clicked.connect(lambda _checked=False, choice=label: self.accept_requested.emit(choice))
            button_grid.addWidget(button, 0, column)
        self.unchanged_button = QPushButton("Leave unchanged")
        self.reject_button = QPushButton("Reject candidates")
        self.review_button = QPushButton("Needs David Review")
        self.scan_risks_button = QPushButton("Scan candidate risks")
        button_grid.addWidget(self.unchanged_button, 1, 0)
        button_grid.addWidget(self.reject_button, 1, 1)
        button_grid.addWidget(self.review_button, 1, 2)
        button_grid.addWidget(self.scan_risks_button, 2, 0, 1, 3)
        layout.addLayout(button_grid)

        self.risk_preview = QTextEdit(readOnly=True)
        self.risk_preview.setPlaceholderText("Candidate risk warnings will appear here.")
        layout.addWidget(QLabel("Candidate risk preview"))
        layout.addWidget(self.risk_preview)

        nav = QHBoxLayout()
        self.previous_button = QPushButton("Previous sentence")
        self.next_button = QPushButton("Next sentence")
        nav.addWidget(self.previous_button)
        nav.addWidget(self.next_button)
        layout.addLayout(nav)

        self.unchanged_button.clicked.connect(self.unchanged_requested.emit)
        self.reject_button.clicked.connect(self.reject_requested.emit)
        self.review_button.clicked.connect(self.review_requested.emit)
        self.scan_risks_button.clicked.connect(self.scan_candidate_risks)
        self.previous_button.clicked.connect(self.previous_requested.emit)
        self.next_button.clicked.connect(self.next_requested.emit)

    def set_sentence(self, original: str, current: str) -> None:
        self.original.setPlainText(original)
        self.current.setPlainText(current)
        for label in ["A", "B", "C"]:
            self.candidates[label].setPlainText(current)
            self.scores[label].setValue(0)
            self.reasons[label].clear()
        self.risk_preview.clear()

    def candidate_payloads(self) -> list[dict]:
        original = self.original.toPlainText().strip()
        return [
            self._candidate_payload(label, original)
            for label in ["A", "B", "C"]
        ]

    def _candidate_payload(self, label: str, original: str) -> dict:
        text = self.candidates[label].toPlainText().strip()
        report = analyze_candidate(original, text) if text else None
        return {
            "label": label,
            "text": text,
            "score": self.scores[label].value(),
            "reason": self.reasons[label].text().strip(),
            "risks": report.warnings if report else [],
        }

    def scan_candidate_risks(self) -> None:
        lines: list[str] = []
        for payload in self.candidate_payloads():
            warnings = payload["risks"]
            lines.append(f"Candidate {payload['label']}:")
            if warnings:
                lines.extend(f"- {warning}" for warning in warnings)
            else:
                lines.append("- No guard warnings.")
            lines.append("")
        self.risk_preview.setPlainText("\n".join(lines).strip())
