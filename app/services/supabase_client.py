"""Supabase client wrapper."""

from __future__ import annotations

from functools import lru_cache
from supabase import create_client, Client

from app.config import settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Return a cached Supabase client instance."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise EnvironmentError(
            "SUPABASE_URL and SUPABASE_KEY must be set in .env or environment."
        )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
