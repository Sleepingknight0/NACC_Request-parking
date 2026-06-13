from __future__ import annotations

import html

import streamlit as st

from modules.constants import GUARD_TASK_STATUS_LABELS, REQUEST_STATUS_LABELS


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #FFFFFF;
            --surface: #F7F7F7;
            --surface-2: #F1F1F1;
            --text: #111111;
            --muted: #666666;
            --border: #E5E5E5;
            --black: #000000;
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

        section[data-testid="stSidebar"] {
            background: #FAFAFA;
            border-right: 1px solid var(--border);
        }

        div[data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--border);
            padding: 14px;
            border-radius: 8px;
        }

        .nacc-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 14px;
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
