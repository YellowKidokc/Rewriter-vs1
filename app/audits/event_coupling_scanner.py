#!/usr/bin/env python3
"""
event_coupling_scanner.py

Purpose
-------
Scan a local Theophysics/MDA folder for event passages that look "law-coupled":
not merely correlated, not merely thematic, but structurally tied to one of the
canonical laws/equations by mechanism, invariant, phase behavior, conservation,
boundary/falsification language, and evidence support.

This script is deliberately conservative:
- It does NOT claim proof.
- It does NOT claim true isomorphism.
- It produces "candidate couplings" for human review.
- It separates weak thematic similarity from stronger structural coupling.

Designed for folders like:
    Moral_Decay_of_America/
    Theophysics/
    03_Decade_Analysis/
    08_Methodology/
    90_Data/
    94_HTML/

Install optional dependencies:
    pip install beautifulsoup4 openpyxl

Basic use:
    python event_coupling_scanner.py /path/to/Moral_Decay_of_America --out coupling_scan

Stricter:
    python event_coupling_scanner.py /path/to/Moral_Decay_of_America --threshold 72 --out coupling_scan

Outputs:
    coupling_candidates.csv
    coupling_candidates.md
    coupling_index.json

Core idea
---------
For each event/passsage, score against law templates:

    thematic similarity      = low value
    mechanism match          = high value
    invariant/conservation   = high value
    phase/threshold behavior = high value
    temporal sequence        = medium/high value
    counterexample/boundary  = high value
    falsifiability language  = high value
    data/citation markers    = support confidence

A candidate is strongest when:
    law terms + mechanism + temporal direction + boundary/failure condition
    appear together in the same local passage.

Authoring note
--------------
This is a deterministic first pass. Later you can add an LLM review step that
takes each candidate and asks:
    "Does this actually instantiate the law, or is it just a metaphor?"
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# Canonical law templates
# =============================================================================


@dataclasses.dataclass
class LawTemplate:
    law_id: str
    name: str
    equation: str
    constructive: str
    destructive: str
    core_terms: List[str]
    mechanism_terms: List[str]
    invariant_terms: List[str]
    phase_terms: List[str]
    failure_terms: List[str]
    falsifier_terms: List[str]


LAW_TEMPLATES: List[LawTemplate] = [
    LawTemplate(
        law_id="LAW1",
        name="Gravitation | Sin ↔ Grace",
        equation="F = Gm1m2/r^2 ; curvature / attraction / event horizon",
        constructive="Grace draws; stable orbit; return/home curvature.",
        destructive="Sin traps; collapse; event horizon; singularity.",
        core_terms=["gravity", "gravitational", "curvature", "pull", "draw", "orbit", "mass"],
        mechanism_terms=["attraction", "drawn", "pulled", "bent", "curved", "trapped", "collapse"],
        invariant_terms=["bound", "binding", "escape", "threshold", "event horizon", "singularity"],
        phase_terms=["crosses", "threshold", "collapse", "stable orbit", "escape velocity"],
        failure_terms=["trap", "trapped", "cannot escape", "fall", "collapse"],
        falsifier_terms=["escape without external", "self-rescue", "no threshold"],
    ),
    LawTemplate(
        law_id="LAW2",
        name="Motion | Sin Nature ↔ Grace-as-Force",
        equation="F = ma ; F = dp/dt ; J = FΔt = Δp",
        constructive="External force changes direction/momentum.",
        destructive="Inertia preserves prior trajectory without correction.",
        core_terms=["motion", "force", "momentum", "inertia", "acceleration", "velocity"],
        mechanism_terms=["external force", "impulse", "direction change", "accelerate", "resists", "push"],
        invariant_terms=["momentum", "inertia", "trajectory", "mass", "force required"],
        phase_terms=["turning point", "conversion", "vector", "rotation", "change direction"],
        failure_terms=["stuck", "unchanged", "continues", "resists", "plateau"],
        falsifier_terms=["self-accelerates", "changes without force", "no external force"],
    ),
    LawTemplate(
        law_id="LAW3",
        name="Electromagnetism | Truth ↔ Deception",
        equation="Maxwell propagation ; phase / interference / signal",
        constructive="Truth propagates coherently; constructive interference.",
        destructive="Deception inverts signal; destructive interference.",
        core_terms=["truth", "deception", "signal", "wave", "phase", "light", "witness"],
        mechanism_terms=["propagate", "transmit", "interference", "inverted", "distorted", "signal fidelity"],
        invariant_terms=["speed", "fidelity", "phase lock", "coherence", "polarization"],
        phase_terms=["phase shift", "180", "out of phase", "constructive", "destructive"],
        failure_terms=["noise", "distortion", "inversion", "false signal", "blackout"],
        falsifier_terms=["truth decays", "signal destroyed without noise"],
    ),
    LawTemplate(
        law_id="LAW4",
        name="Strong Force | Love ↔ Captivity",
        equation="V(r) = -αs/r + k r ; bound state / confinement",
        constructive="Covenant bond permits freedom inside the bond.",
        destructive="Captivity/addiction binds; replacement bonds form when torn.",
        core_terms=["love", "bond", "covenant", "captivity", "addiction", "attachment", "confinement"],
        mechanism_terms=["bind", "bonded", "confined", "attachment", "distance", "replacement"],
        invariant_terms=["bound state", "binding energy", "confinement", "bond energy"],
        phase_terms=["break", "tear", "replacement", "new bond", "capture"],
        failure_terms=["captivity", "obsession", "addiction", "replacement addiction", "bondage"],
        falsifier_terms=["bond breaks without cost", "captivity ends without replacement"],
    ),
    LawTemplate(
        law_id="LAW5",
        name="Thermodynamics | Judgment ↔ Heat Death",
        equation="dS/dt ≥ 0 ; F = E - TS",
        constructive="Free energy remains available to build/maintain order.",
        destructive="Entropy dominates; heat death; sowing/reaping.",
        core_terms=["entropy", "thermodynamic", "decay", "disorder", "free energy", "heat death"],
        mechanism_terms=["decays", "dissipates", "falls apart", "energy", "maintenance", "order"],
        invariant_terms=["second law", "entropy production", "free energy", "cost", "work"],
        phase_terms=["phase transition", "runaway", "threshold", "collapse"],
        failure_terms=["heat death", "decay", "exhaustion", "dissipation", "unraveling"],
        falsifier_terms=["closed system maintains order", "entropy decreases without input"],
    ),
    LawTemplate(
        law_id="LAW6",
        name="Information | Logos ↔ Chaos",
        equation="H(X), C = B log2(1+S/N), K(x)",
        constructive="Signal separates from noise; intelligibility/compression increases.",
        destructive="Chaos/noise destroys identity and recoverability.",
        core_terms=["information", "logos", "chaos", "signal", "noise", "compression", "meaning"],
        mechanism_terms=["encode", "decode", "transmit", "compress", "recover", "noise floor"],
        invariant_terms=["channel capacity", "signal-to-noise", "recoverability", "fidelity"],
        phase_terms=["threshold", "noise floor", "capacity", "lossless", "lossy"],
        failure_terms=["noise", "chaos", "unrecoverable", "lost signal", "fragmentation"],
        falsifier_terms=["noise improves fidelity", "chaos increases recoverability"],
    ),
    LawTemplate(
        law_id="LAW7",
        name="Quantum Mechanics | Faith ↔ Doubt/Control",
        equation="HΨ = EΨ ; ΔxΔp ≥ ℏ/2 ; observation/collapse",
        constructive="Faith observes/collapses toward true state without controlling.",
        destructive="Fear/shame/control collapses into wrong state/mask.",
        core_terms=["quantum", "faith", "doubt", "control", "observer", "collapse", "uncertainty"],
        mechanism_terms=["observe", "measurement", "collapse", "superposition", "choice", "uncertainty"],
        invariant_terms=["uncertainty", "eigenstate", "observer", "state space"],
        phase_terms=["collapse", "decision", "measurement", "threshold"],
        failure_terms=["mask", "fear", "shame", "control", "wrong state"],
        falsifier_terms=["certainty preserves freedom", "no observer effect"],
    ),
    LawTemplate(
        law_id="LAW8",
        name="Relativity | Grace ↔ Frame Lock",
        equation="ds² ; Lorentz invariance ; E=mc²",
        constructive="Grace accommodates frames without contradiction.",
        destructive="Frame lock traps perspective; cannot reach God-view through finite frame.",
        core_terms=["frame", "relativity", "perspective", "invariant", "time", "speed", "causal"],
        mechanism_terms=["frame", "reference frame", "invariance", "time dilation", "redshift"],
        invariant_terms=["proper time", "causal order", "speed limit", "invariance"],
        phase_terms=["locked", "frame lock", "boundary", "speed limit"],
        failure_terms=["stuck in frame", "cannot see", "locked perspective"],
        falsifier_terms=["finite frame sees all frames", "causal order breaks"],
    ),
    LawTemplate(
        law_id="LAW9",
        name="Weak Force | Moral Conservation",
        equation="ψ_whole → ψ_broken + δ + ν_loss",
        constructive="External grace resolves conserved moral displacement.",
        destructive="Suppressed consequence returns as displacement/residual.",
        core_terms=["moral conservation", "conservation", "displacement", "residual", "suppression", "consequence"],
        mechanism_terms=["suppress", "displace", "moves", "reappears", "substitution", "residual", "externalize"],
        invariant_terms=["conserved", "nothing disappears", "remainder", "residual", "noether"],
        phase_terms=["identity change", "decay", "transformation", "substitution"],
        failure_terms=["underground", "black market", "replacement", "overflow", "blowback"],
        falsifier_terms=["deep drive eliminated by suppression", "no displacement", "no replacement", "pure suppression succeeds"],
    ),
    LawTemplate(
        law_id="LAW10",
        name="Coherence | Christ ↔ Decoherence",
        equation="χ = product(...) ; □P = 0 ; coherence output",
        constructive="Coherence holds distinctions/relations/operations without contradiction.",
        destructive="Decoherence is derivative; system loses integration.",
        core_terms=["coherence", "decoherence", "integration", "contradiction", "fragmentation", "system"],
        mechanism_terms=["integrates", "holds together", "coupled", "alignment", "contradiction", "fragmented"],
        invariant_terms=["no contradiction", "integration", "boundary", "harmonic", "uniqueness"],
        phase_terms=["coherence peak", "bifurcation", "decoupling", "collapse", "transition"],
        failure_terms=["fragmentation", "decoupling", "contradiction", "breakdown", "collapse"],
        falsifier_terms=["contradiction preserves function", "fragmentation increases coherence"],
    ),
]


# =============================================================================
# Event candidate structures
# =============================================================================


@dataclasses.dataclass
class EventCandidate:
    file_path: str
    file_role: str
    event_id: str
    title_or_context: str
    year_min: Optional[int]
    year_max: Optional[int]
    snippet: str
    law_id: str
    law_name: str
    coupling_score: float
    coupling_grade: str
    evidence_level: str
    match_reasons: List[str]
    matched_terms: Dict[str, List[str]]
    recommended_action: str
    passage_hash: str


# =============================================================================
# File reading
# =============================================================================


TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".html", ".htm", ".csv", ".json"}
EXCEL_SUFFIXES = {".xlsx", ".xlsm"}


def infer_role(path: Path) -> str:
    parts = [p.lower() for p in path.parts]
    joined = "/".join(parts)
    if "08_methodology" in joined or "method" in joined:
        return "methodology"
    if "90_data" in joined or "data" in joined or path.suffix.lower() in {".csv", ".xlsx", ".xlsm"}:
        return "data"
    if "03_decade" in joined or "decade" in joined:
        return "article_decade"
    if "06_case" in joined or "case" in joined:
        return "case_study"
    if "13_audits" in joined or "audit" in joined or "review" in joined:
        return "audit"
    if "94_html" in joined or path.suffix.lower() in {".html", ".htm"}:
        return "html_article"
    if "proof" in joined:
        return "proof_packet"
    return "unknown"


def read_text_file(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in {".html", ".htm"}:
        raw = strip_html(raw)
    return raw


def strip_html(raw: str) -> str:
    raw = re.sub(r"(?is)<script.*?>.*?</script>", " ", raw)
    raw = re.sub(r"(?is)<style.*?>.*?</style>", " ", raw)
    raw = re.sub(r"(?is)<[^>]+>", " ", raw)
    return html.unescape(re.sub(r"\s+", " ", raw)).strip()


def read_excel_text(path: Path, max_rows_per_sheet: int = 5000) -> str:
    try:
        from openpyxl import load_workbook
    except Exception:
        return ""

    try:
        wb = load_workbook(path, read_only=True, data_only=True)
    except Exception:
        return ""

    chunks: List[str] = []
    for ws in wb.worksheets:
        chunks.append(f"\n\nSHEET: {ws.title}\n")
        for idx, row in enumerate(ws.iter_rows(values_only=True)):
            if idx >= max_rows_per_sheet:
                chunks.append("[TRUNCATED SHEET]\n")
                break
            vals = [str(v) for v in row if v is not None and str(v).strip()]
            if vals:
                chunks.append(" | ".join(vals))
    return "\n".join(chunks)


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.suffix.lower() in EXCEL_SUFFIXES:
            yield path


def read_any(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in EXCEL_SUFFIXES:
        return read_excel_text(path)
    if suffix in TEXT_SUFFIXES:
        return read_text_file(path)
    return ""


# =============================================================================
# Passage/event extraction
# =============================================================================


YEAR_RE = re.compile(r"\b(1[5-9]\d{2}|20[0-3]\d)\b")
DATE_RANGE_RE = re.compile(r"\b(1[5-9]\d{2}|20[0-3]\d)\s*[–-]\s*(1[5-9]\d{2}|20[0-3]\d)\b")

EVENT_CUES = [
    "when", "after", "before", "during", "resulted", "led to", "caused",
    "collapse", "transition", "bifurcation", "threshold", "phase",
    "shift", "reversal", "spike", "decline", "increase", "decrease",
    "law", "ban", "policy", "court", "war", "revolution", "movement",
    "attendance", "trust", "divorce", "birth", "crime", "debt", "media",
]


def split_passages(text: str, max_chars: int = 1400) -> List[str]:
    # Prefer paragraphs first.
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paras) < 3:
        # Fall back to sentence windows.
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        paras = []
        window: List[str] = []
        size = 0
        for s in sentences:
            window.append(s)
            size += len(s)
            if size >= max_chars:
                paras.append(" ".join(window))
                window = []
                size = 0
        if window:
            paras.append(" ".join(window))

    # Merge tiny paragraphs with neighbors.
    merged: List[str] = []
    buffer = ""
    for p in paras:
        if len(buffer) + len(p) < 300:
            buffer = (buffer + " " + p).strip()
        else:
            if buffer:
                merged.append(buffer)
            buffer = p
    if buffer:
        merged.append(buffer)

    # Split oversized passages.
    out: List[str] = []
    for p in merged:
        if len(p) <= max_chars:
            out.append(p)
        else:
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", p) if s.strip()]
            buf: List[str] = []
            size = 0
            for s in sentences:
                buf.append(s)
                size += len(s)
                if size >= max_chars:
                    out.append(" ".join(buf))
                    buf = []
                    size = 0
            if buf:
                out.append(" ".join(buf))
    return out


def passage_has_event_signal(p: str) -> bool:
    lower = p.lower()
    if YEAR_RE.search(p):
        return True
    return any(cue in lower for cue in EVENT_CUES)


def extract_year_range(p: str) -> Tuple[Optional[int], Optional[int]]:
    ranges = DATE_RANGE_RE.findall(p)
    if ranges:
        years = []
        for a, b in ranges:
            years.append(int(a))
            years.append(int(b))
        return min(years), max(years)
    years = [int(y) for y in YEAR_RE.findall(p)]
    if years:
        return min(years), max(years)
    return None, None


# =============================================================================
# Scoring
# =============================================================================


def find_terms(text: str, terms: Sequence[str]) -> List[str]:
    lower = text.lower()
    found = []
    for term in terms:
        if term.lower() in lower:
            found.append(term)
    return sorted(set(found))


def evidence_level(text: str) -> str:
    lower = text.lower()
    has_num = bool(re.search(r"\b\d[\d,.]*\s*(%|percent|million|billion|per|sigma|σ)?\b", text, re.I))
    has_source = any(x in lower for x in [
        "source", "census", "nchs", "nces", "gallup", "pew", "fbi", "bjs",
        "cdc", "piketty", "saez", "kinsey", "doi", "journal", "table",
        "appendix", "sheet:", "dataset", "csv", "xlsx"
    ])
    has_method = any(x in lower for x in [
        "method", "regression", "correlation", "r²", "r2", "confidence",
        "bootstrap", "sensitivity", "threshold", "falsified", "kill condition"
    ])
    if has_num and has_source and has_method:
        return "EXACT_OR_METHOD_SUPPORT_CANDIDATE"
    if has_num and has_source:
        return "SOURCE_BACKED_CANDIDATE"
    if has_source:
        return "SOURCE_CONTEXT_ONLY"
    if has_num:
        return "NUMBER_WITHOUT_VISIBLE_SOURCE"
    return "NARRATIVE_ONLY"


def score_law_coupling(passage: str, law: LawTemplate) -> Tuple[float, List[str], Dict[str, List[str]]]:
    matched = {
        "core": find_terms(passage, law.core_terms),
        "mechanism": find_terms(passage, law.mechanism_terms),
        "invariant": find_terms(passage, law.invariant_terms),
        "phase": find_terms(passage, law.phase_terms),
        "failure": find_terms(passage, law.failure_terms),
        "falsifier": find_terms(passage, law.falsifier_terms),
    }

    reasons: List[str] = []
    score = 0.0

    if matched["core"]:
        score += min(18, 6 * len(matched["core"]))
        reasons.append(f"core terms: {', '.join(matched['core'][:6])}")

    if matched["mechanism"]:
        score += min(24, 8 * len(matched["mechanism"]))
        reasons.append(f"mechanism terms: {', '.join(matched['mechanism'][:6])}")

    if matched["invariant"]:
        score += min(22, 11 * len(matched["invariant"]))
        reasons.append(f"invariant/conservation terms: {', '.join(matched['invariant'][:6])}")

    if matched["phase"]:
        score += min(18, 9 * len(matched["phase"]))
        reasons.append(f"phase/threshold terms: {', '.join(matched['phase'][:6])}")

    if matched["failure"]:
        score += min(16, 8 * len(matched["failure"]))
        reasons.append(f"failure/decay terms: {', '.join(matched['failure'][:6])}")

    if matched["falsifier"]:
        score += min(18, 9 * len(matched["falsifier"]))
        reasons.append(f"falsifier/boundary terms: {', '.join(matched['falsifier'][:6])}")

    # Beyond-correlation bonuses: need multiple kinds of evidence in local passage.
    categories_present = sum(1 for k, v in matched.items() if v)
    if categories_present >= 3:
        score += 10
        reasons.append("beyond-correlation signal: >=3 structural categories matched")
    if matched["mechanism"] and matched["phase"]:
        score += 8
        reasons.append("mechanism + phase/threshold co-occur")
    if matched["mechanism"] and matched["invariant"]:
        score += 10
        reasons.append("mechanism + invariant/conservation co-occur")
    if matched["failure"] and matched["falsifier"]:
        score += 8
        reasons.append("failure mode + falsifier/boundary co-occur")

    # Temporal/data bonus.
    y_min, y_max = extract_year_range(passage)
    if y_min:
        score += 5
        reasons.append(f"temporal anchor: {y_min}" + (f"-{y_max}" if y_max and y_max != y_min else ""))

    ev = evidence_level(passage)
    if ev == "EXACT_OR_METHOD_SUPPORT_CANDIDATE":
        score += 12
        reasons.append("evidence support: number + source + method")
    elif ev == "SOURCE_BACKED_CANDIDATE":
        score += 8
        reasons.append("evidence support: number + source")
    elif ev == "SOURCE_CONTEXT_ONLY":
        score += 4
        reasons.append("evidence support: source context")
    elif ev == "NUMBER_WITHOUT_VISIBLE_SOURCE":
        score += 2
        reasons.append("number present but source not visible")

    return min(score, 100.0), reasons, matched


def coupling_grade(score: float) -> str:
    if score >= 82:
        return "STRONG_LAW_COUPLING_CANDIDATE"
    if score >= 70:
        return "USABLE_LAW_COUPLING_CANDIDATE"
    if score >= 55:
        return "WEAK_OR_THEMATIC_CANDIDATE"
    return "NO_COUPLING"


def recommended_action(grade: str, ev: str) -> str:
    if grade == "STRONG_LAW_COUPLING_CANDIDATE":
        if ev in {"EXACT_OR_METHOD_SUPPORT_CANDIDATE", "SOURCE_BACKED_CANDIDATE"}:
            return "Promote to proof/evidence review; verify source row/table and add link."
        return "Strong structural match but evidence thin; locate source before promotion."
    if grade == "USABLE_LAW_COUPLING_CANDIDATE":
        return "Human review; add as candidate coupling note if support exists."
    if grade == "WEAK_OR_THEMATIC_CANDIDATE":
        return "Keep as analogy/theme unless mechanism is strengthened."
    return "Ignore."


# =============================================================================
# Scanning
# =============================================================================


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def scan_file(path: Path, root: Path, threshold: float) -> List[EventCandidate]:
    text = read_any(path)
    if not text.strip():
        return []

    role = infer_role(path)
    rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    passages = [p for p in split_passages(text) if passage_has_event_signal(p)]
    results: List[EventCandidate] = []

    for idx, p in enumerate(passages):
        y_min, y_max = extract_year_range(p)
        for law in LAW_TEMPLATES:
            score, reasons, matched = score_law_coupling(p, law)
            if score < threshold:
                continue
            ev = evidence_level(p)
            grade = coupling_grade(score)
            snippet = re.sub(r"\s+", " ", p).strip()
            if len(snippet) > 900:
                snippet = snippet[:897] + "..."

            results.append(EventCandidate(
                file_path=rel,
                file_role=role,
                event_id=f"{path.stem}-{idx:04d}-{law.law_id}",
                title_or_context=path.stem,
                year_min=y_min,
                year_max=y_max,
                snippet=snippet,
                law_id=law.law_id,
                law_name=law.name,
                coupling_score=round(score, 2),
                coupling_grade=grade,
                evidence_level=ev,
                match_reasons=reasons,
                matched_terms=matched,
                recommended_action=recommended_action(grade, ev),
                passage_hash=hash_text(p),
            ))

    return results


def scan_root(root: Path, threshold: float, max_files: Optional[int] = None) -> List[EventCandidate]:
    all_results: List[EventCandidate] = []
    files = list(iter_files(root))
    if max_files:
        files = files[:max_files]

    for i, path in enumerate(files, 1):
        try:
            all_results.extend(scan_file(path, root, threshold))
        except Exception as exc:
            print(f"WARNING: failed {path}: {exc}")

    all_results.sort(key=lambda x: (-x.coupling_score, x.file_path, x.event_id))
    return all_results


# =============================================================================
# Output
# =============================================================================


def write_csv(path: Path, rows: List[EventCandidate]) -> None:
    fieldnames = [
        "coupling_score", "coupling_grade", "law_id", "law_name", "evidence_level",
        "file_role", "file_path", "year_min", "year_max", "event_id",
        "match_reasons", "recommended_action", "snippet", "passage_hash",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({
                "coupling_score": r.coupling_score,
                "coupling_grade": r.coupling_grade,
                "law_id": r.law_id,
                "law_name": r.law_name,
                "evidence_level": r.evidence_level,
                "file_role": r.file_role,
                "file_path": r.file_path,
                "year_min": r.year_min or "",
                "year_max": r.year_max or "",
                "event_id": r.event_id,
                "match_reasons": " | ".join(r.match_reasons),
                "recommended_action": r.recommended_action,
                "snippet": r.snippet,
                "passage_hash": r.passage_hash,
            })


def write_json(path: Path, rows: List[EventCandidate]) -> None:
    payload = {
        "schema": "event_coupling_scan_v1",
        "note": "Candidate law couplings only; human review required.",
        "count": len(rows),
        "rows": [dataclasses.asdict(r) for r in rows],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_markdown(path: Path, rows: List[EventCandidate], top_n: int = 100) -> None:
    lines: List[str] = [
        "# Event Coupling Scan",
        "",
        "Candidate law-coupled events/passages. This is not proof; it is a review queue.",
        "",
        f"Total candidates: **{len(rows)}**",
        "",
    ]

    by_law: Dict[str, int] = {}
    for r in rows:
        by_law[r.law_id] = by_law.get(r.law_id, 0) + 1

    lines.append("## Counts by Law")
    lines.append("")
    for law_id, count in sorted(by_law.items()):
        law_name = next((l.name for l in LAW_TEMPLATES if l.law_id == law_id), law_id)
        lines.append(f"- **{law_id}** — {law_name}: {count}")
    lines.append("")

    lines.append(f"## Top {min(top_n, len(rows))} Candidates")
    lines.append("")

    for i, r in enumerate(rows[:top_n], 1):
        lines.extend([
            f"### {i}. {r.coupling_grade} — {r.law_id}: {r.law_name}",
            "",
            f"- **Score:** {r.coupling_score}",
            f"- **Evidence level:** {r.evidence_level}",
            f"- **File:** `{r.file_path}`",
            f"- **Role:** `{r.file_role}`",
            f"- **Years:** {r.year_min or ''}{('-' + str(r.year_max)) if r.year_max and r.year_max != r.year_min else ''}",
            f"- **Why matched:** {'; '.join(r.match_reasons)}",
            f"- **Recommended action:** {r.recommended_action}",
            "",
            "> " + r.snippet.replace("\n", " ")[:1200],
            "",
        ])

    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary(path: Path, rows: List[EventCandidate]) -> None:
    strong = [r for r in rows if r.coupling_grade == "STRONG_LAW_COUPLING_CANDIDATE"]
    usable = [r for r in rows if r.coupling_grade == "USABLE_LAW_COUPLING_CANDIDATE"]

    summary = {
        "total": len(rows),
        "strong": len(strong),
        "usable": len(usable),
        "by_law": {},
        "by_role": {},
        "top_10": [dataclasses.asdict(r) for r in rows[:10]],
    }
    for r in rows:
        summary["by_law"][r.law_id] = summary["by_law"].get(r.law_id, 0) + 1
        summary["by_role"][r.file_role] = summary["by_role"].get(r.file_role, 0) + 1

    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


# =============================================================================
# CLI
# =============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan a folder for candidate law-coupled events/passages."
    )
    parser.add_argument("root", type=Path, help="Root folder to scan")
    parser.add_argument("--out", type=Path, default=Path("event_coupling_scan"), help="Output folder")
    parser.add_argument("--threshold", type=float, default=55.0, help="Minimum score to include")
    parser.add_argument("--max-files", type=int, default=None, help="Limit file count for testing")
    parser.add_argument("--top", type=int, default=100, help="Top candidates in Markdown")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"Root not found: {root}")

    args.out.mkdir(parents=True, exist_ok=True)

    rows = scan_root(root, threshold=args.threshold, max_files=args.max_files)

    write_csv(args.out / "coupling_candidates.csv", rows)
    write_json(args.out / "coupling_index.json", rows)
    write_markdown(args.out / "coupling_candidates.md", rows, top_n=args.top)
    write_summary(args.out / "coupling_summary.json", rows)

    print(f"Scanned: {root}")
    print(f"Candidates: {len(rows)}")
    print(f"Wrote: {args.out / 'coupling_candidates.csv'}")
    print(f"Wrote: {args.out / 'coupling_candidates.md'}")
    print(f"Wrote: {args.out / 'coupling_index.json'}")
    print(f"Wrote: {args.out / 'coupling_summary.json'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
