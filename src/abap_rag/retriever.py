from __future__ import annotations

from .embedder import Embedder
from .models import RetrievedChunk
from .vector_store import VectorStore


class Retriever:
    def __init__(self, embedder: Embedder, vector_store: VectorStore, top_k: int):
        self.embedder = embedder
        self.vector_store = vector_store
        self.top_k = top_k

    def retrieve(self, query: str) -> list[RetrievedChunk]:
        query_embedding = self.embedder.encode([query])
        return self.vector_store.search(query_embedding=query_embedding, top_k=self.top_k)
