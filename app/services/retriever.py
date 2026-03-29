"""Retrieval service — calls Supabase RPC for similarity search."""

from __future__ import annotations

from typing import List

from app.config import settings
from app.models import ChunkResult, SearchResult
from app.services.supabase_client import get_supabase_client


def retrieve(
    query: str,
    query_embedding: List[float],
    top_k: int | None = None,
) -> SearchResult:
    """Call the `match_chunks` RPC and return structured results.

    Parameters
    ----------
    query : str
        Original user query (for display / logging).
    query_embedding : list[float]
        Normalised embedding vector for the query.
    top_k : int | None
        Number of results. Falls back to ``settings.DEFAULT_TOP_K``.
    """
    if top_k is None:
        top_k = settings.DEFAULT_TOP_K

    client = get_supabase_client()

    response = client.rpc(
        settings.RPC_FUNCTION,
        {
            "query_embedding": query_embedding,
            "match_count": top_k,
        },
    ).execute()

    rows = response.data or []

    results = [
        ChunkResult(
            file_name=r["file_name"],
            chunk_index=r["chunk_index"],
            chunk_page_no=r.get("chunk_page_no"),
            chunk_text=r["chunk_text"],
            score=round(r["score"], 4),
        )
        for r in rows
    ]

    return SearchResult(query=query, top_k=top_k, results=results)
