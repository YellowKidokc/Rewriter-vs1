"""Section and sentence segmentation for manual rewrite review."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'\u201c\u2018(\[])")

ABBREVIATIONS = (
    "Mr.",
    "Mrs.",
    "Ms.",
    "Dr.",
    "Prof.",
    "Rev.",
    "St.",
    "Mt.",
    "Fig.",
    "Eq.",
    "e.g.",
    "i.e.",
    "etc.",
    "vs.",
    "U.S.",
    "U.K.",
)


@dataclass
class SentenceRecord:
    id: str
    section: str
    text: str
    index: int


@dataclass
class SectionRecord:
    title: str
    level: int
    sentences: list[SentenceRecord] = field(default_factory=list)


def split_sentence_text(text: str) -> list[str]:
    normalized = re.sub(r"[ \t]+", " ", text.strip())
    if not normalized:
        return []
    protected, replacements = _protect_abbreviations(normalized)
    parts = [part.strip() for part in SENTENCE_RE.split(protected) if part.strip()]
    return [_restore_abbreviations(part, replacements) for part in parts]


def _protect_abbreviations(text: str) -> tuple[str, dict[str, str]]:
    replacements: dict[str, str] = {}
    protected = text
    for index, abbreviation in enumerate(ABBREVIATIONS):
        token = f"__ABBR_{index}__"
        replacements[token] = abbreviation
        protected = protected.replace(abbreviation, token)
    return protected, replacements


def _restore_abbreviations(text: str, replacements: dict[str, str]) -> str:
    restored = text
    for token, abbreviation in replacements.items():
        restored = restored.replace(token, abbreviation)
    return restored


def split_document(text: str) -> list[SectionRecord]:
    sections: list[SectionRecord] = []
    current_title = "ROOT"
    current_level = 0
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_lines
        body = "\n".join(current_lines).strip()
        section = SectionRecord(title=current_title, level=current_level)
        for sentence in split_sentence_text(body):
            sentence_id = f"s{sum(len(s.sentences) for s in sections) + len(section.sentences) + 1:04d}"
            section.sentences.append(SentenceRecord(sentence_id, current_title, sentence, len(section.sentences)))
        if section.sentences or current_title != "ROOT":
            sections.append(section)
        current_lines = []

    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            flush()
            current_level = len(match.group(1))
            current_title = match.group(2).strip()
        else:
            current_lines.append(line)
    flush()
    return sections


def flatten_sentences(sections: list[SectionRecord]) -> list[SentenceRecord]:
    return [sentence for section in sections for sentence in section.sentences]
