"""Retrieval service — calls Supabase RPC for similarity search."""

from __future__ import annotations

import time
from typing import List

import httpx

from app.config import settings
from app.models import ChunkResult, SearchResult
from app.services.supabase_client import get_supabase_client

_TRANSIENT_HTTPX_ERRORS: tuple[type[BaseException], ...] = (
    httpx.RemoteProtocolError,
    httpx.ReadError,
    httpx.ReadTimeout,
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.PoolTimeout,
)

_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = 0.4


def _execute_rpc_with_retry(query_embedding: List[float], top_k: int):
    """Run the RPC call with retry + cached-client reset on transient errors."""
    last_error: Exception | None = None
    for attempt in range(_MAX_ATTEMPTS):
        client = get_supabase_client()
        try:
            return client.rpc(
                settings.RPC_FUNCTION,
                {
                    "query_embedding": query_embedding,
                    "match_count": top_k,
                },
            ).execute()
        except _TRANSIENT_HTTPX_ERRORS as exc:
            last_error = exc
            get_supabase_client.cache_clear()
            if attempt == _MAX_ATTEMPTS - 1:
                break
            time.sleep(_BACKOFF_SECONDS * (attempt + 1))

    assert last_error is not None
    raise last_error


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

    response = _execute_rpc_with_retry(query_embedding, top_k)

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
