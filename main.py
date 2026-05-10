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
from app.services.llm import build_context, generate_answer


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


def _run_rag(query: str, top_k: int) -> tuple[str, list[dict[str, str | float | int | None]]]:
    """Execute embedding, retrieval, and answer generation."""
    embedding = embed_query(query)
    result = retrieve(query=query, query_embedding=embedding, top_k=top_k)

    if not result.results:
        return "Bu konuda kaynaklarda bilgi bulunamadı.", []

    context = build_context(result.results)
    answer = generate_answer(query, context)

    sources = [
        {
            "file_name": chunk.file_name,
            "page_no": chunk.chunk_page_no,
            "score": chunk.score,
        }
        for chunk in result.results
    ]
    return answer, sources


def main() -> None:
    _init_session_state()

    if render_sidebar():
        _reset_chat()

    render_topbar()
    render_chat_header()
    top_k = 10

    chip_question = render_suggestion_chips()
    if chip_question:
        st.session_state.pending_chip_question = chip_question

    render_chat_messages(st.session_state.messages)

    if st.session_state.is_generating and st.session_state.pending_prompt:
        prompt_to_answer = st.session_state.pending_prompt
        try:
            answer, sources = _run_rag(prompt_to_answer, top_k)
            answer_with_sources = f"{answer}\n{format_sources_markdown(sources)}"
        except Exception:
            logger.exception(
                "RAG akışı sırasında beklenmeyen hata: query=%r", prompt_to_answer
            )
            answer_with_sources = ERROR_MESSAGE

        if (
            st.session_state.messages
            and st.session_state.messages[-1].get("is_loading")
        ):
            st.session_state.messages[-1] = {
                "role": "assistant",
                "content": answer_with_sources,
            }
        else:
            st.session_state.messages.append(
                {"role": "assistant", "content": answer_with_sources}
            )
        st.session_state.pending_prompt = None
        st.session_state.is_generating = False
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
    st.session_state.messages.append(
        {"role": "assistant", "content": "", "is_loading": True}
    )
    st.session_state.pending_prompt = prompt
    st.session_state.is_generating = True
    st.rerun()


if __name__ == "__main__":
    main()
