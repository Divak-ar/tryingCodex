from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        vecs = self.model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return np.asarray(vecs, dtype="float32")
