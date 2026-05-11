"""Retrieval service — calls Supabase RPC for similarity search.

The default RPC is ``match_chunks_hybrid`` which combines a Turkish
full-text search (BM25-ish via ``ts_rank_cd``) with cosine vector
similarity using Reciprocal Rank Fusion. Falls back to the legacy
``match_chunks`` (pure semantic) if hybrid is unavailable in the database.
"""

from __future__ import annotations

import logging
import time
from typing import Any, List

import httpx

from app.config import settings
from app.models import ChunkResult, SearchResult
from app.services.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

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
_HYBRID_RPC = "match_chunks_hybrid"
_LEGACY_RPC = "match_chunks"


def _call_rpc(rpc_name: str, params: dict[str, Any]):
    """Execute a Supabase RPC with retry + cached-client reset.

    Logs each transient retry to the console so silent stream resets or
    timeouts don't disappear into the void.
    """
    last_error: Exception | None = None
    start = time.perf_counter()
    for attempt in range(_MAX_ATTEMPTS):
        client = get_supabase_client()
        try:
            response = client.rpc(rpc_name, params).execute()
            if attempt > 0:
                logger.info(
                    "RPC '%s' succeeded on attempt %d/%d (%.0fms total)",
                    rpc_name,
                    attempt + 1,
                    _MAX_ATTEMPTS,
                    (time.perf_counter() - start) * 1000,
                )
            return response
        except _TRANSIENT_HTTPX_ERRORS as exc:
            last_error = exc
            get_supabase_client.cache_clear()
            logger.warning(
                "RPC '%s' transient error on attempt %d/%d: %s — yeniden deniyorum...",
                rpc_name,
                attempt + 1,
                _MAX_ATTEMPTS,
                type(exc).__name__,
            )
            if attempt == _MAX_ATTEMPTS - 1:
                break
            time.sleep(_BACKOFF_SECONDS * (attempt + 1))

    assert last_error is not None
    logger.error(
        "RPC '%s' failed after %d attempts (%.0fms total): %s",
        rpc_name,
        _MAX_ATTEMPTS,
        (time.perf_counter() - start) * 1000,
        last_error,
    )
    raise last_error


def _is_missing_function_error(exc: BaseException) -> bool:
    """Heuristic: tell whether the Postgres error means the RPC doesn't exist."""
    msg = str(exc).lower()
    return (
        "could not find" in msg
        or "function" in msg and "does not exist" in msg
        or "pgrst202" in msg
        or "not found in the schema cache" in msg
    )


def _execute_hybrid(query_text: str, query_embedding: List[float], top_k: int):
    """Try hybrid RPC; on missing-function error fall back to legacy."""
    try:
        return _call_rpc(
            _HYBRID_RPC,
            {
                "query_text": query_text,
                "query_embedding": query_embedding,
                "match_count": top_k,
            },
        )
    except Exception as exc:
        if _is_missing_function_error(exc):
            logger.warning(
                "Hybrid RPC '%s' not available; falling back to '%s'. "
                "Run scripts/match_function.sql in Supabase to enable hybrid search.",
                _HYBRID_RPC,
                _LEGACY_RPC,
            )
            return _call_rpc(
                _LEGACY_RPC,
                {
                    "query_embedding": query_embedding,
                    "match_count": top_k,
                },
            )
        raise


def retrieve(
    query: str,
    query_embedding: List[float],
    top_k: int | None = None,
    fts_query: str | None = None,
) -> SearchResult:
    """Run hybrid retrieval and return structured results.

    Parameters
    ----------
    query : str
        Original user query (for display / logging).
    query_embedding : list[float]
        Normalised embedding vector for the query (already enriched).
    top_k : int | None
        Number of final results. Falls back to ``settings.DEFAULT_TOP_K``.
    fts_query : str | None
        Text used for the keyword / FTS leg of hybrid search. Defaults
        to ``query`` if not supplied.
    """
    if top_k is None:
        top_k = settings.DEFAULT_TOP_K

    fts_text = (fts_query if fts_query is not None else query).strip()
    response = _execute_hybrid(fts_text, query_embedding, top_k)

    rows = response.data or []

    results = [
        ChunkResult(
            file_name=r["file_name"],
            chunk_index=r["chunk_index"],
            chunk_page_no=r.get("chunk_page_no"),
            chunk_text=r["chunk_text"],
            score=round(float(r["score"]), 4),
        )
        for r in rows
    ]

    return SearchResult(query=query, top_k=top_k, results=results)
