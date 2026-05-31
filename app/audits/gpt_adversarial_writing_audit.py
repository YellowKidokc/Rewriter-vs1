#!/usr/bin/env python3
"""
gpt_adversarial_writing_audit.py

GPT-style adversarial writing audit.

Purpose:
- Finds overclaims, missing burden of proof, undefined terms, rhetorical inflation,
  proof/claim mismatches, and structural weak points.
- Designed to protect a Theophysics-style paper from overstatement.

Usage:
    python gpt_adversarial_writing_audit.py path/to/paper.md
    python gpt_adversarial_writing_audit.py path/to/paper.md --out adversarial_report.md
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict


ABSOLUTE_TERMS = [
    "proves", "proved", "proof", "undeniable", "impossible", "always", "never",
    "must", "cannot", "exact", "identical", "certain", "settled", "irrefutable",
    "no way", "every", "all", "none",
]

EVIDENCE_TERMS = [
    "because", "therefore", "data", "test", "verified", "simulation", "derivation",
    "lemma", "theorem", "Lean", "formalized", "measured", "observed", "citation",
]

DEFINED_TERM_RE = re.compile(r"^\s*(?:[-*]\s*)?([A-Z][A-Za-z0-9_\-\s]{1,50})\s*(?::=|=|::|—|-)\s*(.+)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass
class Finding:
    severity: str
    category: str
    location: str
    text: str
    recommendation: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def split_paragraphs(text: str) -> List[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def current_section_for_offset(text: str, offset: int) -> str:
    section = "ROOT"
    for m in HEADING_RE.finditer(text):
        if m.start() <= offset:
            section = m.group(2).strip()
        else:
            break
    return section


def find_overclaims(text: str) -> List[Finding]:
    findings = []
    for m in re.finditer("|".join(re.escape(t) for t in ABSOLUTE_TERMS), text, flags=re.I):
        start = max(0, m.start() - 100)
        end = min(len(text), m.end() + 160)
        snippet = re.sub(r"\s+", " ", text[start:end]).strip()
        section = current_section_for_offset(text, m.start())
        window = text[max(0, m.start()-250):min(len(text), m.end()+250)].lower()
        evidence_near = any(t.lower() in window for t in EVIDENCE_TERMS)
        severity = "HIGH" if not evidence_near else "MEDIUM"
        findings.append(Finding(
            severity=severity,
            category="Overclaim / burden of proof",
            location=section,
            text=snippet,
            recommendation="Either add evidence/derivation or downgrade language to structural/provisional."
        ))
    return findings


def find_undefined_core_terms(text: str, core_terms: List[str]) -> List[Finding]:
    defined = set()
    for line in text.splitlines():
        dm = DEFINED_TERM_RE.match(line)
        if dm:
            defined.add(dm.group(1).strip().lower())
    findings = []
    lower = text.lower()
    for term in core_terms:
        term_low = term.lower()
        if term_low in lower and not any(term_low == d or term_low in d for d in defined):
            findings.append(Finding(
                severity="MEDIUM",
                category="Undefined core term",
                location="GLOBAL",
                text=term,
                recommendation=f"Add a compact definition for '{term}' before using it as load-bearing."
            ))
    return findings


def find_claim_without_support(text: str) -> List[Finding]:
    findings = []
    paragraphs = split_paragraphs(text)
    strong_claim_re = re.compile(r"\b(proves?|shows?|demonstrates?|requires?|therefore|must|cannot|always|never)\b", re.I)
    for idx, p in enumerate(paragraphs, start=1):
        if strong_claim_re.search(p):
            support = any(t.lower() in p.lower() for t in EVIDENCE_TERMS)
            has_tag = bool(re.search(r"\[(p|k|s|a|proof|claim|evidence|falsify)\]", p, re.I))
            if not support and not has_tag:
                findings.append(Finding(
                    severity="HIGH",
                    category="Unsupported strong claim",
                    location=f"paragraph {idx}",
                    text=re.sub(r"\s+", " ", p[:350]).strip(),
                    recommendation="Attach proof tag, evidence, derivation, or downgrade the claim."
                ))
    return findings


def find_repetition(text: str) -> List[Finding]:
    words = re.findall(r"[A-Za-z][A-Za-z'\-]*", text.lower())
    findings = []
    for n in [5, 6, 7]:
        grams: Dict[tuple, int] = {}
        for i in range(len(words)-n+1):
            g = tuple(words[i:i+n])
            grams[g] = grams.get(g, 0) + 1
        repeated = sorted([(g, c) for g, c in grams.items() if c >= 3], key=lambda x: -x[1])[:15]
        for g, c in repeated:
            findings.append(Finding(
                severity="LOW",
                category=f"Repeated {n}-gram",
                location="GLOBAL",
                text=" ".join(g) + f"  [count={c}]",
                recommendation="Keep if intentional motif; cut if accidental redundancy."
            ))
    return findings


def score(findings: List[Finding]) -> Dict[str, int]:
    return {
        "HIGH": sum(1 for f in findings if f.severity == "HIGH"),
        "MEDIUM": sum(1 for f in findings if f.severity == "MEDIUM"),
        "LOW": sum(1 for f in findings if f.severity == "LOW"),
        "TOTAL": len(findings),
    }


def render_markdown(path: Path, findings: List[Finding]) -> str:
    counts = score(findings)
    lines = [
        "# Adversarial Writing Audit",
        "",
        f"File: `{path}`",
        "",
        "This report tests claim-control, not truth.",
        "",
        "## Summary",
        f"- HIGH: {counts['HIGH']}",
        f"- MEDIUM: {counts['MEDIUM']}",
        f"- LOW: {counts['LOW']}",
        f"- TOTAL: {counts['TOTAL']}",
        "",
        "## Findings",
    ]
    for i, f in enumerate(findings, start=1):
        lines += [
            f"### {i}. [{f.severity}] {f.category}",
            f"- Location: {f.location}",
            f"- Text: {f.text}",
            f"- Recommendation: {f.recommendation}",
            "",
        ]
    return "\n".join(lines)


def audit(path: Path) -> str:
    text = read_text(path)
    core_terms = [
        "coherence", "entropy", "grace", "faith", "free will", "observer",
        "collapse", "logos", "justice", "mercy", "truth", "master equation",
        "isomorphism", "phase transition",
    ]
    findings: List[Finding] = []
    findings.extend(find_overclaims(text))
    findings.extend(find_undefined_core_terms(text, core_terms))
    findings.extend(find_claim_without_support(text))
    findings.extend(find_repetition(text))
    return render_markdown(path, findings)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    report = audit(args.file)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
