from __future__ import annotations

from pathlib import Path


def load_text_documents(path: Path) -> dict[str, str]:
    """Load .txt, .md, and .abap files from a folder recursively."""
    if not path.exists():
        raise FileNotFoundError(f"Document path not found: {path}")

    docs: dict[str, str] = {}
    for file in path.rglob("*"):
        if file.suffix.lower() not in {".txt", ".md", ".abap"}:
            continue
        docs[str(file)] = file.read_text(encoding="utf-8", errors="ignore")

    return docs
