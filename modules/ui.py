from __future__ import annotations

import html

import streamlit as st

from modules.constants import GUARD_TASK_STATUS_LABELS, REQUEST_STATUS_LABELS


THEME_OPTIONS = ("เช้า", "กลางคืน")

THEMES = {
    "เช้า": {
        "bg": "#FFFFFF",
        "surface": "#F8F5FF",
        "surface_2": "#F0E9FF",
        "surface_3": "#FFFFFF",
        "text": "#171021",
        "muted": "#695B7D",
        "border": "#DFD4F2",
        "primary": "#5B2AA0",
        "primary_hover": "#4A2188",
        "primary_soft": "#EFE7FF",
        "sidebar": "#FBF9FF",
        "input": "#FFFFFF",
        "shadow": "0 1px 2px rgba(63, 38, 100, 0.08)",
    },
    "กลางคืน": {
        "bg": "#110B1D",
        "surface": "#1B1230",
        "surface_2": "#26183E",
        "surface_3": "#160F26",
        "text": "#F7F2FF",
        "muted": "#CBBCE7",
        "border": "#3A2A57",
        "primary": "#B28CFF",
        "primary_hover": "#C7AAFF",
        "primary_soft": "#2D1F49",
        "sidebar": "#160E25",
        "input": "#211538",
        "shadow": "0 1px 2px rgba(0, 0, 0, 0.28)",
    },
}


def _theme_mode() -> str:
    if "nacc_theme_mode" not in st.session_state:
        st.session_state.nacc_theme_mode = THEME_OPTIONS[0]

    with st.sidebar:
        st.caption("ธีม")
        return st.radio(
            "เลือกธีม",
            THEME_OPTIONS,
            key="nacc_theme_mode",
            horizontal=True,
            label_visibility="collapsed",
        )


def inject_global_css() -> None:
    mode = _theme_mode()
    colors = THEMES.get(mode, THEMES["เช้า"])
    st.markdown(
        f"""
        <style>
        :root {
            --bg: {colors["bg"]};
            --surface: {colors["surface"]};
            --surface-2: {colors["surface_2"]};
            --surface-3: {colors["surface_3"]};
            --text: {colors["text"]};
            --muted: {colors["muted"]};
            --border: {colors["border"]};
            --primary: {colors["primary"]};
            --primary-hover: {colors["primary_hover"]};
            --primary-soft: {colors["primary_soft"]};
            --sidebar: {colors["sidebar"]};
            --input: {colors["input"]};
            --shadow: {colors["shadow"]};
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
            font-family: "Noto Sans Thai", "Sarabun", "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        h1, h2, h3 {
            color: var(--text);
            letter-spacing: 0;
        }

        p, label, span, div, .stMarkdown {
            color: var(--text);
        }

        a {
            color: var(--primary);
        }

        section[data-testid="stSidebar"] {
            background: var(--sidebar);
            border-right: 1px solid var(--border);
        }

        section[data-testid="stSidebar"] * {
            color: var(--text);
        }

        div[data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 14px;
            border-radius: 8px;
            box-shadow: var(--shadow);
        }

        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] div {
            color: var(--text);
        }

        .nacc-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 14px;
            box-shadow: var(--shadow);
        }

        .nacc-muted {
            color: var(--muted);
            font-size: 0.92rem;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 700;
            border: 1px solid transparent;
            white-space: nowrap;
        }

        .status-pending { background: #FFF7D6; color: #6B5600; }
        .status-active { background: #EAF2FF; color: #124B8A; }
        .status-in_progress { background: #EAF2FF; color: #124B8A; }
        .status-submitted { background: #F0EAFE; color: #4B267A; }
        .status-done { background: #E9F7EF; color: #146C2E; }
        .status-cancelled { background: #1F1F1F; color: #F2F2F2; }
        .status-draft { background: #F1F1F1; color: #333333; }

        div[data-testid="stForm"],
        div[data-testid="stExpander"],
        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {
            background: var(--surface-3);
            border-color: var(--border);
        }

        input, textarea,
        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"] {
            background: var(--input) !important;
            color: var(--text) !important;
            border-color: var(--border) !important;
        }

        input::placeholder,
        textarea::placeholder {
            color: var(--muted) !important;
            opacity: 1;
        }

        button[kind="primary"],
        div[data-testid="stFormSubmitButton"] button[kind="primary"] {
            background: var(--primary);
            border-color: var(--primary);
            color: #FFFFFF;
        }

        button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
            background: var(--primary-hover);
            border-color: var(--primary-hover);
            color: #FFFFFF;
        }

        button[kind="secondary"] {
            background: var(--surface-3);
            border-color: var(--border);
            color: var(--text);
        }

        button[kind="secondary"]:hover {
            border-color: var(--primary);
            color: var(--primary);
        }

        div[role="radiogroup"] label {
            background: var(--surface-3);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 4px 8px;
        }

        hr {
            border-color: var(--border);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_title(title: str, subtitle: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.markdown(f'<div class="nacc-muted">{html.escape(subtitle)}</div>', unsafe_allow_html=True)


def status_badge(status: str, kind: str = "request") -> str:
    clean_status = str(status or "").strip() or "pending"
    labels = GUARD_TASK_STATUS_LABELS if kind == "guard" else REQUEST_STATUS_LABELS
    label = labels.get(clean_status, clean_status)
    return f'<span class="status-badge status-{html.escape(clean_status)}">{html.escape(label)}</span>'


def render_status(status: str, kind: str = "request") -> None:
    st.markdown(status_badge(status, kind), unsafe_allow_html=True)


def metric_card(label: str, value, caption: str | None = None) -> None:
    st.metric(label=label, value=value, help=caption)


def section_card(title: str, body: str | None = None) -> None:
    content = f"<strong>{html.escape(title)}</strong>"
    if body:
        content += f'<div class="nacc-muted">{html.escape(body)}</div>'
    st.markdown(f'<div class="nacc-card">{content}</div>', unsafe_allow_html=True)
