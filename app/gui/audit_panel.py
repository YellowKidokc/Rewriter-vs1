"""Audit controls and warning display."""

from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from app.audits import gpt_adversarial_writing_audit, kimi_style_measure_first


class AuditPanel(QWidget):
    audit_updated = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.measure_button = QPushButton("Run measurement audit")
        self.claim_button = QPushButton("Run adversarial claim audit")
        self.audit_warnings = QTextEdit(readOnly=True)
        self.claim_notes = QTextEdit(readOnly=True)
        self._current_text = ""
        self._report = ""

        layout = QVBoxLayout(self)
        layout.addWidget(self.measure_button)
        layout.addWidget(self.claim_button)
        layout.addWidget(QLabel("Audit warnings"))
        layout.addWidget(self.audit_warnings)
        layout.addWidget(QLabel("Claim-risk notes"))
        layout.addWidget(self.claim_notes)

        self.measure_button.clicked.connect(self.run_measurement_audit)
        self.claim_button.clicked.connect(self.run_claim_audit)

    def set_text(self, text: str) -> None:
        self._current_text = text

    def report(self) -> str:
        return self._report

    def _temp_doc(self) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        with handle:
            handle.write(self._current_text)
        return Path(handle.name)

    def run_measurement_audit(self) -> None:
        if not self._current_text.strip():
            self.audit_warnings.setPlainText("Load a document before running audits.")
            return
        path = self._temp_doc()
        try:
            result = kimi_style_measure_first.audit(path, kimi_style_measure_first.DEFAULT_MOTIFS)
            summary = ["# Measurement Audit", "", f"Sentences: {result['lexical_stats']['sentence_count']}", f"Words: {result['lexical_stats']['word_count']}", "", "## Section Weights"]
            summary.extend(f"- {row['section']}: {row['words']} words ({row['percent']}%)" for row in result["section_weights"])
            self._report = "\n".join(summary)
            self.audit_warnings.setPlainText(self._report)
            self.audit_updated.emit(self._report)
        finally:
            path.unlink(missing_ok=True)

    def run_claim_audit(self) -> None:
        if not self._current_text.strip():
            self.claim_notes.setPlainText("Load a document before running audits.")
            return
        path = self._temp_doc()
        try:
            self._report = gpt_adversarial_writing_audit.audit(path)
            self.claim_notes.setPlainText(self._report)
            self.audit_updated.emit(self._report)
        finally:
            path.unlink(missing_ok=True)
