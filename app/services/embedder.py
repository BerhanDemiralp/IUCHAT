"""Embedding service — wraps SentenceTransformer with caching and normalization."""

from __future__ import annotations

import logging
import os
import warnings
from typing import List

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

warnings.filterwarnings("ignore")

for noisy_logger in (
    "transformers",
    "transformers.modeling_utils",
    "transformers.tokenization_utils",
    "transformers.tokenization_utils_base",
    "sentence_transformers",
    "sentence_transformers.SentenceTransformer",
    "huggingface_hub",
    "torch",
    "urllib3",
):
    logging.getLogger(noisy_logger).setLevel(logging.ERROR)

import streamlit as st
from sentence_transformers import SentenceTransformer

try:
    from transformers.utils import logging as hf_logging

    hf_logging.set_verbosity_error()
    hf_logging.disable_progress_bar()
except Exception:
    pass

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
