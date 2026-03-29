"""Streamlit entry point — RAG Retrieval System with Gemini LLM."""

import streamlit as st

from app.ui.components import page_config, search_form, display_llm_answer, display_results
from app.services.embedder import embed_query
from app.services.retriever import retrieve
from app.services.llm import build_context, generate_answer


@st.cache_resource(show_spinner="Loading embedding model...")
def init_model():
    """Preload embedding model at app startup."""
    from app.services.embedder import load_model
    return load_model()


page_config()
init_model()


def main() -> None:
    query, top_k, submitted = search_form()

    if not submitted or not query.strip():
        st.info("Enter a question and press **Search**.")
        return

    with st.spinner("Generating embedding…"):
        embedding = embed_query(query.strip())

    with st.spinner("Searching Supabase…"):
        result = retrieve(
            query=query.strip(),
            query_embedding=embedding,
            top_k=top_k,
        )

    if not result.results:
        st.warning("No results found.")
        return

    context = build_context(result.results)

    with st.spinner("Generating answer with Gemini…"):
        answer = generate_answer(query.strip(), context)

    display_llm_answer(answer)
    display_results(result)


if __name__ == "__main__":
    main()
