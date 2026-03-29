"""Embedding service — wraps SentenceTransformer with caching and normalization."""

from __future__ import annotations

from functools import lru_cache
from typing import List

import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

from app.config import settings


@st.cache_resource(show_spinner="Loading embedding model…")
def load_model() -> SentenceTransformer:
    """Load and cache the SentenceTransformer model (Streamlit resource cache)."""
    return SentenceTransformer(settings.EMBEDDING_MODEL_NAME)


def embed_query(text: str) -> List[float]:
    """Encode a single query string with L2-normalisation.

    Returns a plain Python list suitable for JSON serialisation.
    """
    model = load_model()
    vector = model.encode(
        text,
        normalize_embeddings=True,   # must match offline pipeline
        show_progress_bar=False,
    )
    return vector.tolist()
