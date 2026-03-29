"""Embedding service — wraps SentenceTransformer with caching and normalization."""

from __future__ import annotations

import os
import warnings
from typing import List

os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore")

import streamlit as st
from sentence_transformers import SentenceTransformer

from app.config import settings


@st.cache_resource(show_spinner="Yükleniyor...")
def load_model() -> SentenceTransformer:
    """Load and cache the SentenceTransformer model."""
    return SentenceTransformer(settings.EMBEDDING_MODEL_NAME)


def embed_query(text: str) -> List[float]:
    """Encode a single query string with L2-normalisation."""
    model = load_model()
    vector = model.encode(
        text,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vector.tolist()
