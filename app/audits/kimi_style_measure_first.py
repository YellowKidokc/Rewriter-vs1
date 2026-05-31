#!/usr/bin/env python3
"""
kimi_style_measure_first.py

Kimi-style "measure before reading" writing audit.

Purpose:
- Analyze a Markdown/text paper structurally before making editorial judgments.
- Measures motif frequency, section weight, sentence rhythm, redundancy, proof-tag coverage,
  and basic coherence signals.

Usage:
    python kimi_style_measure_first.py path/to/paper.md
    python kimi_style_measure_first.py path/to/paper.md --out report.json
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


DEFAULT_MOTIFS = [
    "coherence", "entropy", "grace", "law", "faith", "truth", "collapse",
    "observer", "free will", "logos", "cross", "resurrection", "justice",
    "mercy", "order", "disorder", "closed system", "open system",
]

PROOF_TAGS = ["[p]", "[k]", "[s]", "[a]", "[proof]", "[claim]", "[evidence]", "[falsify]"]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def split_sections(text: str) -> List[Tuple[str, str]]:
    lines = text.splitlines()
    sections = []
    current_heading = "ROOT"
    current_body = []
    heading_re = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    for line in lines:
        m = heading_re.match(line)
        if m:
            if current_body or current_heading != "ROOT":
                sections.append((current_heading, "\n".join(current_body).strip()))
            current_heading = m.group(2).strip()
            current_body = []
        else:
            current_body.append(line)
    sections.append((current_heading, "\n".join(current_body).strip()))
    return sections


def split_sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text)
    return [p.strip() for p in parts if p.strip()]


def tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-z][A-Za-z'\-]*", text.lower())


def ngrams(tokens: List[str], n: int) -> Counter:
    return Counter(tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1))


def stdev(xs: List[float]) -> float:
    if len(xs) <= 1:
        return 0.0
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x-m)**2 for x in xs) / (len(xs)-1))


def lexical_stats(text: str) -> Dict:
    tokens = tokenize(text)
    sentences = split_sentences(text)
    lengths = [len(tokenize(s)) for s in sentences] or [0]
    unique = set(tokens)
    return {
        "word_count": len(tokens),
        "unique_words": len(unique),
        "type_token_ratio": round(len(unique) / len(tokens), 4) if tokens else 0,
        "sentence_count": len(sentences),
        "avg_sentence_words": round(sum(lengths) / len(lengths), 2),
        "max_sentence_words": max(lengths),
        "min_sentence_words": min(lengths),
        "sentence_length_stdev": round(stdev(lengths), 2),
    }


def motif_distribution(text: str, motifs: List[str]) -> Dict:
    lowered = text.lower()
    result = {}
    for motif in motifs:
        pattern = re.escape(motif.lower())
        result[motif] = len(re.findall(pattern, lowered))
    return dict(sorted(result.items(), key=lambda kv: (-kv[1], kv[0])))


def section_weights(sections: List[Tuple[str, str]]) -> List[Dict]:
    total_words = sum(len(tokenize(body)) for _, body in sections) or 1
    rows = []
    for heading, body in sections:
        wc = len(tokenize(body))
        rows.append({
            "section": heading,
            "words": wc,
            "percent": round(100 * wc / total_words, 2),
            "sentences": len(split_sentences(body)),
        })
    return rows


def redundancy_scan(text: str, top_n: int = 25) -> Dict:
    tokens = tokenize(text)
    def top(counter: Counter, min_count: int):
        return [
            {"phrase": " ".join(k), "count": v}
            for k, v in counter.most_common(top_n)
            if v >= min_count
        ]
    return {
        "repeated_bigrams": top(ngrams(tokens, 2), 5),
        "repeated_trigrams": top(ngrams(tokens, 3), 3),
        "repeated_4grams": top(ngrams(tokens, 4), 2),
    }


def proof_tag_coverage(text: str, sections: List[Tuple[str, str]]) -> Dict:
    lowered = text.lower()
    total = {tag: lowered.count(tag.lower()) for tag in PROOF_TAGS}
    per_section = []
    for heading, body in sections:
        b = body.lower()
        count = sum(b.count(tag.lower()) for tag in PROOF_TAGS)
        claims = len(re.findall(r"\b(must|therefore|proves?|shows?|demonstrates?|requires?|cannot|always|never)\b", b))
        per_section.append({
            "section": heading,
            "proof_tag_count": count,
            "strong_claim_signal_count": claims,
            "possible_gap": claims > 0 and count == 0,
        })
    return {"total_tags": total, "per_section": per_section}


def coherence_signal(text: str, motifs: List[str]) -> Dict:
    sections = split_sections(text)
    motif_hits_by_section = defaultdict(int)
    section_map = dict(sections)
    for heading, body in sections:
        body_low = body.lower()
        motif_hits_by_section[heading] = sum(1 for m in motifs if m.lower() in body_low)
    counts = list(motif_hits_by_section.values())
    avg = sum(counts) / len(counts) if counts else 0
    low_sections = [h for h, c in motif_hits_by_section.items() if c == 0 and len(tokenize(section_map.get(h, ""))) > 50]
    return {
        "avg_distinct_motifs_per_section": round(avg, 2),
        "sections_with_no_core_motifs": low_sections,
        "warning": "Coherence score is structural only, not truth validation.",
    }


def audit(path: Path, motifs: List[str]) -> Dict:
    text = read_text(path)
    sections = split_sections(text)
    return {
        "file": str(path),
        "kimi_style_note": "Measure before reading. This is a structural audit, not a truth judgment.",
        "lexical_stats": lexical_stats(text),
        "section_weights": section_weights(sections),
        "motif_distribution": motif_distribution(text, motifs),
        "redundancy_scan": redundancy_scan(text),
        "proof_tag_coverage": proof_tag_coverage(text, sections),
        "coherence_signal": coherence_signal(text, motifs),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--motif", action="append", default=None, help="Add/override motifs. Repeatable.")
    args = parser.parse_args()
    motifs = args.motif if args.motif else DEFAULT_MOTIFS
    report = audit(args.file, motifs)
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(payload, encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
