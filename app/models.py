"""Data models for the RAG system."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class ChunkResult:
    """A single retrieved chunk returned from the similarity search."""

    file_name: str
    chunk_index: int
    chunk_page_no: int | None
    chunk_text: str
    score: float


@dataclass
class SearchResult:
    """Aggregated search results."""

    query: str
    top_k: int
    results: List[ChunkResult] = field(default_factory=list)
