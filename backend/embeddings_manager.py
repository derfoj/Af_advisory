# backend/embeddings_manager.py

from typing import List, Literal

import numpy as np

# Example: from sentence_transformers import SentenceTransformer
# Example: from langchain_community.embeddings import OpenAIEmbeddings

ModelType = Literal["bert", "vana", "langchain"]

class EmbeddingsManager:
    def __init__(self):
        # Lazy-load models to avoid heavy startup
        self._bert_model = None
        self._vana_model = None
        self._langchain_model = None

    def _load_bert(self):
        if self._bert_model is None:
            from sentence_transformers import SentenceTransformer
            self._bert_model = SentenceTransformer("all-MiniLM-L6-v2")

    def _load_langchain(self):
        if self._langchain_model is None:
            from langchain_community.embeddings import OpenAIEmbeddings
            self._langchain_model = OpenAIEmbeddings()  # configure via env vars

    def embed(self, texts: List[str], model: ModelType = "bert") -> np.ndarray:
        if not texts:
            return np.array([])

        if model == "bert":
            self._load_bert()
            vectors = self._bert_model.encode(texts)
        elif model == "langchain":
            self._load_langchain()
            vectors = self._langchain_model.embed_documents(texts)
        elif model == "vana":
            # TODO: integrate real VANA model
            raise NotImplementedError("VANA model not yet integrated.")
        else:
            raise ValueError(f"Unknown model: {model}")

        return np.array(vectors)
