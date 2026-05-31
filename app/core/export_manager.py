"""Export rewrite ledgers, reconstructed drafts, rejected options, and audit notes."""

from __future__ import annotations

import json
from pathlib import Path

from .rewrite_ledger import RewriteLedger


class ExportManager:
    def __init__(self, output_dir: str | Path = "outputs") -> None:
        self.output_dir = Path(output_dir)

    def export_all(self, ledger: RewriteLedger, reconstructed: str, audit_report: str = "") -> dict[str, Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            "json": self.output_dir / "rewrite_decisions.json",
            "markdown": self.output_dir / "rewrite_decisions.md",
            "draft": self.output_dir / "paper_reconstructed.md",
            "rejected": self.output_dir / "paper_rejected_options.md",
            "audit": self.output_dir / "audit_report.md",
        }
        paths["json"].write_text(json.dumps(ledger.to_list(), indent=2, ensure_ascii=False), encoding="utf-8")
        paths["markdown"].write_text(self._ledger_markdown(ledger), encoding="utf-8")
        paths["draft"].write_text(reconstructed, encoding="utf-8")
        paths["rejected"].write_text(self._rejected_markdown(ledger), encoding="utf-8")
        paths["audit"].write_text(audit_report or "# Audit Report\n\nNo audit has been run in this session.\n", encoding="utf-8")
        return paths

    def _ledger_markdown(self, ledger: RewriteLedger) -> str:
        lines = ["# Rewrite Decisions", ""]
        for entry in ledger.all_entries():
            lines.extend([
                f"## {entry.sentence_id} - {entry.status}",
                f"- Section: {entry.section}",
                f"- Selected: {entry.selected or 'None'}",
                f"- Meaning drift risk: {entry.meaning_drift_risk}",
                f"- Claim strength risk: {entry.claim_strength_risk}",
                f"- Reason: {entry.reason or 'Not supplied'}",
                "",
                "**Original**",
                "",
                entry.original,
                "",
                "**Current before decision**",
                "",
                entry.current_before_decision,
                "",
            ])
        return "\n".join(lines).strip() + "\n"

    def _rejected_markdown(self, ledger: RewriteLedger) -> str:
        lines = ["# Rejected Alternatives", ""]
        for entry in ledger.all_entries():
            rejected = [candidate for candidate in entry.candidates if candidate.label != entry.selected]
            if not rejected:
                continue
            lines.append(f"## {entry.sentence_id} - {entry.section}")
            for candidate in rejected:
                lines.extend([
                    f"### Candidate {candidate.label}",
                    f"- Score: {candidate.score}",
                    f"- Reason: {candidate.reason or 'Not supplied'}",
                    f"- Risks: {', '.join(candidate.risks) if candidate.risks else 'None listed'}",
                    "",
                    candidate.text or "_(blank)_",
                    "",
                ])
        return "\n".join(lines).strip() + "\n"
