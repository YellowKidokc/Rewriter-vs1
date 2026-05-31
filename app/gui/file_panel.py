"""Left-side file, section, and sentence navigation panel."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFileDialog, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget


class FilePanel(QWidget):
    open_requested = Signal(str)
    sentence_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.open_button = QPushButton("Open file")
        self.path_label = QLabel("No file loaded")
        self.path_label.setWordWrap(True)
        self.section_list = QListWidget()
        self.sentence_list = QListWidget()

        layout = QVBoxLayout(self)
        layout.addWidget(self.open_button)
        layout.addWidget(QLabel("Loaded file"))
        layout.addWidget(self.path_label)
        layout.addWidget(QLabel("Sections"))
        layout.addWidget(self.section_list)
        layout.addWidget(QLabel("Sentences"))
        layout.addWidget(self.sentence_list)

        self.open_button.clicked.connect(self._choose_file)
        self.sentence_list.currentItemChanged.connect(self._emit_sentence)

    def _choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open document",
            "",
            "Documents (*.md *.markdown *.txt *.html *.htm)",
        )
        if path:
            self.open_requested.emit(path)

    def set_document(self, path: str, sections) -> None:
        self.path_label.setText(path)
        self.section_list.clear()
        self.sentence_list.clear()
        for section in sections:
            self.section_list.addItem(section.title)
            for sentence in section.sentences:
                self.sentence_list.addItem(f"{sentence.id}: {sentence.text[:80]}")
                self.sentence_list.item(self.sentence_list.count() - 1).setData(256, sentence.id)
        if self.sentence_list.count():
            self.sentence_list.setCurrentRow(0)

    def select_sentence_id(self, sentence_id: str) -> None:
        for row in range(self.sentence_list.count()):
            if self.sentence_list.item(row).data(256) == sentence_id:
                self.sentence_list.setCurrentRow(row)
                break

    def _emit_sentence(self, current, _previous) -> None:
        if current:
            self.sentence_selected.emit(current.data(256))
