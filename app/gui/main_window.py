"""Main PySide6 window for the rewrite ledger workbench."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QMessageBox, QSplitter, QVBoxLayout, QWidget

from app.core.document_loader import load_document
from app.core.draft_state import DraftState
from app.core.export_manager import ExportManager
from app.core.rewrite_ledger import RewriteCandidate, RewriteLedger, RewriteLedgerEntry
from app.core.sentence_splitter import flatten_sentences, split_document
from app.gui.audit_panel import AuditPanel
from app.gui.export_panel import ExportPanel
from app.gui.file_panel import FilePanel
from app.gui.preview_panel import PreviewPanel
from app.gui.rewrite_panel import RewritePanel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Rewrite Ledger Workbench")
        self.resize(1400, 850)

        self.file_panel = FilePanel()
        self.rewrite_panel = RewritePanel()
        self.preview_panel = PreviewPanel()
        self.audit_panel = AuditPanel()
        self.export_panel = ExportPanel()

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(self.preview_panel, 3)
        right_layout.addWidget(self.audit_panel, 2)
        right_layout.addWidget(self.export_panel, 1)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.file_panel)
        splitter.addWidget(self.rewrite_panel)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 2)
        self.setCentralWidget(splitter)

        self.sections = []
        self.draft_state: DraftState | None = None
        self.ledger = RewriteLedger()
        self.current_sentence_id: str | None = None
        self.audit_report = ""

        self.file_panel.open_requested.connect(self.open_file)
        self.file_panel.sentence_selected.connect(self.show_sentence)
        self.rewrite_panel.accept_requested.connect(self.accept_candidate)
        self.rewrite_panel.unchanged_requested.connect(self.leave_unchanged)
        self.rewrite_panel.review_requested.connect(self.needs_review)
        self.rewrite_panel.reject_requested.connect(self.reject_candidates)
        self.rewrite_panel.previous_requested.connect(self.previous_sentence)
        self.rewrite_panel.next_requested.connect(self.next_sentence)
        self.audit_panel.audit_updated.connect(self._set_audit_report)
        self.export_panel.export_requested.connect(self.export_outputs)

    def open_file(self, path: str) -> None:
        try:
            document = load_document(path)
            self.sections = split_document(document.working_text)
            self.draft_state = DraftState.from_sections(self.sections)
            self.ledger = RewriteLedger()
            self.file_panel.set_document(str(document.path), self.sections)
            self._refresh_preview()
        except Exception as exc:  # GUI boundary: show user-visible load errors.
            QMessageBox.critical(self, "Could not open document", str(exc))

    def show_sentence(self, sentence_id: str) -> None:
        if not self.draft_state:
            return
        sentence = self.draft_state.sentence_by_id(sentence_id)
        self.current_sentence_id = sentence_id
        self.rewrite_panel.set_sentence(sentence.text, self.draft_state.current_text_for(sentence_id))

    def accept_candidate(self, label: str) -> None:
        if not self._ready_for_decision():
            return
        payloads = self.rewrite_panel.candidate_payloads()
        selected = next(candidate for candidate in payloads if candidate["label"] == label)
        assert self.draft_state and self.current_sentence_id
        if not selected["text"]:
            QMessageBox.warning(self, "Blank candidate", f"Candidate {label} is blank.")
            return
        sentence = self.draft_state.sentence_by_id(self.current_sentence_id)
        current_before = self.draft_state.current_text_for(self.current_sentence_id)
        candidates = [RewriteCandidate(**payload) for payload in payloads]
        entry = RewriteLedgerEntry(
            sentence_id=sentence.id,
            section=sentence.section,
            original=sentence.text,
            current_before_decision=current_before,
            candidates=candidates,
            selected=label,
            status="accepted",
            reason=selected["reason"] or f"Accepted candidate {label} manually.",
            meaning_drift_risk="low",
            claim_strength_risk="low",
        )
        self.ledger.record(entry)
        self.draft_state.apply_rewrite(sentence.id, selected["text"])
        self._refresh_preview()
        self.next_sentence()

    def leave_unchanged(self) -> None:
        self._record_non_acceptance("unchanged", "Sentence left unchanged.")
        if self.draft_state and self.current_sentence_id:
            self.draft_state.leave_unchanged(self.current_sentence_id)
        self._refresh_preview()
        self.next_sentence()

    def reject_candidates(self) -> None:
        self._record_non_acceptance("rejected", "Manual candidates rejected.")
        self._refresh_preview()
        self.next_sentence()

    def needs_review(self) -> None:
        self._record_non_acceptance("needs_review", "Marked for David review.")
        self._refresh_preview()
        self.next_sentence()

    def _record_non_acceptance(self, status: str, reason: str) -> None:
        if not self._ready_for_decision():
            return
        assert self.draft_state and self.current_sentence_id
        sentence = self.draft_state.sentence_by_id(self.current_sentence_id)
        entry = RewriteLedgerEntry(
            sentence_id=sentence.id,
            section=sentence.section,
            original=sentence.text,
            current_before_decision=self.draft_state.current_text_for(sentence.id),
            candidates=[RewriteCandidate(**payload) for payload in self.rewrite_panel.candidate_payloads()],
            selected="",
            status=status,  # type: ignore[arg-type]
            reason=reason,
            meaning_drift_risk="low" if status == "unchanged" else "medium",
            claim_strength_risk="low" if status == "unchanged" else "medium",
        )
        self.ledger.record(entry)

    def previous_sentence(self) -> None:
        self._move_sentence(-1)

    def next_sentence(self) -> None:
        self._move_sentence(1)

    def _move_sentence(self, offset: int) -> None:
        if not self.draft_state or not self.current_sentence_id:
            return
        sentences = flatten_sentences(self.sections)
        ids = [sentence.id for sentence in sentences]
        index = ids.index(self.current_sentence_id)
        next_index = max(0, min(len(ids) - 1, index + offset))
        self.file_panel.select_sentence_id(ids[next_index])

    def export_outputs(self) -> None:
        if not self.draft_state:
            QMessageBox.warning(self, "Nothing to export", "Load a document before exporting.")
            return
        paths = ExportManager().export_all(self.ledger, self.draft_state.reconstruct(), self.audit_report)
        self.export_panel.set_status("Exported: " + ", ".join(str(path) for path in paths.values()))

    def _refresh_preview(self) -> None:
        if not self.draft_state:
            self.preview_panel.set_text("")
            self.audit_panel.set_text("")
            return
        text = self.draft_state.reconstruct()
        self.preview_panel.set_text(text)
        self.audit_panel.set_text(text)

    def _set_audit_report(self, report: str) -> None:
        self.audit_report = report

    def _ready_for_decision(self) -> bool:
        if not self.draft_state or not self.current_sentence_id:
            QMessageBox.warning(self, "No active sentence", "Load a document and select a sentence first.")
            return False
        return True
