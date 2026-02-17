from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ABAP_RAG_", extra="ignore")

    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 900
    chunk_overlap: int = 120
    top_k: int = 4
    index_path: Path = Path(".rag_store/faiss.index")
    metadata_path: Path = Path(".rag_store/metadata.json")


settings = Settings()
