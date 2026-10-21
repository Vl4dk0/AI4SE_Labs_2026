"""Find source files and cut long ones into pieces the extractor can finish."""

from __future__ import annotations

from pathlib import Path

from .models import Document

_SUFFIXES = {".txt", ".eml", ".md"}


def discover_documents(input_dir: Path) -> list[Document]:
    """Every text-like file under the directory, id'd by its relative path.

    Names are not fixed: a similar corpus in another folder has to work.
    """
    documents: list[Document] = []
    for path in sorted(input_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        documents.append(
            Document(doc_id=path.relative_to(input_dir).as_posix(), text=text)
        )
    return documents


def split_text(text: str, limit: int = 12_000, overlap: int = 400) -> list[str]:
    """Split only when one call would be too long to answer completely.

    The break is on a line boundary, with a short overlap so a requirement
    that straddles the cut still appears whole in one of the pieces.
    """
    if len(text) <= limit:
        return [text]
    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + limit)
        if end < len(text):
            break_at = text.rfind("\n", start + limit // 2, end)
            if break_at != -1:
                end = break_at
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= len(text):
            break
        next_start = max(end - overlap, start + 1)
        start = next_start
    return pieces or [text]


def head_tail(text: str, head: int = 8_000, tail: int = 1_500) -> str:
    """Genre and date sit at the ends; the middle is for extraction, not labeling."""
    if len(text) <= head + tail:
        return text
    omitted = "\n\n[... middle omitted for classification ...]\n\n"
    return text[:head] + omitted + text[-tail:]
