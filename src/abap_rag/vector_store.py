from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np

from .models import DocumentChunk, RetrievedChunk


class VectorStore:
    def __init__(self, index_path: Path, metadata_path: Path):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.index: faiss.IndexFlatIP | None = None
        self.metadata: list[DocumentChunk] = []

    def build(self, embeddings: np.ndarray, chunks: list[DocumentChunk]) -> None:
        if len(chunks) == 0:
            raise ValueError("No chunks to index")
        self.index = faiss.IndexFlatIP(embeddings.shape[1])
        self.index.add(embeddings)
        self.metadata = chunks

    def save(self) -> None:
        if self.index is None:
            raise RuntimeError("Index not built")
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self.index, str(self.index_path))
        payload = [c.__dict__ for c in self.metadata]
        self.metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self) -> None:
        if not self.index_path.exists() or not self.metadata_path.exists():
            raise FileNotFoundError("Index or metadata file missing")
        self.index = faiss.read_index(str(self.index_path))
        raw = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        self.metadata = [DocumentChunk(**c) for c in raw]

    def search(self, query_embedding: np.ndarray, top_k: int) -> list[RetrievedChunk]:
        if self.index is None:
            raise RuntimeError("Index is not loaded")
        scores, ids = self.index.search(query_embedding, top_k)
        rows: list[RetrievedChunk] = []
        for score, idx in zip(scores[0], ids[0]):
            if idx < 0:
                continue
            rows.append(RetrievedChunk(chunk=self.metadata[idx], score=float(score)))
        return rows
