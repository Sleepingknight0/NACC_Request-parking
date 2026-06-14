from __future__ import annotations

import html
from urllib.parse import quote

import streamlit as st

from modules.constants import (
    GUARD_TASK_STATUS_LABELS,
    REQUEST_STATUS_LABELS,
    WORKSHEET_HEADER_LABELS,
)


THEME_OPTIONS = ("day", "night")
THEME_QUERY_VALUES = {"day": "day", "light": "day", "night": "night", "dark": "night"}
THEME_QUERY_KEYS = {"day": "day", "night": "night"}

THEMES = {
    "day": {
        "bg": "#FEFBFF",
        "surface": "#FFFFFF",
        "surface_2": "#F5ECF8",
        "surface_3": "#FFFFFF",
        "text": "#1A1020",
        "muted": "#66566F",
        "border": "#E2D2EA",
        "primary": "#61116C",
        "primary_hover": "#4B0D55",
        "on_primary": "#FFFFFF",
        "primary_soft": "#EFE0F4",
        "sidebar": "#F7F0FA",
        "input": "#FFFFFF",
        "shadow": "0 4px 14px rgba(97, 17, 108, 0.08)",
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
        "shadow": "0 4px 16px rgba(0, 0, 0, 0.32)",
    },
}


def _theme_mode() -> str:
    query_theme = st.query_params.get("theme", "")
    if isinstance(query_theme, list):
        query_theme = query_theme[0] if query_theme else ""

    mode = THEME_QUERY_VALUES.get(str(query_theme).lower(), st.session_state.get("nacc_theme_mode", THEME_OPTIONS[0]))
    st.session_state.nacc_theme_mode = mode
    role = st.session_state.get("user_role") or st.query_params.get("role", "")
    if isinstance(role, list):
        role = role[0] if role else ""
    role_suffix = f"&role={quote(str(role))}" if role else ""

    day_active = " is-active" if mode == "day" else ""
    night_active = " is-active" if mode == "night" else ""
    st.markdown(
        f"""
        <nav class="theme-switcher" aria-label="เลือกธีม">
            <a class="theme-icon-button{day_active}" href="?theme={THEME_QUERY_KEYS["day"]}{role_suffix}" target="_self" title="ธีมเช้า" aria-label="ธีมเช้า">☀</a>
            <a class="theme-icon-button{night_active}" href="?theme={THEME_QUERY_KEYS["night"]}{role_suffix}" target="_self" title="ธีมกลางคืน" aria-label="ธีมกลางคืน">☾</a>
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

        h1 {
            border-left: 6px solid var(--primary);
            padding-left: 14px;
            line-height: 1.08;
            max-width: 100%;
            overflow-wrap: break-word;
        }

        h2, h3 {
            color: var(--primary);
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

        section[data-testid="stSidebar"] > div {
            background: var(--sidebar);
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
            background: var(--primary) !important;
            color: var(--on-primary) !important;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover *,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] * {
            color: var(--on-primary) !important;
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

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] ul li:first-child a:hover::after,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] ul li:first-child a[aria-current="page"]::after {
            color: var(--on-primary);
        }

        div[data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-top: 4px solid var(--primary);
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
            border-top: 4px solid var(--primary);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 14px;
            box-shadow: var(--shadow);
        }

        .nacc-hero {
            background:
                linear-gradient(135deg, var(--surface) 0%, var(--surface-2) 100%);
            border: 1px solid var(--border);
            border-left: 7px solid var(--primary);
            border-radius: 10px;
            padding: 22px 24px;
            margin: 2px 0 20px;
            box-shadow: var(--shadow);
        }

        .nacc-hero h1 {
            border-left: 0;
            padding-left: 0;
            margin: 0 0 8px;
        }

        .nacc-hero p {
            color: var(--muted);
            margin: 0;
            font-size: 1rem;
            line-height: 1.55;
        }

        .nacc-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px;
            margin: 12px 0 20px;
        }

        .nacc-record-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-left: 5px solid var(--primary);
            border-radius: 8px;
            padding: 14px 15px;
            box-shadow: var(--shadow);
            min-height: 118px;
        }

        .nacc-record-card-title {
            color: var(--text);
            font-weight: 850;
            font-size: 1rem;
            line-height: 1.35;
            margin-bottom: 8px;
            overflow-wrap: anywhere;
        }

        .nacc-record-card-meta {
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .nacc-action-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
            gap: 10px;
            margin: 14px 0 22px;
        }

        .nacc-action-card {
            display: block;
            background: var(--surface);
            border: 1px solid var(--border);
            border-top: 4px solid var(--primary);
            border-radius: 8px;
            padding: 14px;
            text-decoration: none !important;
            color: var(--text) !important;
            box-shadow: var(--shadow);
        }

        .nacc-action-card strong {
            display: block;
            color: var(--primary);
            font-size: 1rem;
            margin-bottom: 4px;
        }

        .nacc-action-card span {
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.45;
        }

        .nacc-action-card:hover {
            border-color: var(--primary);
            transform: translateY(-1px);
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

        div[data-testid="stForm"],
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-top: 4px solid var(--primary) !important;
            box-shadow: var(--shadow);
        }

        div[data-testid="stAlert"] {
            background: var(--surface-2) !important;
            border: 1px solid var(--border) !important;
            border-left: 4px solid var(--primary) !important;
            border-radius: 8px !important;
            box-shadow: var(--shadow);
        }

        div[data-testid="stAlert"] > div,
        div[data-testid="stAlert"] [role="alert"],
        div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] {
            background: transparent !important;
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

        div[data-testid="stFileUploader"] button,
        div[data-testid="stDownloadButton"] button {
            background: var(--primary) !important;
            color: var(--on-primary) !important;
            border-color: var(--primary) !important;
            font-weight: 800 !important;
            opacity: 1 !important;
        }

        div[data-testid="stFileUploader"] button *,
        div[data-testid="stDownloadButton"] button *,
        button[kind="primary"] *,
        div[data-testid="stFormSubmitButton"] button[kind="primary"] * {
            color: var(--on-primary) !important;
            fill: var(--on-primary) !important;
            stroke: var(--on-primary) !important;
            opacity: 1 !important;
        }

        div[data-testid="stRadio"] label,
        div[role="radiogroup"] label {
            background: var(--surface-2) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            padding: 6px 10px !important;
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
            background: var(--primary) !important;
            border-color: var(--primary) !important;
            color: var(--on-primary) !important;
            font-weight: 850 !important;
        }

        button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
            background: var(--primary-hover) !important;
            border-color: var(--primary-hover) !important;
            color: var(--on-primary) !important;
        }

        button[kind="secondary"] {
            background: var(--surface-3) !important;
            border-color: var(--border) !important;
            color: var(--text) !important;
            font-weight: 750 !important;
        }

        button[kind="secondary"]:hover {
            border-color: var(--primary) !important;
            color: var(--primary) !important;
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
            background: var(--surface-2);
            border: 1px solid var(--border);
            border-left: 4px solid var(--primary);
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
            background: var(--primary-soft);
            font-weight: 800;
            color: var(--primary);
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
            h1 {
                font-size: 2rem !important;
                line-height: 1.14;
                border-left-width: 5px;
                padding-left: 10px;
            }

            .theme-switcher {
                top: 58px;
                right: 16px;
            }

            .theme-icon-button {
                width: 30px;
                height: 30px;
                font-size: 17px;
            }

            .nacc-hero {
                padding: 18px 16px;
                margin-right: 68px;
            }

            .nacc-record-card {
                min-height: auto;
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
    subtitle_html = f"<p>{html.escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f"""
        <section class="nacc-hero">
            <h1>{html.escape(title)}</h1>
            {subtitle_html}
        </section>
        """,
        unsafe_allow_html=True,
    )


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


def _label_for_column(column: str, worksheet: str | None = None) -> str:
    if worksheet and worksheet in WORKSHEET_HEADER_LABELS:
        label = WORKSHEET_HEADER_LABELS[worksheet].get(column)
        if label:
            return label

    for labels in WORKSHEET_HEADER_LABELS.values():
        if column in labels:
            return labels[column]

    fallback_labels = {
        "requests": "จำนวนหนังสือ",
        "parking_dates": "จำนวนวันจอด",
        "cars": "จำนวนรถ",
        "active_tasks": "งานที่ยังเปิดอยู่",
        "source_agency": "สำนัก/หน่วยงาน",
        "parking_location": "จุดจอด",
        "status": "สถานะ",
    }
    return fallback_labels.get(column, column)


def _status_label(value: str, kind: str = "request") -> str:
    labels = GUARD_TASK_STATUS_LABELS if kind == "guard" else REQUEST_STATUS_LABELS
    return labels.get(str(value or "").strip(), str(value or "").strip() or "-")


def _display_value(column: str, value, status_kind: str = "request") -> str:
    text = "" if value is None else str(value)
    if not text or text.lower() == "nan":
        return "-"
    if column == "status":
        return _status_label(text, status_kind)
    if column == "has_vehicle_plates":
        return "มี" if text.upper() in {"TRUE", "YES", "1"} else "ไม่มี"
    if column == "is_final":
        return "ใช่" if text.upper() in {"TRUE", "YES", "1"} else "ไม่ใช่"
    return text


def is_local_upload_url(url: str | None) -> bool:
    text = str(url or "").strip()
    if not text:
        return False
    return text.startswith("uploads/") or text.startswith("uploads\\")


def safe_file_link(url: str | None, label: str = "เปิดไฟล์") -> None:
    text = str(url or "").strip()
    if not text:
        st.caption("ไม่มีไฟล์แนบ")
        return
    if is_local_upload_url(text):
        st.warning("ไฟล์นี้อยู่ในพื้นที่ชั่วคราวของแอป ยังไม่ใช่ลิงก์ถาวร")
        st.caption(text)
        return
    st.link_button(label, text, use_container_width=True)


def with_role_url(href: str) -> str:
    role = st.session_state.get("user_role") or st.query_params.get("role", "")
    if isinstance(role, list):
        role = role[0] if role else ""
    if not role:
        return href
    separator = "&" if "?" in href else "?"
    return f"{href}{separator}role={quote(str(role))}"


def request_detail_url(request_id: str) -> str:
    return with_role_url(f"/รายละเอียดหนังสือ?request_id={quote(str(request_id))}")


def guard_submit_url(request_id: str) -> str:
    return with_role_url(f"/ส่งงาน_รปภ?request_id={quote(str(request_id))}")


def render_system_info_expander(row: dict, fields: list[str] | None = None) -> None:
    system_fields = fields or [
        "request_id",
        "request_date_id",
        "task_id",
        "primary_task_id",
        "task_ids",
        "source_request_date_ids",
        "created_at",
        "updated_at",
        "submitted_at",
        "completed_at",
    ]
    values = [(field, row.get(field, "")) for field in system_fields if row.get(field, "")]
    if not values:
        return
    with st.expander("ข้อมูลระบบ"):
        render_key_value_table([(field, str(value)) for field, value in values])


def to_display_dataframe(
    df,
    columns: list[str] | None = None,
    worksheet: str | None = None,
    status_kind: str = "request",
):
    display_df = df
    if columns is not None:
        existing_columns = [column for column in columns if column in df.columns]
        display_df = df[existing_columns] if existing_columns else df

    display_df = display_df.copy()
    for column in display_df.columns:
        display_df[column] = display_df[column].map(lambda value, col=column: _display_value(col, value, status_kind))

    display_df = display_df.rename(
        columns={column: _label_for_column(column, worksheet) for column in display_df.columns}
    )
    return display_df


def render_dataframe(
    df,
    columns: list[str] | None = None,
    empty_text: str = "ไม่มีรายการ",
    worksheet: str | None = None,
    status_kind: str = "request",
) -> None:
    display_df = df
    if columns is not None:
        existing_columns = [column for column in columns if column in df.columns]
        display_df = df[existing_columns] if existing_columns else df

    if getattr(display_df, "empty", True):
        st.markdown(f'<div class="nacc-empty-state">{html.escape(empty_text)}</div>', unsafe_allow_html=True)
        return

    display_df = to_display_dataframe(display_df, worksheet=worksheet, status_kind=status_kind)

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


def render_record_cards(
    df,
    *,
    title_field: str,
    subtitle_field: str | None = None,
    fields: list[str],
    worksheet: str | None = None,
    status_kind: str = "request",
    empty_text: str = "ไม่มีรายการ",
    max_cards: int = 8,
) -> None:
    if getattr(df, "empty", True):
        st.markdown(f'<div class="nacc-empty-state">{html.escape(empty_text)}</div>', unsafe_allow_html=True)
        return

    cards = []
    for row in df.head(max_cards).to_dict(orient="records"):
        title = _display_value(title_field, row.get(title_field, ""), status_kind)
        subtitle_html = ""
        if subtitle_field:
            subtitle = _display_value(subtitle_field, row.get(subtitle_field, ""), status_kind)
            if subtitle and subtitle != "-":
                subtitle_html = f'<div class="nacc-muted">{html.escape(subtitle)}</div>'
        meta_lines = []
        for field in fields:
            if field == title_field:
                continue
            label = _label_for_column(field, worksheet)
            value = _display_value(field, row.get(field, ""), status_kind)
            meta_lines.append(f"{html.escape(label)}: {html.escape(value)}")
        cards.append(
            "<article class=\"nacc-record-card\">"
            f"<div class=\"nacc-record-card-title\">{html.escape(title)}</div>"
            f"{subtitle_html}"
            f"<div class=\"nacc-record-card-meta\">{'<br>'.join(meta_lines)}</div>"
            "</article>"
        )

    note = ""
    if len(df) > max_cards:
        note = f'<div class="nacc-muted">แสดง {max_cards} รายการแรกจากทั้งหมด {len(df)} รายการ</div>'

    st.markdown(f'<div class="nacc-grid">{"".join(cards)}</div>{note}', unsafe_allow_html=True)


PAGE_PATHS = {
    "/แดชบอร์ด": "pages/01_แดชบอร์ด.py",
    "/บันทึกหนังสือ": "pages/02_บันทึกหนังสือ.py",
    "/รายการหนังสือ": "pages/03_รายการหนังสือ.py",
    "/รายละเอียดหนังสือ": "pages/04_รายละเอียดหนังสือ.py",
    "/งาน_รปภ": "pages/05_งาน_รปภ.py",
    "/ส่งงาน_รปภ": "pages/06_ส่งงาน_รปภ.py",
    "/รายงานรายเดือน": "pages/07_รายงานรายเดือน.py",
    "/ตั้งค่า": "pages/08_ตั้งค่า.py",
}


def render_action_grid(actions: list[tuple[str, str, str]]) -> None:
    cols = st.columns(min(len(actions), 3) or 1)
    for index, (label, href, description) in enumerate(actions):
        column = cols[index % len(cols)]
        target = PAGE_PATHS.get(href, href)
        with column:
            st.page_link(target, label=label, help=description, use_container_width=True)


def render_key_value_table(rows: list[tuple[str, str]], empty_text: str = "ไม่มีข้อมูล") -> None:
    if not rows:
        st.markdown(f'<div class="nacc-empty-state">{html.escape(empty_text)}</div>', unsafe_allow_html=True)
        return

    table_rows = "".join(
        f"<tr><th>{html.escape(str(label))}</th><td>{html.escape(str(value))}</td></tr>"
        for label, value in rows
    )
    st.markdown(f'<table class="nacc-table"><tbody>{table_rows}</tbody></table>', unsafe_allow_html=True)
