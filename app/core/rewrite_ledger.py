"""Progressive rewrite ledger data model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Literal

Status = Literal["accepted", "rejected", "unchanged", "needs_review"]
Risk = Literal["low", "medium", "high"]


@dataclass
class RewriteCandidate:
    label: str
    text: str
    score: int = 0
    reason: str = ""
    risks: list[str] = field(default_factory=list)


@dataclass
class RewriteLedgerEntry:
    sentence_id: str
    section: str
    original: str
    current_before_decision: str
    problem_type: str = "manual_review"
    candidates: list[RewriteCandidate] = field(default_factory=list)
    selected: str = ""
    status: Status = "unchanged"
    reason: str = ""
    meaning_drift_risk: Risk = "low"
    claim_strength_risk: Risk = "low"
    decided_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RewriteLedger:
    entries: dict[str, RewriteLedgerEntry] = field(default_factory=dict)

    def record(self, entry: RewriteLedgerEntry) -> None:
        self.entries[entry.sentence_id] = entry

    def all_entries(self) -> list[RewriteLedgerEntry]:
        return [self.entries[key] for key in sorted(self.entries)]

    def to_list(self) -> list[dict]:
        return [entry.to_dict() for entry in self.all_entries()]
