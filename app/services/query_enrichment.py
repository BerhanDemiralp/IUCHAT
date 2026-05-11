"""Lightweight query enrichment for Turkish university-domain search.

Two outputs are produced from a raw user query:

1. ``embed_text`` — text used to compute the embedding vector. Abbreviations
   are expanded so the semantic search benefits from richer context.
2. ``fts_text``   — text passed to Postgres' ``websearch_to_tsquery``. Both
   the original tokens AND the expansions are kept so the FTS path catches
   either form (e.g. user writes "AGNO" but the document uses "ağırlıklı
   genel not ortalaması").

The enrichment is intentionally light: a curated dictionary of common
Turkish higher-ed abbreviations + minor casing/whitespace normalisation.
There is no heavy NLP, so this adds essentially zero latency.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

ABBREVIATIONS: dict[str, tuple[str, ...]] = {
    # Akademik ortalama
    "agno": ("ağırlıklı genel not ortalaması", "genel not ortalaması"),
    "gano": ("genel ağırlıklı not ortalaması", "genel not ortalaması"),
    "ano": ("akademik not ortalaması",),
    # Kredi sistemleri
    "akts": ("Avrupa Kredi Transfer Sistemi", "ECTS"),
    "ects": ("AKTS", "Avrupa Kredi Transfer Sistemi"),
    # Sınavlar
    "ösym": ("Ölçme Seçme ve Yerleştirme Merkezi",),
    "osym": ("Ölçme Seçme ve Yerleştirme Merkezi",),
    "yks": ("Yükseköğretim Kurumları Sınavı",),
    "tyt": ("Temel Yeterlilik Testi",),
    "ayt": ("Alan Yeterlilik Testi",),
    "dgs": ("Dikey Geçiş Sınavı",),
    "yds": ("Yabancı Dil Sınavı",),
    "yökdil": ("Yükseköğretim Kurulu Yabancı Dil Sınavı",),
    "yokdil": ("Yükseköğretim Kurulu Yabancı Dil Sınavı",),
    # Kurumlar / sistemler
    "yök": ("Yükseköğretim Kurulu",),
    "yok": ("Yükseköğretim Kurulu",),
    "obis": ("öğrenci bilgi sistemi",),
    "öbis": ("öğrenci bilgi sistemi",),
    "aksis": ("akademik sistem",),
    "sks": ("sağlık kültür ve spor",),
    "öidb": ("Öğrenci İşleri Daire Başkanlığı",),
    "oidb": ("Öğrenci İşleri Daire Başkanlığı",),
    "iuc": ("İstanbul Üniversitesi-Cerrahpaşa",),
    "iüc": ("İstanbul Üniversitesi-Cerrahpaşa",),
    "iü": ("İstanbul Üniversitesi",),
    # Mali / burs
    "kyk": ("Kredi ve Yurtlar Kurumu", "Gençlik ve Spor Bakanlığı"),
    # Erasmus / değişim
    "erasmus+": ("Erasmus", "Erasmus Plus", "değişim programı"),
    # Diğer
    "ab": ("Avrupa Birliği",),
}


@dataclass(frozen=True)
class EnrichedQuery:
    """Container for the two enriched representations of a user query."""

    original: str
    embed_text: str
    fts_text: str

    def __str__(self) -> str:
        return self.original


def _normalize_token(tok: str) -> str:
    """Lowercase + strip surrounding punctuation, but keep Turkish chars intact."""
    return tok.strip(".,;:!?()[]{}\"'`").lower()


def _ascii_fold(text: str) -> str:
    """ASCII-fold for case-insensitive matching of mixed forms (yök vs yok)."""
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
    )


def enrich_query(query: str) -> EnrichedQuery:
    """Expand abbreviations and produce embed / FTS variants.

    Empty / whitespace queries are returned unchanged.
    """
    if not query or not query.strip():
        return EnrichedQuery(original=query, embed_text=query, fts_text=query)

    tokens = re.findall(r"\S+", query)
    expansions: list[str] = []
    seen_expansions: set[str] = set()

    for raw in tokens:
        key = _normalize_token(raw)
        if not key:
            continue
        candidates: tuple[str, ...] = ABBREVIATIONS.get(key, ())
        if not candidates:
            # try ascii-folded variant (e.g. "ÖSYM" -> "osym")
            candidates = ABBREVIATIONS.get(_ascii_fold(key), ())
        for exp in candidates:
            if exp.lower() not in seen_expansions:
                expansions.append(exp)
                seen_expansions.add(exp.lower())

    if not expansions:
        return EnrichedQuery(original=query, embed_text=query, fts_text=query)

    # For embeddings: append expansions in natural language so the encoder
    # picks up the additional semantic context without distorting the query.
    embed_text = f"{query} ({'; '.join(expansions)})"

    # For FTS we want both original tokens and the expansion words available
    # for the lexer; simple concatenation is enough since websearch_to_tsquery
    # tokenises and stems them itself.
    fts_text = f"{query} {' '.join(expansions)}"

    return EnrichedQuery(original=query, embed_text=embed_text, fts_text=fts_text)
