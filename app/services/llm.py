"""Gemini LLM service — generates answers from retrieved context."""

from __future__ import annotations

import streamlit as st
import google.generativeai as genai

from app.config import settings
from app.models import ChunkResult


@st.cache_resource(show_spinner="Connecting to Gemini…")
def _get_model():
    """Configure and return a cached Gemini model instance."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(settings.GEMINI_MODEL)


def build_context(chunks: list[ChunkResult]) -> str:
    """Format retrieved chunks into a context string for the LLM."""
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(
            f"[Kaynak {i}] (Dosya: {chunk.file_name}, Sayfa: {chunk.chunk_page_no or '?'}, "
            f"Benzerlik: {chunk.score * 100:.1f}%)\n{chunk.chunk_text}"
        )
    return "\n\n---\n\n".join(parts)


def generate_answer(query: str, context: str) -> str:
    """Send query + context to Gemini and return the answer."""
    model = _get_model()

    prompt = f"""Sen İstanbul Üniversitesi-Cerrahpaşa'nın resmi yapay zeka asistanısın. Üniversiteye ait tüm dokümanlardan (yönergeler, yönetmelikler, akademik bilgiler, idari prosedürler, vb.) derlenen kaynak metinleri kullanarak kullanıcının sorusunu yanıtla.

KURALLAR:
- Sadece verilen kaynaklardaki bilgileri kullan.
- Kaynaklarda soruyla ilgili bilgi yoksa "Bu konuda kaynaklarda bilgi bulunamadı." de.
- Yanıtını destekleyen kaynak(lar)ın hangisi olduğunu belirt (Dosya adı ve sayfa numarası).
- Kısa, net ve anlaşılır cevap ver.
- Birden fazla kaynak ilgiliyse hepsinden faydalan.
- Türkçe yanıt ver.

KAYNAK METİNLER:
{context}

KULLANICI SORUSU: {query}

YANIT:"""

    response = model.generate_content(prompt)
    return response.text
