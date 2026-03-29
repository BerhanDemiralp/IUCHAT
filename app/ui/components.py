"""Streamlit UI components."""

from __future__ import annotations

import streamlit as st

from app.models import ChunkResult, SearchResult
from app.config import settings


def search_form() -> tuple[str, int, bool]:
    """Render the search form and return (query, top_k, submitted)."""
    st.header("🎓 İstanbul Üniversitesi-Cerrahpaşa Asistanı")

    query = st.text_input(
        "Sorunuzu yazın",
        placeholder="e.g. Neden Bilgisayar Mühendislğinini tercih etmeliyim? / Lisans Mezuniyet şartları nelerdir?",
        key="query_input",
    )

    top_k = st.slider(
        "Number of results (top-k)",
        min_value=1,
        max_value=20,
        value=settings.DEFAULT_TOP_K,
        key="top_k_slider"
    )

    submitted = st.button("Search", type="primary", use_container_width=True)

    return query, top_k, submitted


def display_llm_answer(answer: str) -> None:
    """Render the LLM-generated answer."""
    st.markdown("### 🤖 Cevap")
    st.markdown(answer)


def display_results(search_result: SearchResult) -> None:
    """Render search results as expandable cards with score badges."""
    if not search_result.results:
        st.warning("No results found.")
        return

    st.markdown("---")
    st.markdown(
        f"**{len(search_result.results)}** kaynak bulundu: *{search_result.query}*"
    )

    for i, chunk in enumerate(search_result.results, start=1):
        _render_chunk_card(i, chunk)


def _render_chunk_card(rank: int, chunk: ChunkResult) -> None:
    """Render a single chunk as a styled expander."""
    score_pct = chunk.score * 100
    label = (
        f"#{rank}  |  {chunk.file_name}  |  "
        f"Page {chunk.chunk_page_no or '?'}  |  "
        f"Score: {score_pct:.1f}%"
    )
    with st.expander(label, expanded=False):
        st.markdown(chunk.chunk_text)


def page_config() -> None:
    """Set global Streamlit page config (call once at top of main)."""
    st.set_page_config(
        page_title="İÜC Asistanı",
        page_icon="🎓",
        layout="centered",
    )
