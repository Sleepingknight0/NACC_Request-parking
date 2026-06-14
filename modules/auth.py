from __future__ import annotations

import streamlit as st


ROLE_ADMIN = "admin"
ROLE_OFFICER = "officer"
ROLE_GUARD = "guard"

ROLE_LABELS = {
    ROLE_GUARD: "รปภ.",
    ROLE_OFFICER: "เจ้าหน้าที่",
    ROLE_ADMIN: "แอดมิน",
}

ROLE_DESCRIPTIONS = {
    ROLE_GUARD: "ดูงาน ดาวน์โหลดป้าย และส่งรูปงาน",
    ROLE_OFFICER: "บันทึกหนังสือ ค้นหา และดูประวัติคำขอ",
    ROLE_ADMIN: "ตรวจงาน รายงาน และตั้งค่าระบบ",
}

PAGE_ACCESS = {
    "home": [ROLE_GUARD, ROLE_OFFICER, ROLE_ADMIN],
    "dashboard": [ROLE_ADMIN],
    "new_request": [ROLE_OFFICER, ROLE_ADMIN],
    "request_list": [ROLE_OFFICER, ROLE_ADMIN],
    "request_detail": [ROLE_OFFICER, ROLE_ADMIN],
    "guard_tasks": [ROLE_GUARD, ROLE_ADMIN],
    "guard_submit": [ROLE_GUARD, ROLE_ADMIN],
    "monthly_report": [ROLE_ADMIN],
    "settings": [ROLE_ADMIN],
}


def _admin_pin() -> str:
    try:
        return str(st.secrets.get("app", {}).get("admin_pin", "1234"))
    except Exception:
        return "1234"


def get_current_role() -> str | None:
    role = st.session_state.get("user_role")
    if role in ROLE_LABELS:
        return str(role)

    return None


def set_current_role(role: str) -> None:
    if role not in ROLE_LABELS:
        raise ValueError("Unknown role")
    st.session_state["user_role"] = role


def clear_role() -> None:
    explicit_keys = {
        "user_role",
        "selected_request_id",
        "selected_guard_request_id",
        "selected_task_id",
        "selected_package_id",
        "last_created_request",
        "admin_pin_input",
    }
    for key in list(st.session_state.keys()):
        if key in explicit_keys or str(key).startswith("selected_"):
            st.session_state.pop(key, None)
    for key in ["role", "request_id", "task_id", "selected_request_id", "selected_guard_request_id"]:
        try:
            if key in st.query_params:
                del st.query_params[key]
        except Exception:
            continue


def _switch_home() -> None:
    for home_page in ("streamlit_app.py", "app.py"):
        try:
            st.switch_page(home_page)
        except st.errors.StreamlitAPIException:
            continue
    st.rerun()


def can_access(page_key: str, role: str | None = None) -> bool:
    selected_role = role or get_current_role()
    if selected_role == ROLE_ADMIN:
        return True
    return selected_role in PAGE_ACCESS.get(page_key, [ROLE_ADMIN])


def render_role_selector(*, redirect_home_on_select: bool = False) -> None:
    st.markdown(
        """
        <section class="nacc-role-landing">
            <h1>ระบบขอที่จอดรถ ป.ป.ช.</h1>
            <p>คุณคือใคร</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    role_order = [ROLE_GUARD, ROLE_OFFICER]
    columns = st.columns(2)
    for column, role in zip(columns, role_order):
        with column:
            st.markdown(
                f"""
                <div class="nacc-role-card">
                    <strong>{ROLE_LABELS[role]}</strong>
                    <span>{ROLE_DESCRIPTIONS[role]}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(ROLE_LABELS[role], key=f"select_role_{role}", use_container_width=True):
                set_current_role(role)
                if redirect_home_on_select:
                    _switch_home()
                st.rerun()

    with st.expander("สำหรับผู้ดูแลระบบ"):
        pin = st.text_input("รหัสผู้ดูแล", type="password", key="admin_pin_input")
        if st.button("เข้าสู่ระบบผู้ดูแล", key="select_role_admin", use_container_width=True):
            if pin == _admin_pin():
                set_current_role(ROLE_ADMIN)
                if redirect_home_on_select:
                    _switch_home()
                st.rerun()
            st.error("รหัสไม่ถูกต้อง")


def render_role_badge() -> None:
    role = get_current_role()
    with st.sidebar:
        if role:
            st.caption(f"บทบาท: {ROLE_LABELS.get(role, role)}")
            if st.button("เปลี่ยนผู้ใช้งาน", use_container_width=True):
                clear_role()
                _switch_home()


def require_role(allowed_roles: list[str], page_key: str | None = None) -> None:
    role = get_current_role()
    render_role_badge()
    if not role:
        if page_key and page_key != "home":
            st.warning("หน้านี้ไม่เปิดให้บทบาทของคุณใช้งาน")
        render_role_selector(redirect_home_on_select=True)
        st.stop()

    allowed = allowed_roles
    if page_key is not None:
        allowed = PAGE_ACCESS.get(page_key, allowed_roles)

    if role != ROLE_ADMIN and role not in allowed:
        st.warning("หน้านี้ไม่เปิดให้บทบาทของคุณใช้งาน")
        if st.button("เปลี่ยนผู้ใช้งาน", key=f"blocked_change_role_{page_key or 'page'}"):
            clear_role()
            _switch_home()
        st.stop()
