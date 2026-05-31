"""Right-side reconstructed draft preview."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


class PreviewPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.preview = QTextEdit(readOnly=True)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Live reconstructed draft preview"))
        layout.addWidget(self.preview)

    def set_text(self, text: str) -> None:
        self.preview.setPlainText(text)
