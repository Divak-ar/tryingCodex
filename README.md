# SAP ABAP Document RAG System

This project implements a complete Retrieval-Augmented Generation (RAG) workflow focused on SAP ABAP documentation.

## Architecture

1. **Ingestion**
   - Reads `.md`, `.txt`, `.abap` files recursively.
   - Splits text into overlapping chunks.
2. **Embedding**
   - Converts chunks into dense vectors with SentenceTransformers.
3. **Vector Indexing**
   - Stores normalized vectors in FAISS (inner-product similarity).
   - Persists metadata for chunk provenance.
4. **Retrieval**
   - Encodes query and fetches top-k chunks.
5. **Generation Layer**
   - Builds a grounded answer prompt with source snippets and scores.

## Project Structure

- `src/abap_rag/` core pipeline and modules
- `api/main.py` FastAPI service
- `scripts/cli.py` command line helper
- `data/` sample ABAP documents
- `tests/` unit tests

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e . pytest
```

### Run API

```bash
uvicorn api.main:app --reload
```

Then call:

```bash
curl -X POST localhost:8000/ingest -H "content-type: application/json" -d '{"path":"data"}'
curl -X POST localhost:8000/ask -H "content-type: application/json" -d '{"query":"How should I optimize ABAP SELECT statements?"}'
```

### CLI usage

```bash
python scripts/cli.py ingest data
python scripts/cli.py ask "When should I use HASHED TABLE in ABAP?"
```

## Notes

- First run may download embedding model weights.
- Replace `PromptGenerator` with an LLM call (OpenAI/Azure/SAP AI Core) for production-grade answers.
- Adjust chunking and top-k via environment variables:
  - `ABAP_RAG_CHUNK_SIZE`
  - `ABAP_RAG_CHUNK_OVERLAP`
  - `ABAP_RAG_TOP_K`
