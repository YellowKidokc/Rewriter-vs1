#!/usr/bin/env python3
"""
combined_theophysics_paper_auditor.py

Combined version:
- Kimi-style measurement first
- GPT-style adversarial claim-control second
- Produces JSON + Markdown reports

Usage:
    python combined_theophysics_paper_auditor.py paper.md
    python combined_theophysics_paper_auditor.py paper.md --outdir reports
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple


DEFAULT_MOTIFS = [
    "coherence", "entropy", "grace", "law", "faith", "truth", "collapse",
    "observer", "free will", "logos", "cross", "resurrection", "justice",
    "mercy", "order", "disorder", "closed system", "open system",
]

PROOF_TAGS = ["[p]", "[k]", "[s]", "[a]", "[proof]", "[claim]", "[evidence]", "[falsify]"]

ABSOLUTE_TERMS = [
    "proves", "proved", "proof", "undeniable", "impossible", "always", "never",
    "must", "cannot", "exact", "identical", "certain", "settled", "irrefutable",
    "no way", "every", "all", "none",
]

EVIDENCE_TERMS = [
    "because", "therefore", "data", "test", "verified", "simulation", "derivation",
    "lemma", "theorem", "Lean", "formalized", "measured", "observed", "citation",
]

CORE_TERMS = [
    "coherence", "entropy", "grace", "faith", "free will", "observer",
    "collapse", "logos", "justice", "mercy", "truth", "master equation",
    "isomorphism", "phase transition",
]

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
DEFINED_TERM_RE = re.compile(r"^\s*(?:[-*]\s*)?([A-Z][A-Za-z0-9_\-\s]{1,50})\s*(?::=|=|::|—|-)\s*(.+)$")


@dataclass
class Finding:
    severity: str
    category: str
    location: str
    text: str
    recommendation: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-z][A-Za-z'\-]*", text.lower())


def split_sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text) if p.strip()]


def split_sections(text: str) -> List[Tuple[str, str]]:
    lines = text.splitlines()
    sections = []
    heading = "ROOT"
    body = []
    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            if body or heading != "ROOT":
                sections.append((heading, "\n".join(body).strip()))
            heading = m.group(2).strip()
            body = []
        else:
            body.append(line)
    sections.append((heading, "\n".join(body).strip()))
    return sections


def stdev(xs: List[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x-m)**2 for x in xs) / (len(xs)-1))


def lexical_stats(text: str) -> Dict:
    tokens = tokenize(text)
    sentences = split_sentences(text)
    lengths = [len(tokenize(s)) for s in sentences] or [0]
    return {
        "word_count": len(tokens),
        "unique_words": len(set(tokens)),
        "type_token_ratio": round(len(set(tokens)) / len(tokens), 4) if tokens else 0,
        "sentence_count": len(sentences),
        "avg_sentence_words": round(sum(lengths) / len(lengths), 2),
        "sentence_length_stdev": round(stdev(lengths), 2),
        "max_sentence_words": max(lengths),
    }


def section_weights(sections: List[Tuple[str, str]]) -> List[Dict]:
    total = sum(len(tokenize(b)) for _, b in sections) or 1
    return [
        {
            "section": h,
            "words": len(tokenize(b)),
            "percent": round(100 * len(tokenize(b)) / total, 2),
            "sentences": len(split_sentences(b)),
        }
        for h, b in sections
    ]


def motif_distribution(text: str, motifs: List[str]) -> Dict:
    lower = text.lower()
    return dict(sorted(
        ((m, len(re.findall(re.escape(m.lower()), lower))) for m in motifs),
        key=lambda kv: (-kv[1], kv[0])
    ))


def ngrams(tokens: List[str], n: int) -> Counter:
    return Counter(tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1))


def redundancy_scan(text: str) -> Dict:
    tokens = tokenize(text)
    def top(counter: Counter, min_count: int, limit: int = 20):
        return [{"phrase": " ".join(k), "count": v} for k, v in counter.most_common(limit) if v >= min_count]
    return {
        "repeated_trigrams": top(ngrams(tokens, 3), 3),
        "repeated_4grams": top(ngrams(tokens, 4), 2),
        "repeated_5grams": top(ngrams(tokens, 5), 2),
    }


def proof_tag_coverage(text: str, sections: List[Tuple[str, str]]) -> Dict:
    lower = text.lower()
    totals = {tag: lower.count(tag.lower()) for tag in PROOF_TAGS}
    per = []
    claim_re = re.compile(r"\b(must|therefore|proves?|shows?|demonstrates?|requires?|cannot|always|never)\b", re.I)
    for h, b in sections:
        tag_count = sum(b.lower().count(tag.lower()) for tag in PROOF_TAGS)
        claim_count = len(claim_re.findall(b))
        per.append({
            "section": h,
            "proof_tag_count": tag_count,
            "strong_claim_signal_count": claim_count,
            "possible_gap": claim_count > 0 and tag_count == 0,
        })
    return {"total_tags": totals, "per_section": per}


def coherence_signal(text: str, sections: List[Tuple[str, str]], motifs: List[str]) -> Dict:
    rows = []
    for h, b in sections:
        hits = [m for m in motifs if m.lower() in b.lower()]
        rows.append({"section": h, "distinct_core_motifs": len(hits), "motifs": hits})
    avg = round(sum(r["distinct_core_motifs"] for r in rows) / len(rows), 2) if rows else 0
    return {"avg_distinct_motifs_per_section": avg, "by_section": rows}


def current_section_for_offset(text: str, offset: int) -> str:
    section = "ROOT"
    for m in HEADING_RE.finditer(text):
        if m.start() <= offset:
            section = m.group(2).strip()
        else:
            break
    return section


def adversarial_findings(text: str) -> List[Finding]:
    findings: List[Finding] = []
    pattern = "|".join(re.escape(t) for t in ABSOLUTE_TERMS)
    for m in re.finditer(pattern, text, flags=re.I):
        window = text[max(0, m.start()-250): min(len(text), m.end()+250)].lower()
        evidence_near = any(t.lower() in window for t in EVIDENCE_TERMS)
        snippet = re.sub(r"\s+", " ", text[max(0, m.start()-100): min(len(text), m.end()+160)]).strip()
        findings.append(Finding(
            severity="MEDIUM" if evidence_near else "HIGH",
            category="Overclaim / burden of proof",
            location=current_section_for_offset(text, m.start()),
            text=snippet,
            recommendation="Add evidence/derivation/proof tag or downgrade to structural/provisional language."
        ))
    defined = set()
    for line in text.splitlines():
        dm = DEFINED_TERM_RE.match(line)
        if dm:
            defined.add(dm.group(1).strip().lower())
    lower = text.lower()
    for term in CORE_TERMS:
        tl = term.lower()
        if tl in lower and not any(tl == d or tl in d for d in defined):
            findings.append(Finding(
                severity="MEDIUM",
                category="Undefined core term",
                location="GLOBAL",
                text=term,
                recommendation=f"Define '{term}' before it carries argumentative weight."
            ))
    for row in proof_tag_coverage(text, split_sections(text))["per_section"]:
        if row["possible_gap"]:
            findings.append(Finding(
                severity="HIGH",
                category="Strong claims without proof tags",
                location=row["section"],
                text=f"{row['strong_claim_signal_count']} strong-claim signals, {row['proof_tag_count']} proof tags.",
                recommendation="Add [p]/[k]/[s]/[a] tags or downgrade claims."
            ))
    return findings


def severity_counts(findings: List[Finding]) -> Dict:
    return {
        "HIGH": sum(1 for f in findings if f.severity == "HIGH"),
        "MEDIUM": sum(1 for f in findings if f.severity == "MEDIUM"),
        "LOW": sum(1 for f in findings if f.severity == "LOW"),
        "TOTAL": len(findings),
    }


def verdict(counts: Dict, stats: Dict) -> str:
    high = counts["HIGH"]
    medium = counts["MEDIUM"]
    wc = stats.get("word_count", 0)
    if high == 0 and medium <= 5:
        return "Clean structural pass; still requires human truth review."
    if high <= max(3, wc // 2500):
        return "Usable draft with targeted claim-control fixes."
    return "Needs revision before external-facing use."


def run_audit(path: Path) -> Dict:
    text = read_text(path)
    sections = split_sections(text)
    stats = lexical_stats(text)
    findings = adversarial_findings(text)
    return {
        "file": str(path),
        "note": "Combined report: structural measurement + adversarial claim-control. Not a truth validator.",
        "measurement": {
            "lexical_stats": stats,
            "section_weights": section_weights(sections),
            "motif_distribution": motif_distribution(text, DEFAULT_MOTIFS),
            "redundancy_scan": redundancy_scan(text),
            "proof_tag_coverage": proof_tag_coverage(text, sections),
            "coherence_signal": coherence_signal(text, sections, DEFAULT_MOTIFS),
        },
        "adversarial": {
            "severity_counts": severity_counts(findings),
            "findings": [asdict(f) for f in findings],
        },
        "verdict": verdict(severity_counts(findings), stats),
    }


def render_markdown(report: Dict) -> str:
    lines = [
        "# Combined Theophysics Paper Audit",
        "",
        f"File: `{report['file']}`",
        "",
        report["note"],
        "",
        "## Verdict",
        report["verdict"],
        "",
        "## Measurement Summary",
    ]
    stats = report["measurement"]["lexical_stats"]
    for k, v in stats.items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Section Weights"]
    for row in report["measurement"]["section_weights"]:
        lines.append(f"- {row['section']}: {row['words']} words ({row['percent']}%)")
    lines += ["", "## Top Motifs"]
    for motif, count in list(report["measurement"]["motif_distribution"].items())[:20]:
        lines.append(f"- {motif}: {count}")
    lines += ["", "## Adversarial Findings"]
    counts = report["adversarial"]["severity_counts"]
    lines += [f"- HIGH: {counts['HIGH']}", f"- MEDIUM: {counts['MEDIUM']}", f"- LOW: {counts['LOW']}", f"- TOTAL: {counts['TOTAL']}", ""]
    for i, f in enumerate(report["adversarial"]["findings"], start=1):
        lines += [
            f"### {i}. [{f['severity']}] {f['category']}",
            f"- Location: {f['location']}",
            f"- Text: {f['text']}",
            f"- Recommendation: {f['recommendation']}",
            "",
        ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--outdir", type=Path, default=Path("audit_reports"))
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    report = run_audit(args.file)
    stem = args.file.stem
    json_path = args.outdir / f"{stem}_combined_audit.json"
    md_path = args.outdir / f"{stem}_combined_audit.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")
    print(report["verdict"])


if __name__ == "__main__":
    main()
