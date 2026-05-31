"""Working draft state that updates after each accepted sentence decision."""

from __future__ import annotations

from dataclasses import dataclass, field

from .sentence_splitter import SectionRecord, SentenceRecord, flatten_sentences


@dataclass
class DraftState:
    sections: list[SectionRecord]
    replacements: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_sections(cls, sections: list[SectionRecord]) -> "DraftState":
        return cls(sections=sections)

    @property
    def sentences(self) -> list[SentenceRecord]:
        return flatten_sentences(self.sections)

    def current_text_for(self, sentence_id: str) -> str:
        sentence = self.sentence_by_id(sentence_id)
        return self.replacements.get(sentence_id, sentence.text)

    def sentence_by_id(self, sentence_id: str) -> SentenceRecord:
        for sentence in self.sentences:
            if sentence.id == sentence_id:
                return sentence
        raise KeyError(f"Unknown sentence id: {sentence_id}")

    def apply_rewrite(self, sentence_id: str, text: str) -> None:
        self.replacements[sentence_id] = text

    def leave_unchanged(self, sentence_id: str) -> None:
        self.replacements.pop(sentence_id, None)

    def reconstruct(self) -> str:
        chunks: list[str] = []
        for section in self.sections:
            if section.title != "ROOT":
                heading = "#" * max(1, section.level or 1)
                chunks.append(f"{heading} {section.title}")
            if section.sentences:
                chunks.append(" ".join(self.current_text_for(sentence.id) for sentence in section.sentences))
        return "\n\n".join(chunk for chunk in chunks if chunk).strip() + "\n"
