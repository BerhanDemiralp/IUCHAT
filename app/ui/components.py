"""Streamlit UI components for chat-first layout."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import streamlit as st

SUGGESTION_QUESTIONS: list[tuple[str, str]] = [
    (":material/badge:", "Öğrenci kimlik kartı nasıl yenilenir?"),
    (":material/description:", "Öğrenci belgesi nasıl alınır?"),
    (":material/swap_horiz:", "Yatay geçiş başvuru şartları nelerdir?"),
    (":material/school:", "Mezuniyet şartları nelerdir?"),
    (":material/public:", "Erasmus başvurusu nasıl yapılır?"),
    (":material/menu_book:", "Ders programına nereden ulaşabilirim?"),
]

SIDEBAR_LOGO_URL = "https://cdn.iuc.edu.tr/FileHandler.ashx?f=EjTkziuNjkCBTfsgvG7zLg"
TOPBAR_LOGO_URL = "https://cdn.iuc.edu.tr/FileHandler.ashx?f=jbN9bVMs6EqJJoGn33Ie1A"
HERO_LOGO_URL = "https://cdn.iuc.edu.tr/FileHandler.ashx?f=EjTkziuNjkCBTfsgvG7zLg"
AGENT_AVATAR_URL = "https://cdn.iuc.edu.tr/FileHandler.ashx?f=EjTkziuNjkCBTfsgvG7zLg"

SIDEBAR_SILHOUETTE_CANDIDATES = [
    Path(__file__).resolve().parent / "assets" / "siluet.png",
    Path(__file__).resolve().parent / "assets" / "siluet.jpeg",
]


def _silhouette_data_uri() -> str | None:
    """Return base64 data URI for the sidebar silhouette image, if present."""
    for path in SIDEBAR_SILHOUETTE_CANDIDATES:
        if path.exists():
            mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
            encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
            return f"data:{mime};base64,{encoded}"
    return None


def page_config() -> None:
    """Set global Streamlit page config (call once at top of main)."""
    st.set_page_config(
        page_title="IUCHAT",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_sidebar_silhouette() -> None:
    """Inject the silhouette image as the sidebar's bottom background."""
    uri = _silhouette_data_uri()
    if not uri:
        return
    st.markdown(
        f"""
        <style>
          [data-testid="stSidebar"] {{
            --sidebar-silhouette: url('{uri}');
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_styles() -> None:
    """Apply custom CSS for screenshot-like chat layout."""
    st.markdown(
        """
        <style>
          .stApp { background: #FFFFFF; }
          .block-container {
            padding-top: 1.2rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
            max-width: 1080px !important;
          }
          [data-testid="stBottom"] > div,
          [data-testid="stBottomBlockContainer"] {
            max-width: 1080px !important;
            margin-left: auto !important;
            margin-right: auto !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
          }
          header[data-testid="stHeader"] {
            background: transparent !important;
            border: none !important;
          }
          [data-testid="stToolbar"] {
            visibility: visible !important;
            display: block !important;
            position: static !important;
            top: auto !important;
            right: auto !important;
            z-index: auto !important;
          }
          [data-testid="stDecoration"] { display: none !important; }
          [data-testid="stSidebar"] {
            background-color: #011534;
            background-image: var(--sidebar-silhouette, none);
            background-repeat: no-repeat;
            background-position: left bottom;
            background-size: 100% auto;
            border-right: 1px solid rgba(255,255,255,0.10);
            width: 280px !important;
            min-width: 280px !important;
            max-width: 280px !important;
            flex-shrink: 0 !important;
            resize: none !important;
          }
          [data-testid="stSidebarResizeHandle"],
          [data-testid="stSidebar"] [data-testid="stSidebarResizeHandle"],
          [data-testid="stSidebar"] [data-testid="stSidebarResizer"],
          [data-testid="stSidebar"] [class*="resizeHandle"],
          [data-testid="stSidebar"] [class*="ResizeHandle"] {
            display: none !important;
            pointer-events: none !important;
            width: 0 !important;
          }
          [data-testid="stSidebar"] * { color: #FFFFFF !important; }
          [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
            background: #D6A62A !important;
            color: #011534 !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
          }
          [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"]:hover {
            background: #C4931F !important;
          }
          [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] [data-testid="stIconMaterial"],
          [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] span[data-testid="stIconMaterial"] {
            color: #FFFFFF !important;
            fill: #FFFFFF !important;
          }
          .sidebar-title {
            font-size: 1.35rem;
            font-weight: 700;
            margin: .35rem 0 1.2rem 0;
            text-align: center;
          }
          .menu-item {
            padding: 8px 0;
            opacity: 0.95;
            font-size: 0.95rem;
          }
          .menu-link {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 12px;
            margin: 6px 0;
            border-radius: 10px;
            color: #FFFFFF !important;
            text-decoration: none !important;
            font-size: 0.95rem;
            font-weight: 500;
            transition: background 0.15s ease, transform 0.15s ease;
          }
          .menu-link:hover {
            background: rgba(214, 166, 42, 0.12);
            transform: translateX(2px);
          }
          .menu-link .menu-icon {
            width: 20px;
            height: 20px;
            color: #D6A62A;
            flex-shrink: 0;
          }
          .menu-link span {
            color: #FFFFFF !important;
          }
          .social-row {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;
            margin: 14px 6px 6px 6px;
            padding-top: 14px;
            border-top: 1px solid rgba(255,255,255,0.12);
          }
          .social-link {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 38px;
            height: 38px;
            border-radius: 50%;
            border: 1px solid rgba(214, 166, 42, 0.45);
            color: #D6A62A !important;
            transition: background 0.18s ease, transform 0.18s ease, border-color 0.18s ease;
            text-decoration: none !important;
          }
          .social-link svg {
            width: 18px;
            height: 18px;
          }
          .social-link:hover {
            background: rgba(214, 166, 42, 0.18);
            border-color: #D6A62A;
            transform: translateY(-1px);
          }
          .sidebar-logo-wrap {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 14px;
            padding-top: 6px;
            width: 100%;
            text-align: center;
          }
          .sidebar-logo-wrap img {
            display: block;
            margin: 0 auto;
          }
          .hero-card {
            border: none;
            border-radius: 14px;
            padding: 16px 8px 24px 8px;
            background: transparent;
            margin-bottom: 10px;
          }
          .topbar-wrap {
            width: 100%;
            box-sizing: border-box;
            margin-bottom: 14px;
          }
          .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
            box-sizing: border-box;
            border: 1px solid #D8DEE8;
            border-radius: 14px;
            padding: 8px 16px;
            background: #FFFFFF;
          }
          .topbar-title { margin-left: 0; padding-left: 0; }
          .topbar-help { margin-right: 0; }
          .topbar-title {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 700;
            color: #14213D;
          }
          .topbar-help {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #14213D !important;
            font-size: 0.9rem;
            font-weight: 600;
            padding: 6px 14px;
            border-radius: 999px;
            border: 1px solid #D8DEE8;
            text-decoration: none !important;
            transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
          }
          .topbar-help svg {
            width: 16px;
            height: 16px;
            color: #D6A62A;
          }
          .topbar-help:hover {
            background: #FFF8E1;
            border-color: #D6A62A;
          }
          .hero-center {
            display: flex;
            align-items: center;
            flex-direction: column;
            text-align: center;
            margin-bottom: 8px;
          }
          .chip-title {
            font-size: 0.9rem;
            color: #7B8798;
            margin: 8px 0 6px 0;
          }
          div.stButton > button[kind="secondary"] {
            border-radius: 999px;
            border: 1px solid #D8DEE8;
            background: #FFFFFF;
            color: #14213D;
            font-size: 0.88rem;
            min-height: 2.3rem;
            box-shadow: 0 4px 14px rgba(7, 27, 58, 0.06);
            transition: box-shadow 0.18s ease, transform 0.18s ease, border-color 0.18s ease;
          }
          div.stButton > button[kind="secondary"]:hover {
            border-color: #D6A62A;
            background: #FFF8E1;
            box-shadow: 0 6px 18px rgba(214, 166, 42, 0.18);
            transform: translateY(-1px);
          }
          div.stButton > button[kind="secondary"] [data-testid="stIconMaterial"],
          div.stButton > button[kind="secondary"] span[data-testid="stIconMaterial"] {
            color: #D6A62A !important;
            fill: #D6A62A !important;
            font-size: 1.1rem !important;
            margin-right: 4px;
          }
          div.stButton > button[kind="secondary"]:hover [data-testid="stIconMaterial"],
          div.stButton > button[kind="secondary"]:hover span[data-testid="stIconMaterial"] {
            color: #C4931F !important;
            fill: #C4931F !important;
          }
          .source-list {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #D8DEE8;
            font-size: 0.9rem;
          }
          [data-testid="stChatMessage"] {
            background: transparent;
            border: none;
            padding: 2px 0;
          }
          [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
            border-radius: 14px;
            padding: 12px 14px;
            border: 1px solid #D8DEE8;
            color: #14213D !important;
            box-shadow: 0 4px 16px rgba(7, 27, 58, 0.06);
          }
          .assistant-wrap [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
            background: #FFFFFF;
          }
          [data-testid="stChatMessageAvatarAssistant"],
          [data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"] {
            border: 2px solid #D6A62A !important;
            border-radius: 50% !important;
            box-shadow: 0 2px 8px rgba(7, 27, 58, 0.18) !important;
            overflow: hidden !important;
          }
          [data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) [data-testid="stMarkdownContainer"] {
            background: #0B2A55;
            border-color: #0B2A55;
          }
          [data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) [data-testid="stMarkdownContainer"] * {
            color: #FFFFFF !important;
          }
          .user-row {
            display: flex;
            justify-content: flex-end;
            width: 100%;
            margin: 4px 0;
          }
          .user-bubble {
            background: #0B2A55;
            color: #FFFFFF;
            border-radius: 14px;
            padding: 12px 16px;
            font-size: 0.95rem;
            line-height: 1.55;
            border: 1px solid #0B2A55;
            box-shadow: 0 4px 16px rgba(7, 27, 58, 0.18);
            max-width: 100%;
            width: fit-content;
            display: inline-block;
            text-align: left;
            word-wrap: break-word;
          }
          .user-bubble * { color: #FFFFFF !important; }
          .typing-dots {
            display: inline-flex;
            gap: 4px;
            margin-left: 6px;
            vertical-align: middle;
          }
          .typing-dots span {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #D6A62A;
            animation: typing-bounce 1.2s infinite ease-in-out;
          }
          .typing-dots span:nth-child(2) { animation-delay: 0.15s; }
          .typing-dots span:nth-child(3) { animation-delay: 0.30s; }
          @keyframes typing-bounce {
            0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
            40%           { transform: translateY(-4px); opacity: 1; }
          }
          .source-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #D8DEE8;
          }
          .source-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #FFF8E1;
            border: 1px solid #F3D98B;
            color: #14213D;
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 0.82rem;
            line-height: 1.2;
            max-width: 100%;
          }
          .source-chip-icon { color: #C4931F; font-size: 0.8rem; }
          .source-chip-label {
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 220px;
          }
          .source-chip-meta { color: #7B8798; font-size: 0.75rem; }
          [data-testid="stChatMessage"] code {
            color: #0B2A55 !important;
            background: #F6F8FB;
            border-radius: 6px;
            padding: 2px 6px;
          }
          [data-testid="stChatInput"] {
            border-top: none;
          }
          [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            padding-bottom: 240px;
          }
          [data-testid="stChatInput"] > div {
            border: 1px solid #D8DEE8 !important;
            border-radius: 12px !important;
            box-shadow: none !important;
            transition: border-color 0.15s ease;
          }
          [data-testid="stChatInput"] > div:focus-within {
            border-color: #D6A62A !important;
            box-shadow: none !important;
          }
          [data-testid="stChatInput"] [data-baseweb="textarea"],
          [data-testid="stChatInput"] [data-baseweb="textarea"]:focus,
          [data-testid="stChatInput"] [data-baseweb="textarea"]:focus-within,
          [data-testid="stChatInput"] [data-baseweb="textarea"]:hover {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            background: transparent !important;
          }
          [data-testid="stChatInput"] [data-baseweb="textarea"] > div,
          [data-testid="stChatInput"] [data-baseweb="textarea"] > div:focus-within {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            background: transparent !important;
          }
          [data-testid="stChatInput"] textarea,
          [data-testid="stChatInput"] textarea:focus,
          [data-testid="stChatInput"] textarea:focus-visible,
          [data-testid="stChatInput"] textarea:hover {
            outline: none !important;
            box-shadow: none !important;
            border: none !important;
            background: transparent !important;
          }
          [data-testid="stChatInput"] button {
            background: #071B3A !important;
            color: #D6A62A !important;
            border: none !important;
            border-radius: 50% !important;
            width: 36px !important;
            height: 36px !important;
            min-width: 36px !important;
            padding: 0 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
          }
          [data-testid="stChatInput"] button:hover {
            background: #0B2A55 !important;
          }
          [data-testid="stChatInput"] button:disabled {
            background: #14213D !important;
            color: #7B8798 !important;
            opacity: 0.6 !important;
          }
          [data-testid="stChatInput"] button svg {
            color: #D6A62A !important;
            fill: #D6A62A !important;
          }
          [data-testid="stChatInput"] button:disabled svg {
            color: #7B8798 !important;
            fill: #7B8798 !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> bool:
    """Render native Streamlit sidebar and return True when new chat clicked."""
    with st.sidebar:
        if SIDEBAR_LOGO_URL:
            left_spacer, center_logo, right_spacer = st.columns([1, 2, 1])
            with center_logo:
                st.image(SIDEBAR_LOGO_URL, width=132)
        st.markdown('<div class="sidebar-title">IUChat</div>', unsafe_allow_html=True)
        new_chat = st.button(
            "Yeni Sohbet",
            type="primary",
            use_container_width=True,
            icon=":material/edit_square:",
        )
        st.markdown(
            """
            <a class="menu-link" href="https://www.iuc.edu.tr/tr/content/akademik/fakulteler" target="_blank" rel="noopener noreferrer">
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 10 12 4l9 6"/>
                <path d="M5 10v9h14v-9"/>
                <path d="M9 19v-5h6v5"/>
              </svg>
              <span>Fakülteler</span>
            </a>
            <a class="menu-link" href="https://iuc.edu.tr/tr/content/yonetim/rektor" target="_blank" rel="noopener noreferrer">
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="8" r="3.4"/>
                <path d="M5 20c1.4-3.4 4.2-5 7-5s5.6 1.6 7 5"/>
              </svg>
              <span>Yönetim</span>
            </a>
            <a class="menu-link" href="https://aksis.iuc.edu.tr/" target="_blank" rel="noopener noreferrer">
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <rect x="4" y="4" width="16" height="16" rx="2"/>
                <path d="M8 9h8"/>
                <path d="M8 13h8"/>
                <path d="M8 17h5"/>
              </svg>
              <span>AKSİS</span>
            </a>
            <a class="menu-link" href="https://sks.iuc.edu.tr/tr/yemeklistesi" target="_blank" rel="noopener noreferrer">
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 3v8a3 3 0 0 0 3 3v7"/>
                <path d="M11 3v8"/>
                <path d="M8 3v6"/>
                <path d="M17 3c-1.5 1.6-2.5 3.7-2.5 6.3 0 1.6.8 2.7 2.5 2.7v9"/>
              </svg>
              <span>Yemek Listesi</span>
            </a>
            <div class="social-row">
              <a class="social-link" href="https://www.instagram.com/iucerrahpasa/" target="_blank" rel="noopener noreferrer" aria-label="Instagram">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="5"/>
                  <circle cx="12" cy="12" r="4"/>
                  <circle cx="17.3" cy="6.7" r="0.6" fill="currentColor"/>
                </svg>
              </a>
              <a class="social-link" href="https://www.youtube.com/channel/UCYxPtgvy8y4NK4-j5JY0W0w/featured?view_as=subscriber" target="_blank" rel="noopener noreferrer" aria-label="YouTube">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="2.5" y="6" width="19" height="12" rx="3"/>
                  <path d="M10.5 9.5v5l4-2.5z" fill="currentColor" stroke="none"/>
                </svg>
              </a>
              <a class="social-link" href="https://x.com/iu_cerrahpasa" target="_blank" rel="noopener noreferrer" aria-label="X">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M4 4l16 16"/>
                  <path d="M20 4 4 20"/>
                </svg>
              </a>
            </div>
            """,
            unsafe_allow_html=True,
        )
    return new_chat


def render_topbar() -> None:
    """Render top strip similar to target screenshot."""
    if TOPBAR_LOGO_URL:
        title_html = (
            "<div class='topbar-title'>"
            f"<img src='{TOPBAR_LOGO_URL}' height='42'/>"
            "</div>"
        )
    else:
        title_html = "<div class='topbar-title'><span>🎓 IUChat</span></div>"

    contact_link = (
        "<a class='topbar-help' "
        "href='https://www.iuc.edu.tr/tr/content/universitemiz/iletisim#5600720031002D006C003800430045003800670038003100' "
        "target='_blank' rel='noopener noreferrer'>"
        "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
        "<path d='M4 5h6l1.5 4-2.5 1.5a11 11 0 0 0 4.5 4.5L15 12.5 19 14v6c0 .6-.4 1-1 1A15 15 0 0 1 3 6c0-.6.4-1 1-1Z'/>"
        "</svg>"
        "<span>İletişim</span>"
        "</a>"
    )
    st.markdown(
        f"<div class='topbar-wrap'><div class='topbar'>{title_html}{contact_link}</div></div>",
        unsafe_allow_html=True,
    )


def render_chat_header() -> None:
    """Render hero card at top of chat area."""
    logo_html = ""
    if HERO_LOGO_URL:
        logo_html = f"<img src='{HERO_LOGO_URL}' width='84'/>"

    st.markdown(
        f"""
        <div class="hero-card">
          <div class="hero-center">{logo_html}</div>
          <div class="hero-center" style="font-size:2rem; font-weight:700; color:#14213D;">Merhaba,</div>
          <div style="color:#4d596a; text-align:center; max-width: 720px; margin: 6px auto 0; line-height: 1.6; font-size: 0.98rem;">
            İstanbul Üniversitesi - Cerrahpaşa ile ilgili akademik takvim,
            öğrenci işleri, yönetmelikler, fakülteler, yatay/dikey geçiş, burs, yemekhane ve daha pek çok
            konuda sana resmi belgelere dayalı kısa ve net cevaplar verebilirim. Aşağıdaki örnek sorulardan
            başlayabilir veya kendi sorunu yazabilirsin.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_suggestion_chips() -> str | None:
    """Render suggestion buttons and return selected question."""
    st.markdown('<div class="chip-title">Önerilen sorular</div>', unsafe_allow_html=True)
    selected: str | None = None
    cols = st.columns(3)
    for idx, (icon, question) in enumerate(SUGGESTION_QUESTIONS):
        with cols[idx % 3]:
            if st.button(
                question,
                icon=icon,
                use_container_width=True,
                key=f"chip_{idx}",
                type="secondary",
            ):
                selected = question
    return selected


_TYPING_INDICATOR_HTML = (
    "<strong>Kaynaklar taranıyor</strong>"
    "<span class='typing-dots'><span></span><span></span><span></span></span>"
)


def render_chat_messages(messages: list[dict[str, Any]]) -> None:
    """Render chat history as Streamlit chat bubbles."""
    for message in messages:
        role = message.get("role", "assistant")
        if role == "assistant":
            left, right = st.columns([9.5, 2.5], gap="small")
            with left:
                st.markdown("<div class='assistant-wrap'>", unsafe_allow_html=True)
                with st.chat_message("assistant", avatar=AGENT_AVATAR_URL):
                    if message.get("is_loading"):
                        st.markdown(_TYPING_INDICATOR_HTML, unsafe_allow_html=True)
                    else:
                        st.markdown(message.get("content", ""), unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with right:
                st.empty()
        else:
            st.markdown(
                f"<div class='user-row'><div class='user-bubble'>{message.get('content', '')}</div></div>",
                unsafe_allow_html=True,
            )


def render_chat_input(disabled: bool = False) -> str | None:
    """Render chat input and return user text."""
    return st.chat_input("Sorunuzu yazın...", disabled=disabled)


def _prettify_source_name(file_name: str) -> str:
    """Convert raw file name to a friendly chip label."""
    base = file_name.rsplit(".", 1)[0]
    base = base.replace("_", " ").replace("-", " ").strip()
    return " ".join(word.capitalize() for word in base.split() if word) or file_name


def format_sources_markdown(sources: list[dict[str, Any]]) -> str:
    """Format retrieved sources as compact inline chips."""
    if not sources:
        return ""

    seen: set[str] = set()
    chips: list[str] = []
    for source in sources:
        file_name = str(source.get("file_name", "Kaynak"))
        if file_name in seen:
            continue
        seen.add(file_name)
        label = _prettify_source_name(file_name)
        page_no = source.get("page_no")
        meta = f"Sayfa {page_no}" if page_no not in (None, "", "?") else "Kaynak"
        chips.append(
            f"<span class='source-chip'>"
            f"<span class='source-chip-icon'>🔗</span>"
            f"<span class='source-chip-label'>{label}</span>"
            f"<span class='source-chip-meta'>{meta}</span>"
            f"</span>"
        )
        if len(chips) >= 3:
            break

    return (
        "<div class='source-row'>"
        + "".join(chips)
        + "</div>"
    )
