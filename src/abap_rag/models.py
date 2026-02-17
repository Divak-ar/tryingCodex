from dataclasses import dataclass


@dataclass(slots=True)
class DocumentChunk:
    chunk_id: str
    source: str
    title: str
    text: str


@dataclass(slots=True)
class RetrievedChunk:
    chunk: DocumentChunk
    score: float
