from __future__ import annotations

from pathlib import Path

from .chunker import chunk_document
from .embedder import Embedder
from .generator import PromptGenerator
from .loader import load_text_documents
from .retriever import Retriever
from .settings import Settings
from .vector_store import VectorStore


class RagPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.embedder = Embedder(settings.embedding_model_name)
        self.vector_store = VectorStore(settings.index_path, settings.metadata_path)
        self.retriever = Retriever(
            embedder=self.embedder,
            vector_store=self.vector_store,
            top_k=settings.top_k,
        )

    def ingest(self, docs_path: Path) -> int:
        docs = load_text_documents(docs_path)
        all_chunks = []
        for source, text in docs.items():
            all_chunks.extend(
                chunk_document(
                    source=source,
                    text=text,
                    chunk_size=self.settings.chunk_size,
                    overlap=self.settings.chunk_overlap,
                )
            )

        embeddings = self.embedder.encode([c.text for c in all_chunks])
        self.vector_store.build(embeddings=embeddings, chunks=all_chunks)
        self.vector_store.save()
        return len(all_chunks)

    def load_index(self) -> None:
        self.vector_store.load()

    def ask(self, query: str) -> dict:
        rows = self.retriever.retrieve(query)
        answer = PromptGenerator.generate(query, rows)
        return {
            "query": query,
            "answer": answer,
            "contexts": [
                {
                    "source": row.chunk.source,
                    "chunk_id": row.chunk.chunk_id,
                    "score": row.score,
                    "text": row.chunk.text,
                }
                for row in rows
            ],
        }
