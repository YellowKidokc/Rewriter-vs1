"""Minimal HTML-to-text cleanup for the rewrite workbench."""

from __future__ import annotations

import html
import re


def html_to_text(source: str) -> str:
    """Convert HTML into readable Markdown-ish text without overwriting source files."""
    text = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", "", source)
    for level in range(6, 0, -1):
        text = re.sub(rf"(?is)<h{level}[^>]*>(.*?)</h{level}>", lambda m: "\n" + "#" * level + " " + _strip_tags(m.group(1)) + "\n", text)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|section|article|li|ul|ol|blockquote)>", "\n", text)
    text = _strip_tags(text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)
