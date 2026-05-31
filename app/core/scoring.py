"""Candidate scoring model for manual rewrite decisions."""

from __future__ import annotations

from dataclasses import dataclass, field


POSITIVE_LIMITS = {
    "clarity_gain": 20,
    "structural_fit": 15,
    "claim_accuracy": 20,
    "rhythm_improvement": 10,
    "reader_comprehension": 10,
    "paragraph_coherence": 10,
    "style_fit": 10,
    "redundancy_reduction": 5,
}

PENALTY_LIMITS = {
    "meaning_drift": 30,
    "overclaim_increase": 30,
    "loss_of_nuance": 20,
    "tone_mismatch": 10,
    "new_ambiguity": 10,
}


@dataclass
class ScoreBreakdown:
    positives: dict[str, int] = field(default_factory=lambda: {key: 0 for key in POSITIVE_LIMITS})
    penalties: dict[str, int] = field(default_factory=lambda: {key: 0 for key in PENALTY_LIMITS})

    def total(self) -> int:
        positive_total = sum(_clamp(value, POSITIVE_LIMITS[key]) for key, value in self.positives.items())
        penalty_total = sum(_clamp(value, PENALTY_LIMITS[key]) for key, value in self.penalties.items())
        return max(0, min(100, positive_total - penalty_total))


def _clamp(value: int, limit: int) -> int:
    return max(0, min(limit, int(value)))


def score_candidate(breakdown: ScoreBreakdown | None = None, **values: int) -> int:
    """Score a candidate with the configured 0-100 weighted formula."""
    breakdown = breakdown or ScoreBreakdown()
    for key, value in values.items():
        if key in breakdown.positives:
            breakdown.positives[key] = value
        elif key in breakdown.penalties:
            breakdown.penalties[key] = value
        else:
            raise KeyError(f"Unknown scoring factor: {key}")
    return breakdown.total()


def acceptance_guidance(score: int, claim_risk: str, meaning_risk: str) -> str:
    if meaning_risk in {"medium", "high"} or claim_risk in {"medium", "high"}:
        return "Needs David Review"
    if score >= 75:
        return "Acceptable if it improves clarity or structure."
    return "Do not accept automatically; leave unchanged or review."
