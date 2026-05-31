"""Risk checks for manual rewrite candidates."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

Risk = Literal["low", "medium", "high"]

NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?%?\b")
YEAR_RE = re.compile(r"\b(?:1[5-9]\d{2}|20\d{2})\b")
BRACKET_CITATION_RE = re.compile(r"\[[^\]]+\]")
PAREN_CITATION_RE = re.compile(r"\((?:[A-Z][A-Za-z-]+(?:\s+et\s+al\.)?,?\s+\d{4}|[A-Z][A-Za-z-]+,\s+\d{4})\)")
SCRIPTURE_RE = re.compile(r"\b(?:[1-3]\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+\d+:\d+(?:-\d+)?\b")
PROTECTED_TERM_RE = re.compile(
    r"\b(?:Jesus|Christ|Trinity|God|Logos|grace|sin|atonement|Noether|Shannon|entropy|"
    r"coherence|decoherence|free will|Master Equation|Theophysics|MDA|GTQ|Lean)\b",
    re.IGNORECASE,
)

WEAK_TO_STRONG = (
    ("suggests", "proves"),
    ("may", "must"),
    ("could", "does"),
    ("correlates", "causes"),
    ("consistent with", "demonstrates"),
    ("model-based", "established"),
    ("provisional", "settled"),
)


@dataclass
class ChangeGuardReport:
    meaning_risk: Risk = "low"
    claim_strength_risk: Risk = "low"
    warnings: list[str] = field(default_factory=list)


def analyze_candidate(original: str, candidate: str) -> ChangeGuardReport:
    report = ChangeGuardReport()

    _compare_set("number", _numbers(original), _numbers(candidate), report, "high")
    _compare_set("year/date", set(YEAR_RE.findall(original)), set(YEAR_RE.findall(candidate)), report, "high")
    _compare_set("citation", _citations(original), _citations(candidate), report, "high")
    _compare_set("Scripture reference", set(SCRIPTURE_RE.findall(original)), set(SCRIPTURE_RE.findall(candidate)), report, "high")
    _compare_set("protected term", _protected_terms(original), _protected_terms(candidate), report, "medium")

    lowered_original = original.lower()
    lowered_candidate = candidate.lower()
    for weak, strong in WEAK_TO_STRONG:
        if weak in lowered_original and strong in lowered_candidate:
            report.claim_strength_risk = _max_risk(report.claim_strength_risk, "high")
            report.warnings.append(f"Claim strength increased: '{weak}' -> '{strong}'.")

    if len(candidate.strip()) < max(12, len(original.strip()) * 0.45):
        report.meaning_risk = _max_risk(report.meaning_risk, "medium")
        report.warnings.append("Candidate is much shorter than the original; check for lost nuance.")

    return report


def _numbers(text: str) -> set[str]:
    return set(NUMBER_RE.findall(text)) - set(YEAR_RE.findall(text))


def _citations(text: str) -> set[str]:
    return set(BRACKET_CITATION_RE.findall(text)) | set(PAREN_CITATION_RE.findall(text))


def _protected_terms(text: str) -> set[str]:
    return {match.group(0).lower() for match in PROTECTED_TERM_RE.finditer(text)}


def _compare_set(label: str, original: set[str], candidate: set[str], report: ChangeGuardReport, risk: Risk) -> None:
    if original == candidate:
        return
    missing = sorted(original - candidate)
    added = sorted(candidate - original)
    if missing:
        report.meaning_risk = _max_risk(report.meaning_risk, risk)
        report.warnings.append(f"Candidate removed {label}(s): {', '.join(missing)}.")
    if added:
        report.meaning_risk = _max_risk(report.meaning_risk, risk)
        report.warnings.append(f"Candidate added {label}(s): {', '.join(added)}.")


def _max_risk(current: Risk, candidate: Risk) -> Risk:
    order = {"low": 0, "medium": 1, "high": 2}
    return candidate if order[candidate] > order[current] else current
