"""Export controls."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class ExportPanel(QWidget):
    export_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.export_button = QPushButton("Export ledger + draft")
        self.status_label = QLabel("Exports are written to outputs/ by default.")
        self.status_label.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self.export_button)
        layout.addWidget(self.status_label)
        self.export_button.clicked.connect(self.export_requested.emit)

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)
