from __future__ import annotations

import html

import streamlit as st

from modules.constants import GUARD_TASK_STATUS_LABELS, REQUEST_STATUS_LABELS


THEME_OPTIONS = ("day", "night")
THEME_QUERY_VALUES = {"day": "day", "light": "day", "night": "night", "dark": "night"}
THEME_QUERY_KEYS = {"day": "day", "night": "night"}

THEMES = {
    "day": {
        "bg": "#FFFFFF",
        "surface": "#FFFFFF",
        "surface_2": "#F7F2FB",
        "surface_3": "#FFFFFF",
        "text": "#1A1020",
        "muted": "#66566F",
        "border": "#E7DDF0",
        "primary": "#61116C",
        "primary_hover": "#4B0D55",
        "on_primary": "#FFFFFF",
        "primary_soft": "#F3EAF7",
        "sidebar": "#FFFFFF",
        "input": "#FFFFFF",
        "shadow": "0 1px 3px rgba(97, 17, 108, 0.10)",
    },
    "night": {
        "bg": "#140718",
        "surface": "#211027",
        "surface_2": "#2C1735",
        "surface_3": "#190B1F",
        "text": "#FFF8FF",
        "muted": "#D8C4E0",
        "border": "#4A2656",
        "primary": "#D2A808",
        "primary_hover": "#E7C248",
        "on_primary": "#1A1020",
        "primary_soft": "#341840",
        "sidebar": "#18091D",
        "input": "#24102B",
        "shadow": "0 1px 3px rgba(0, 0, 0, 0.34)",
    },
}


def _theme_mode() -> str:
    query_theme = st.query_params.get("theme", "")
    if isinstance(query_theme, list):
        query_theme = query_theme[0] if query_theme else ""

    mode = THEME_QUERY_VALUES.get(str(query_theme).lower(), st.session_state.get("nacc_theme_mode", THEME_OPTIONS[0]))
    st.session_state.nacc_theme_mode = mode

    day_active = " is-active" if mode == "day" else ""
    night_active = " is-active" if mode == "night" else ""
    st.markdown(
        f"""
        <nav class="theme-switcher" aria-label="เลือกธีม">
            <a class="theme-icon-button{day_active}" href="?theme={THEME_QUERY_KEYS["day"]}" target="_self" title="ธีมเช้า" aria-label="ธีมเช้า">☀</a>
            <a class="theme-icon-button{night_active}" href="?theme={THEME_QUERY_KEYS["night"]}" target="_self" title="ธีมกลางคืน" aria-label="ธีมกลางคืน">☾</a>
        </nav>
        """,
        unsafe_allow_html=True,
    )
    return mode


def inject_global_css() -> None:
    mode = _theme_mode()
    colors = THEMES.get(mode, THEMES["day"])
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
            --on-primary: __ON_PRIMARY__;
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
            top: 58px;
            right: 24px;
            z-index: 100000;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px;
            background: var(--surface);
            border: 2px solid var(--border);
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
            color: var(--on-primary) !important;
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

        header[data-testid="stHeader"] {
            pointer-events: none;
        }

        header[data-testid="stHeader"] * {
            pointer-events: none;
        }

        header[data-testid="stHeader"] button,
        header[data-testid="stHeader"] a,
        header[data-testid="stHeader"] [role="button"],
        header[data-testid="stHeader"] [data-testid="stAppDeployButton"],
        header[data-testid="stHeader"] [data-testid="stToolbar"] button,
        header[data-testid="stHeader"] [data-testid="stToolbar"] a,
        header[data-testid="stHeader"] [data-testid="stToolbar"] [role="button"] {
            pointer-events: auto;
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

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] ul li:first-child a[data-testid="stSidebarNavLink"] > * {
            display: none !important;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] ul li:first-child a::after {
            content: "หน้าหลัก";
            font-size: 0.92rem;
            font-weight: 700;
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
        div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stJson"],
        div[data-testid="stCodeBlock"],
        div[data-testid="stFileUploader"],
        div[data-testid="stFileUploader"] section,
        div[data-testid="stFileUploader"] div[data-testid="stFileUploaderDropzone"] {
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

        div[data-testid="stNumberInput"] button,
        div[data-testid="stNumberInput"] [role="button"],
        div[data-testid="stFileUploader"] button,
        div[data-testid="stDownloadButton"] button {
            background: var(--primary-soft) !important;
            color: var(--text) !important;
            border-color: var(--border) !important;
        }

        div[data-testid="stFileUploader"] small,
        div[data-testid="stFileUploader"] span,
        div[data-testid="stFileUploader"] p {
            color: var(--muted) !important;
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
            color: var(--on-primary);
        }

        button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
            background: var(--primary-hover);
            border-color: var(--primary-hover);
            color: var(--on-primary);
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
        [data-testid="stJson"] *,
        [data-testid="stCodeBlock"] *,
        [data-testid="stElementToolbar"] * {
            color: var(--text) !important;
        }

        .nacc-empty-state {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--muted);
            padding: 14px 16px;
            margin: 4px 0 18px;
            box-shadow: var(--shadow);
        }

        .nacc-table {
            min-width: 720px;
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            overflow: hidden;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface-3);
            margin: 4px 0 18px;
            box-shadow: var(--shadow);
        }

        .nacc-table-wrap {
            width: 100%;
            overflow-x: auto;
            margin: 4px 0 18px;
        }

        .nacc-table th,
        .nacc-table td {
            color: var(--text);
            border-bottom: 1px solid var(--border);
            padding: 10px 12px;
            text-align: left;
            vertical-align: top;
            font-size: 0.92rem;
        }

        .nacc-table th {
            background: var(--surface);
            font-weight: 800;
        }

        .nacc-table tr:last-child td {
            border-bottom: 0;
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
                top: 58px;
                right: 16px;
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
        "__ON_PRIMARY__": colors["on_primary"],
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


def render_dataframe(df, columns: list[str] | None = None, empty_text: str = "ไม่มีรายการ") -> None:
    display_df = df
    if columns is not None:
        existing_columns = [column for column in columns if column in df.columns]
        display_df = df[existing_columns] if existing_columns else df

    if getattr(display_df, "empty", True):
        st.markdown(f'<div class="nacc-empty-state">{html.escape(empty_text)}</div>', unsafe_allow_html=True)
        return

    max_rows = 200
    truncated = len(display_df) > max_rows
    visible_df = display_df.head(max_rows).fillna("")
    headers = "".join(f"<th>{html.escape(str(column))}</th>" for column in visible_df.columns)
    body_rows = []
    for row in visible_df.to_dict(orient="records"):
        cells = "".join(f"<td>{html.escape(str(value))}</td>" for value in row.values())
        body_rows.append(f"<tr>{cells}</tr>")

    note = ""
    if truncated:
        note = f'<div class="nacc-muted">แสดง {max_rows} รายการแรกจากทั้งหมด {len(display_df)} รายการ</div>'
    table = f"""
    <div class="nacc-table-wrap">
        <table class="nacc-table">
            <thead><tr>{headers}</tr></thead>
            <tbody>{"".join(body_rows)}</tbody>
        </table>
    </div>
    {note}
    """
    st.markdown(table, unsafe_allow_html=True)


def render_key_value_table(rows: list[tuple[str, str]], empty_text: str = "ไม่มีข้อมูล") -> None:
    if not rows:
        st.markdown(f'<div class="nacc-empty-state">{html.escape(empty_text)}</div>', unsafe_allow_html=True)
        return

    table_rows = "".join(
        f"<tr><th>{html.escape(str(label))}</th><td>{html.escape(str(value))}</td></tr>"
        for label, value in rows
    )
    st.markdown(f'<table class="nacc-table"><tbody>{table_rows}</tbody></table>', unsafe_allow_html=True)
