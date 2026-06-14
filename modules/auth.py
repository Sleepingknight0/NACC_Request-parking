from __future__ import annotations

import streamlit as st


ROLE_ADMIN = "admin"
ROLE_OFFICER = "officer"
ROLE_GUARD = "guard"
ROLE_VIEWER = "viewer"

ROLE_LABELS = {
    ROLE_GUARD: "รปภ.",
    ROLE_OFFICER: "เจ้าหน้าที่",
    ROLE_ADMIN: "แอดมิน",
    ROLE_VIEWER: "ผู้ดูข้อมูล",
}

ROLE_DESCRIPTIONS = {
    ROLE_GUARD: "ดูงาน ดาวน์โหลดป้าย และส่งรูปงาน",
    ROLE_OFFICER: "บันทึกหนังสือและค้นหาคำขอ",
    ROLE_ADMIN: "ตรวจงาน รายงาน และตั้งค่าระบบ",
    ROLE_VIEWER: "ดูข้อมูลอย่างเดียว",
}

PAGE_ACCESS = {
    "home": [ROLE_GUARD, ROLE_OFFICER, ROLE_ADMIN, ROLE_VIEWER],
    "dashboard": [ROLE_ADMIN, ROLE_VIEWER],
    "new_request": [ROLE_OFFICER, ROLE_ADMIN],
    "request_list": [ROLE_OFFICER, ROLE_ADMIN, ROLE_VIEWER],
    "request_detail": [ROLE_OFFICER, ROLE_ADMIN, ROLE_VIEWER],
    "guard_tasks": [ROLE_GUARD, ROLE_ADMIN],
    "guard_submit": [ROLE_GUARD, ROLE_ADMIN],
    "monthly_report": [ROLE_ADMIN, ROLE_VIEWER],
    "settings": [ROLE_ADMIN],
}


def get_current_role() -> str | None:
    role = st.session_state.get("user_role")
    if role in ROLE_LABELS:
        return str(role)

    query_role = st.query_params.get("role", "")
    if isinstance(query_role, list):
        query_role = query_role[0] if query_role else ""
    if query_role in ROLE_LABELS:
        st.session_state["user_role"] = query_role
        return str(query_role)

    return None


def set_current_role(role: str) -> None:
    if role not in ROLE_LABELS:
        raise ValueError("Unknown role")
    st.session_state["user_role"] = role
    st.query_params["role"] = role


def clear_role() -> None:
    st.session_state.pop("user_role", None)
    if "role" in st.query_params:
        del st.query_params["role"]


def can_access(page_key: str, role: str | None = None) -> bool:
    selected_role = role or get_current_role()
    if selected_role == ROLE_ADMIN:
        return True
    return selected_role in PAGE_ACCESS.get(page_key, [ROLE_ADMIN])


def render_role_selector() -> None:
    st.markdown("## ระบบขอที่จอดรถ ป.ป.ช.")
    st.caption("คุณใช้งานในฐานะอะไร")

    role_order = [ROLE_GUARD, ROLE_OFFICER, ROLE_ADMIN]
    columns = st.columns(3)
    for column, role in zip(columns, role_order):
        with column:
            st.markdown(f"### {ROLE_LABELS[role]}")
            st.write(ROLE_DESCRIPTIONS[role])
            if st.button(f"เข้าใช้งานในฐานะ{ROLE_LABELS[role]}", key=f"select_role_{role}", use_container_width=True):
                set_current_role(role)
                st.rerun()

    with st.expander("ผู้ดูข้อมูล"):
        st.write(ROLE_DESCRIPTIONS[ROLE_VIEWER])
        if st.button("เข้าใช้งานแบบดูข้อมูล", key="select_role_viewer", use_container_width=True):
            set_current_role(ROLE_VIEWER)
            st.rerun()


def render_role_badge() -> None:
    role = get_current_role()
    with st.sidebar:
        if role:
            st.caption(f"บทบาท: {ROLE_LABELS.get(role, role)}")
            if st.button("เปลี่ยนบทบาท", use_container_width=True):
                clear_role()
                st.rerun()


def require_role(allowed_roles: list[str], page_key: str | None = None) -> None:
    role = get_current_role()
    render_role_badge()
    if not role:
        render_role_selector()
        st.stop()

    allowed = allowed_roles
    if page_key is not None:
        allowed = PAGE_ACCESS.get(page_key, allowed_roles)

    if role != ROLE_ADMIN and role not in allowed:
        st.warning("หน้านี้ไม่เปิดให้บทบาทของคุณใช้งาน")
        if st.button("เปลี่ยนบทบาท", key=f"blocked_change_role_{page_key or 'page'}"):
            clear_role()
            st.rerun()
        st.stop()
