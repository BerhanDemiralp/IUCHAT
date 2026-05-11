"""Gemini LLM service — generates answers from retrieved context."""

from __future__ import annotations

import re
from typing import Iterator, Sequence

import streamlit as st
import google.generativeai as genai

from app.config import settings
from app.models import ChunkResult

# How many of the most recent user/assistant turns are passed to the LLM as
# conversational context. Each "turn" = one user message + the following
# assistant message, so MAX_HISTORY_TURNS=3 means up to 6 messages.
MAX_HISTORY_TURNS = 3


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


_SOURCE_CHIP_RE = re.compile(r"<a[^>]*class=['\"]source-chip['\"][^>]*>.*?</a>", re.DOTALL)
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _clean_assistant_content(content: str) -> str:
    """Strip source-chip HTML so the LLM only sees the natural answer text."""
    if not content:
        return ""
    cleaned = _SOURCE_CHIP_RE.sub("", content)
    cleaned = _HTML_TAG_RE.sub("", cleaned)
    return cleaned.strip()


def _format_history(history: Sequence[dict] | None) -> str:
    """Format recent chat history as a compact transcript for the prompt.

    Skips welcome / loading / error sentinel messages. Caps to the last
    ``MAX_HISTORY_TURNS`` user+assistant pairs.
    """
    if not history:
        return ""

    pairs: list[tuple[str, str]] = []
    pending_user: str | None = None

    for msg in history:
        role = msg.get("role")
        content = (msg.get("content") or "").strip()
        if not content or msg.get("is_loading"):
            continue
        if role == "user":
            pending_user = content
        elif role == "assistant" and pending_user is not None:
            pairs.append((pending_user, _clean_assistant_content(content)))
            pending_user = None

    if not pairs:
        return ""

    pairs = pairs[-MAX_HISTORY_TURNS:]
    lines: list[str] = []
    for user_msg, asst_msg in pairs:
        lines.append(f"Kullanıcı: {user_msg}")
        if asst_msg:
            lines.append(f"Asistan: {asst_msg}")
    return "\n".join(lines)


def _build_prompt(query: str, context: str, history_text: str = "") -> str:
    """Compose the full prompt sent to Gemini."""
    history_block = (
        f"\n# ÖNCEKİ KONUŞMA (bağlam için)\n"
        f"{history_text}\n\n"
        f"Yeni soruyu yorumlarken yukarıdaki bağlamı kullan. \"Ona\", \"onun\", \"peki\","
        f" \"bu konuda\" gibi referansları önceki konu üzerinden çöz.\n"
    ) if history_text else ""

    return f"""{history_block}# ROL
Sen "İÜC Asistan"sın — İstanbul Üniversitesi-Cerrahpaşa'nın resmi belgelerine dayanan
bir yapay zeka asistanısın. Hedef kitlen aday öğrenciler, kayıtlı öğrenciler, mezunlar
ve akademik/idari personeldir.

# AMAÇ
Kullanıcının sorusunu, aşağıdaki "KAYNAK METİNLER" bölümünde verilen üniversite
dokümanlarına (yönetmelikler, yönergeler, senato kararları, akademik takvim,
fakülte/bölüm bilgileri, idari prosedürler, başvuru formları vb.) dayanarak
**doğru, kısa ve uygulanabilir** bir biçimde yanıtla.

# CEVAP YAZIM KURALLARI
1. **Sadece verilen kaynaklardaki** bilgileri kullan; kaynak dışı varsayım, tahmin
   veya genel bilgi ekleme.
2. Cevabı **Türkçe**, açık ve resmi bir dille yaz; ama gerektiğinde sıcak ve
   yardımsever bir tonu koru. "Sen" diliyle hitap et.
3. **Kısa ve öz** ol. Gereksiz tekrarlardan, dolgu cümlelerden ve aşırı resmi
   bürokratik dilden kaçın. Cümleler net ve doğrudan olsun.
4. Soruya uygun olduğunda bilgiyi **markdown** ile yapılandır:
   - Adım adım süreçler için **numaralı liste** kullan (1., 2., 3.)
   - Birbirinden bağımsız maddeler için **kısa madde işaretli liste** kullan
   - Önemli koşulları/şartları **kalın** yaz (`**...**`)
   - Çok kısa, tek cümlelik cevaplarda liste kullanma
5. Tarih, süre, sayı, oran, GANO/AGNO eşik değerleri, başvuru aralıkları ve
   benzeri **somut bilgileri olduğu gibi koru**, yuvarlama veya değiştirme.
6. Birden fazla kaynak parçası ilgiliyse hepsinden faydalan; çelişen bilgi varsa
   en güncel/kapsamlı olanı tercih et ve diğerini sessizce göz ardı et.
7. Cevabın içine **kaynak, dosya adı, sayfa numarası, "Kaynak:", "Kaynaklar:",
   "[Kaynak 1]" gibi ifadeleri YAZMA**. Kaynaklar arayüzde otomatik olarak ayrı
   gösteriliyor.

# BİLGİ EKSİKLİĞİ DURUMU
- Soruyla doğrudan ilgili bilgi kaynaklarda **kısmen** varsa: önce mevcut bilgiyi
  ver, ardından kısa bir cümleyle "Detaylı/güncel bilgi için ilgili fakülte
  sekreterliği veya Öğrenci İşleri Daire Başkanlığı ile iletişime geçebilirsin."
  şeklinde yönlendir.
- Soruyla ilgili **hiçbir** bilgi kaynaklarda yoksa: tek cümleyle
  "Bu konuda elimdeki belgelerde bilgi bulunamadı; resmi kanallar üzerinden
  öğrenmen daha doğru olacaktır." de. Uydurma bilgi verme.

# KAPSAM DIŞI / SOHBET DURUMU
- Selamlaşma, teşekkür gibi kısa sohbet mesajlarında kuralları katı uygulama;
  kibar ve samimi bir cümleyle karşılık ver, ardından nasıl yardımcı
  olabileceğini sor.
- Üniversite ile ilgisiz konularda (genel kültür, hava durumu, kişisel görüş,
  vb.) kibarca İÜC kapsamında olmadığını belirt ve örnek konular öner
  (akademik takvim, öğrenci belgesi, yatay geçiş, mezuniyet, Erasmus, ders
  programı vb.).
- **Asla** kişisel görüş bildirme, siyasi/dini yorum yapma, hukuki tavsiye
  verme. Mevzuata dayalı bilgi aktarımıyla sınırlı kal.

# KAYNAK METİNLER
{context}

# KULLANICI SORUSU
{query}

# YANIT
"""


def generate_answer(
    query: str,
    context: str,
    chat_history: Sequence[dict] | None = None,
) -> str:
    """Send query + context (+ recent history) to Gemini and return the full answer."""
    model = _get_model()
    prompt = _build_prompt(query, context, _format_history(chat_history))
    response = model.generate_content(prompt)
    return response.text


def generate_answer_stream(
    query: str,
    context: str,
    chat_history: Sequence[dict] | None = None,
) -> Iterator[str]:
    """Stream Gemini's answer token by token.

    Yields incremental text chunks suitable for ``st.write_stream``. Empty
    chunks are filtered. Callers can ``"".join(...)`` the iterator to obtain
    the full final text.
    """
    model = _get_model()
    prompt = _build_prompt(query, context, _format_history(chat_history))
    response = model.generate_content(prompt, stream=True)
    for chunk in response:
        try:
            text = chunk.text
        except (AttributeError, ValueError):
            text = ""
        if text:
            yield text
