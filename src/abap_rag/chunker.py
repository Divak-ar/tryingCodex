from __future__ import annotations

from .models import DocumentChunk


def _title_from_text(text: str) -> str:
    for line in text.splitlines():
        clean = line.strip("# ").strip()
        if clean:
            return clean[:80]
    return "Untitled ABAP document"


def chunk_document(source: str, text: str, chunk_size: int, overlap: int) -> list[DocumentChunk]:
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    chunks: list[DocumentChunk] = []
    start = 0
    idx = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        body = text[start:end].strip()
        if body:
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{source}:{idx}",
                    source=source,
                    title=_title_from_text(body),
                    text=body,
                )
            )
            idx += 1
        start += chunk_size - overlap

    return chunks
