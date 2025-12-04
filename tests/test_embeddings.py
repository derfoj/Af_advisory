# tests/test_embeddings.py

from __future__ import annotations

import numpy as np

from backend.embeddings_manager import EmbeddingsManager


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-10
    return float(a @ b / denom)


def test_embedding_shape_and_dim():
    manager = EmbeddingsManager()  # uses default model (bert)

    texts = ["hello world", "total sales 2023"]
    # ❌ old: vecs = manager.embed(texts, model="simple")
    vecs = manager.embed(texts)  # use default model

    # should return 2 vectors (one per text)
    assert vecs.shape[0] == 2

    # should be 2D (n_samples, dim)
    assert len(vecs.shape) == 2

    # each vector should be (almost) unit norm
    for v in vecs:
        assert np.isclose(np.linalg.norm(v), 1.0, atol=1e-5)


def test_similarity_higher_for_related_queries():
    manager = EmbeddingsManager()  # uses default model (bert)

    q1 = "total sales by month in 2023"
    q2 = "monthly revenue for 2023"
    q3 = "list all customer addresses"

    # ❌ old: manager.embed([q1], model="simple")[0]
    v1 = manager.embed([q1])[0]
    v2 = manager.embed([q2])[0]
    v3 = manager.embed([q3])[0]

    sim_12 = cosine_similarity(v1, v2)
    sim_13 = cosine_similarity(v1, v3)

    # similar sales queries should be closer than unrelated address query
    assert sim_12 > sim_13


def test_empty_input_returns_empty_array():
    manager = EmbeddingsManager()  # uses default model (bert)
    vecs = manager.embed([])
    assert vecs.shape[0] == 0
