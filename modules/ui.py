from __future__ import annotations

import html

import streamlit as st

from modules.constants import GUARD_TASK_STATUS_LABELS, REQUEST_STATUS_LABELS


THEME_OPTIONS = ("เช้า", "กลางคืน")
THEME_QUERY_VALUES = {"day": "เช้า", "light": "เช้า", "night": "กลางคืน", "dark": "กลางคืน"}
THEME_QUERY_KEYS = {"เช้า": "day", "กลางคืน": "night"}

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
    query_theme = st.query_params.get("theme", "")
    if isinstance(query_theme, list):
        query_theme = query_theme[0] if query_theme else ""

    mode = THEME_QUERY_VALUES.get(str(query_theme).lower(), st.session_state.get("nacc_theme_mode", THEME_OPTIONS[0]))
    st.session_state.nacc_theme_mode = mode

    day_active = " is-active" if mode == "เช้า" else ""
    night_active = " is-active" if mode == "กลางคืน" else ""
    st.markdown(
        f"""
        <nav class="theme-switcher" aria-label="เลือกธีม">
            <a class="theme-icon-button{day_active}" href="?theme={THEME_QUERY_KEYS["เช้า"]}" title="ธีมเช้า" aria-label="ธีมเช้า">☀</a>
            <a class="theme-icon-button{night_active}" href="?theme={THEME_QUERY_KEYS["กลางคืน"]}" title="ธีมกลางคืน" aria-label="ธีมกลางคืน">☾</a>
        </nav>
        """,
        unsafe_allow_html=True,
    )
    return mode


def inject_global_css() -> None:
    mode = _theme_mode()
    colors = THEMES.get(mode, THEMES["เช้า"])
    css = """
        <style>
        :root {
            --bg: __BG__;
            --surface: __SURFACE__;
            --surface-2: __SURFACE_2__;
            --surface-3: __SURFACE_3__;
            --text: __TEXT__;
            --muted: __MUTED__;
            --border: __BORDER__;
            --primary: __PRIMARY__;
            --primary-hover: __PRIMARY_HOVER__;
            --primary-soft: __PRIMARY_SOFT__;
            --sidebar: __SIDEBAR__;
            --input: __INPUT__;
            --shadow: __SHADOW__;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
            font-family: "Noto Sans Thai", "Sarabun", "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .theme-switcher {
            position: fixed;
            top: 14px;
            right: 88px;
            z-index: 100000;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px;
            background: var(--surface-3);
            border: 1px solid var(--border);
            border-radius: 999px;
            box-shadow: var(--shadow);
        }

        .theme-icon-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            border-radius: 999px;
            color: var(--muted) !important;
            text-decoration: none !important;
            font-size: 18px;
            font-weight: 800;
            line-height: 1;
            border: 1px solid transparent;
            transition: background 120ms ease, color 120ms ease, border-color 120ms ease;
        }

        .theme-icon-button:hover,
        .theme-icon-button.is-active {
            background: var(--primary);
            color: #FFFFFF !important;
            border-color: var(--primary);
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

        .stApp,
        div[data-testid="stAppViewContainer"],
        div[data-testid="stMain"],
        main,
        section.main,
        header[data-testid="stHeader"],
        div[data-testid="stHeader"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"] {
            background: var(--bg) !important;
            color: var(--text) !important;
        }

        header[data-testid="stHeader"] *,
        div[data-testid="stToolbar"] *,
        div[data-testid="stDecoration"] * {
            color: var(--text) !important;
            fill: var(--text) !important;
        }

        section[data-testid="stSidebar"] {
            background: var(--sidebar);
            border-right: 1px solid var(--border);
        }

        section[data-testid="stSidebar"] * {
            color: var(--text);
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
        section[data-testid="stSidebar"] a {
            color: var(--text) !important;
            border-radius: 8px;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: var(--primary-soft) !important;
            color: var(--primary) !important;
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

        div[data-testid="stMetricValue"],
        div[data-testid="stMetricLabel"] {
            color: var(--text) !important;
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
        div[data-testid="stTable"],
        div[data-testid="stAlert"],
        div[data-testid="stTabs"],
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--surface-3) !important;
            border-color: var(--border) !important;
            color: var(--text) !important;
        }

        input, textarea,
        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"],
        div[data-baseweb="input"] {
            background: var(--input) !important;
            color: var(--text) !important;
            border-color: var(--border) !important;
        }

        input,
        textarea,
        div[data-baseweb="select"] *,
        div[data-baseweb="base-input"] *,
        div[data-baseweb="input"] * {
            color: var(--text) !important;
            fill: var(--text) !important;
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

        code {
            background: var(--primary-soft) !important;
            color: var(--primary) !important;
            border: 1px solid var(--border);
            border-radius: 6px;
        }

        [data-testid="stDataFrame"] *,
        [data-testid="stTable"] *,
        [data-testid="stElementToolbar"] * {
            color: var(--text) !important;
        }

        hr {
            border-color: var(--border);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        @media (max-width: 760px) {
            .theme-switcher {
                top: 12px;
                right: 54px;
            }

            .theme-icon-button {
                width: 30px;
                height: 30px;
                font-size: 17px;
            }
        }
        </style>
        """
    replacements = {
        "__BG__": colors["bg"],
        "__SURFACE__": colors["surface"],
        "__SURFACE_2__": colors["surface_2"],
        "__SURFACE_3__": colors["surface_3"],
        "__TEXT__": colors["text"],
        "__MUTED__": colors["muted"],
        "__BORDER__": colors["border"],
        "__PRIMARY__": colors["primary"],
        "__PRIMARY_HOVER__": colors["primary_hover"],
        "__PRIMARY_SOFT__": colors["primary_soft"],
        "__SIDEBAR__": colors["sidebar"],
        "__INPUT__": colors["input"],
        "__SHADOW__": colors["shadow"],
    }
    for token, value in replacements.items():
        css = css.replace(token, value)
    st.markdown(css, unsafe_allow_html=True)


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
