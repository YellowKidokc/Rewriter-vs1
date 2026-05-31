"""Document loading helpers for Markdown, text, and HTML inputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .html_cleaner import html_to_text

SUPPORTED_EXTENSIONS = {".md", ".markdown", ".txt", ".html", ".htm"}


@dataclass(frozen=True)
class LoadedDocument:
    path: Path
    original_text: str
    working_text: str
    file_type: str


def load_document(path: str | Path) -> LoadedDocument:
    source = Path(path).expanduser().resolve()
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {source.suffix}. Use .md, .txt, .html, or .htm.")
    raw = source.read_text(encoding="utf-8", errors="replace")
    text = html_to_text(raw) if source.suffix.lower() in {".html", ".htm"} else raw
    return LoadedDocument(path=source, original_text=raw, working_text=text, file_type=source.suffix.lower())
