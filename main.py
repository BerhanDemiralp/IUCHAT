"""Streamlit entry point — chat-first IUC assistant with RAG."""

import logging
import os
import sys
import warnings
from pathlib import Path

os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

warnings.filterwarnings("ignore")

for _noisy_logger in (
    "transformers",
    "sentence_transformers",
    "huggingface_hub",
    "torch",
    "urllib3",
):
    logging.getLogger(_noisy_logger).setLevel(logging.ERROR)

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("iuchat")

ERROR_MESSAGE = (
    "Üzgünüm, sorunu işlerken beklenmeyen bir sorun yaşadım. "
    "Birkaç saniye sonra tekrar dener misin? Sorun devam ederse "
    "soruyu farklı kelimelerle yazmayı deneyebilirsin."
)

from app.ui.components import (
    AGENT_AVATAR_URL,
    format_sources_markdown,
    inject_sidebar_silhouette,
    inject_styles,
    page_config,
    render_chat_header,
    render_chat_input,
    render_chat_messages,
    render_topbar,
    render_sidebar,
    render_suggestion_chips,
)
from app.services.embedder import embed_query
from app.services.retriever import retrieve
from app.services.llm import build_context, generate_answer_stream
from app.services.query_enrichment import enrich_query


@st.cache_resource(show_spinner="Loading embedding model...")
def init_model():
    """Preload embedding model at app startup."""
    from app.services.embedder import load_model
    return load_model()


page_config()
inject_styles()
inject_sidebar_silhouette()
init_model()


def _init_session_state() -> None:
    """Initialize chat state once per session."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hadi sohbete başlayalım. "
                    "Ne öğrenmek istiyorsun?"
                ),
            }
        ]

    if "pending_chip_question" not in st.session_state:
        st.session_state.pending_chip_question = None
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None
    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False


def _reset_chat() -> None:
    """Reset chat history."""
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Yeni sohbet başlatıldı.\n\n"
                "İÜC ile ilgili sorularınızı yazabilirsiniz."
            ),
        }
    ]
    st.session_state.pending_chip_question = None
    st.session_state.pending_prompt = None
    st.session_state.is_generating = False


def _retrieve_context(query: str, top_k: int):
    """Embed + hybrid-retrieve. Returns (context_str, sources_list)."""
    import time as _time

    enriched = enrich_query(query)

    t0 = _time.perf_counter()
    embedding = embed_query(enriched.embed_text)
    t_embed_ms = (_time.perf_counter() - t0) * 1000

    t1 = _time.perf_counter()
    result = retrieve(
        query=query,
        query_embedding=embedding,
        top_k=top_k,
        fts_query=enriched.fts_text,
    )
    t_retrieve_ms = (_time.perf_counter() - t1) * 1000

    logger.info(
        "Retrieval: embed=%.0fms, supabase=%.0fms, hits=%d, query=%r",
        t_embed_ms,
        t_retrieve_ms,
        len(result.results),
        query[:80],
    )

    if not result.results:
        return None, []
    context = build_context(result.results)
    sources = [
        {
            "file_name": chunk.file_name,
            "page_no": chunk.chunk_page_no,
            "score": chunk.score,
        }
        for chunk in result.results
    ]
    return context, sources


def _stream_assistant_response(prompt_to_answer: str, top_k: int) -> str:
    """Render a live streaming assistant bubble.

    Returns the final assistant message (answer + sources HTML) that should
    be appended to the chat history.
    """
    from app.ui.components import _TYPING_INDICATOR_HTML  # local to avoid cycles

    left, _right = st.columns([9.5, 2.5], gap="small")
    with left:
        st.markdown("<div class='assistant-wrap'>", unsafe_allow_html=True)
        with st.chat_message("assistant", avatar=AGENT_AVATAR_URL):
            status_slot = st.empty()
            status_slot.markdown(_TYPING_INDICATOR_HTML, unsafe_allow_html=True)

            try:
                context, sources = _retrieve_context(prompt_to_answer, top_k)
            except Exception:
                logger.exception(
                    "Retrieval hatası: query=%r", prompt_to_answer
                )
                status_slot.markdown(ERROR_MESSAGE)
                st.markdown("</div>", unsafe_allow_html=True)
                return ERROR_MESSAGE

            if context is None:
                msg = "Bu konuda elimdeki belgelerde bilgi bulunamadı."
                status_slot.markdown(msg)
                st.markdown("</div>", unsafe_allow_html=True)
                return msg

            try:
                # Pass last few turns (excluding the just-pushed user message)
                # so the LLM can resolve references like "ona", "peki", "onun"
                # to the previous topic.
                history_for_llm = [
                    m for m in st.session_state.messages[:-1]
                    if not m.get("is_loading") and m.get("content")
                ]
                stream_iter = generate_answer_stream(
                    prompt_to_answer, context, chat_history=history_for_llm
                )

                # Keep the typing indicator visible until the FIRST token
                # actually arrives from the LLM — otherwise the assistant
                # bubble appears empty during the model's "time-to-first-token"
                # (~500ms-1s of round-trip latency).
                def _stream_with_indicator_swap():
                    first = True
                    for chunk in stream_iter:
                        if first:
                            status_slot.empty()
                            first = False
                        yield chunk
                    if first:
                        # No chunks at all — clear the indicator anyway
                        status_slot.empty()

                answer_text = st.write_stream(_stream_with_indicator_swap())
            except Exception:
                logger.exception(
                    "LLM streaming hatası: query=%r", prompt_to_answer
                )
                status_slot.markdown(ERROR_MESSAGE)
                st.markdown("</div>", unsafe_allow_html=True)
                return ERROR_MESSAGE

            if not isinstance(answer_text, str):
                answer_text = "".join(answer_text) if answer_text else ""

            sources_html = format_sources_markdown(sources)
            if sources_html:
                st.markdown(sources_html, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    return f"{answer_text}\n{sources_html}" if sources_html else answer_text


def main() -> None:
    _init_session_state()

    if render_sidebar():
        _reset_chat()

    render_topbar()
    render_chat_header()
    top_k = settings_top_k()

    chip_question = render_suggestion_chips()
    if chip_question:
        st.session_state.pending_chip_question = chip_question

    render_chat_messages(st.session_state.messages)

    if st.session_state.is_generating and st.session_state.pending_prompt:
        prompt_to_answer = st.session_state.pending_prompt
        final_message = _stream_assistant_response(prompt_to_answer, top_k)
        st.session_state.messages.append(
            {"role": "assistant", "content": final_message}
        )
        st.session_state.pending_prompt = None
        st.session_state.is_generating = False
        # Force a clean rerun so the live streaming bubble is replaced by the
        # history-rendered version. Without this, Streamlit can keep the live
        # bubble in the DOM, producing a visual duplicate next to the
        # history-rendered message on the following rerun.
        st.rerun()

    user_input = render_chat_input(disabled=st.session_state.is_generating)
    prompt = st.session_state.pending_chip_question or user_input

    if not prompt:
        return

    st.session_state.pending_chip_question = None
    prompt = prompt.strip()
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.pending_prompt = prompt
    st.session_state.is_generating = True
    st.rerun()


def settings_top_k() -> int:
    """Resolve top_k from settings module (single source of truth)."""
    from app.config import settings
    return settings.DEFAULT_TOP_K


if __name__ == "__main__":
    main()
