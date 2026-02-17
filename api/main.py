from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from abap_rag.pipeline import RagPipeline
from abap_rag.settings import settings

app = FastAPI(title="SAP ABAP RAG System", version="0.1.0")
pipeline = RagPipeline(settings)


class IngestRequest(BaseModel):
    path: str = "data"


class AskRequest(BaseModel):
    query: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest")
def ingest(payload: IngestRequest) -> dict:
    docs_path = Path(payload.path)
    try:
        count = pipeline.ingest(docs_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"indexed_chunks": count, "path": str(docs_path)}


@app.post("/ask")
def ask(payload: AskRequest) -> dict:
    try:
        pipeline.load_index()
        return pipeline.ask(payload.query)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail="Index not found. Run /ingest first.") from exc
