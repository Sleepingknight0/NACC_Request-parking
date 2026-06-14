from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.auth import ROLE_ADMIN, ROLE_GUARD, ROLE_OFFICER, ROLE_VIEWER, get_current_role, render_role_badge, render_role_selector
from modules.guard_packages import build_guard_packages
from modules.sheets import initialize_storage, read_sheet
from modules.ui import (
    inject_global_css,
    render_action_grid,
    render_page_title,
    status_badge,
)


def _metric_row(requests, packages) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("หนังสือทั้งหมด", len(requests))
    col2.metric("งาน รปภ.", len(packages))
    col3.metric("งานค้าง", len(packages[packages["status"].isin(["pending", "in_progress"])]) if not packages.empty else 0)
    col4.metric("ส่งแล้วรอตรวจ", len(packages[packages["status"] == "submitted"]) if not packages.empty else 0)


def _render_package_cards(packages, *, title: str, max_cards: int = 4, allow_detail: bool = False) -> None:
    st.subheader(title)
    if packages.empty:
        st.caption("ไม่มีรายการ")
        return
    for _, row in packages.head(max_cards).iterrows():
        with st.container(border=True):
            st.markdown(f"### เลขหนังสือ {row['book_no']}")
            st.markdown(status_badge(row["status"], "guard"), unsafe_allow_html=True)
            st.write(f"**สำนัก/หน่วยงาน:** {row['source_agency']}")
            st.write(f"**วันที่จอด:** {row['date_summary']}")
            st.write(f"**จุดจอด:** {row['parking_location']} | **จำนวนรถ:** {row['car_count']}")
            col1, col2 = st.columns(2)
            if col1.button("ส่งงาน", key=f"home_submit_{row['request_id']}", use_container_width=True):
                st.session_state["selected_guard_request_id"] = str(row["request_id"])
                st.switch_page("pages/06_ส่งงาน_รปภ.py")
            if allow_detail:
                if col2.button("เปิดรายละเอียด", key=f"home_detail_{row['request_id']}", use_container_width=True):
                    st.session_state["selected_request_id"] = str(row["request_id"])
                    st.switch_page("pages/04_รายละเอียดหนังสือ.py")


def _render_guard_home(packages) -> None:
    render_page_title("งาน รปภ.", "ดูงาน ดาวน์โหลดป้าย และส่งรูปงาน")
    render_action_grid(
        [
            ("งาน รปภ.", "/งาน_รปภ", "ดูงานที่ต้องทำและดาวน์โหลด PDF"),
            ("ส่งงาน", "/ส่งงาน_รปภ", "อัปโหลดรูปใกล้และรูปไกล"),
        ]
    )
    today = pd.Timestamp.today().date().isoformat()
    today_packages = packages[
        packages["start_date"].astype(str).le(today)
        & packages["end_date"].astype(str).ge(today)
        & packages["status"].isin(["pending", "in_progress"])
    ] if not packages.empty else packages
    pending = packages[packages["status"].isin(["pending", "in_progress"])] if not packages.empty else packages
    _render_package_cards(today_packages, title="งานวันนี้")
    _render_package_cards(pending, title="งานค้าง")


def _render_officer_home(requests, packages) -> None:
    render_page_title("งานเจ้าหน้าที่", "บันทึกหนังสือและค้นหาคำขอด้วยเลขหนังสือ")
    render_action_grid(
        [
            ("บันทึกหนังสือใหม่", "/บันทึกหนังสือ", "เพิ่มคำขอและสร้างงาน รปภ. หนึ่งงานต่อคำขอ"),
            ("ค้นหาเลขหนังสือ", "/รายการหนังสือ", "ค้นหาด้วยเลขหนังสือ สำนัก หรือทะเบียน"),
        ]
    )
    _metric_row(requests, packages)
    submitted = packages[packages["status"] == "submitted"] if not packages.empty else packages
    _render_package_cards(submitted, title="ส่งแล้วรอตรวจ", allow_detail=True)


def _render_admin_home(requests, packages) -> None:
    render_page_title("แผงควบคุมผู้ดูแล", "ตรวจงาน ซ่อมข้อมูล และดูรายงานระบบ")
    render_action_grid(
        [
            ("Dashboard", "/แดชบอร์ด", "ภาพรวมรายเดือนและงานเร่งด่วน"),
            ("บันทึกหนังสือ", "/บันทึกหนังสือ", "เพิ่มคำขอใหม่"),
            ("ค้นหา", "/รายการหนังสือ", "ค้นหาและเปิดรายละเอียด"),
            ("งาน รปภ.", "/งาน_รปภ", "ตรวจงานและดาวน์โหลด PDF"),
            ("รายงาน", "/รายงานรายเดือน", "สรุปข้อมูลรายเดือน"),
            ("ตั้งค่า", "/ตั้งค่า", "ซ่อมฐานข้อมูลและตรวจระบบ"),
        ]
    )
    _metric_row(requests, packages)
    submitted = packages[packages["status"] == "submitted"] if not packages.empty else packages
    _render_package_cards(submitted, title="ส่งแล้วรอตรวจ", allow_detail=True)


def _render_viewer_home(requests, packages) -> None:
    render_page_title("ดูข้อมูล", "ค้นหาและดูรายงานแบบอ่านอย่างเดียว")
    render_action_grid(
        [
            ("Dashboard", "/แดชบอร์ด", "ภาพรวมรายเดือน"),
            ("ค้นหา", "/รายการหนังสือ", "ค้นหาคำขอ"),
            ("รายงาน", "/รายงานรายเดือน", "สรุปรายเดือน"),
        ]
    )
    _metric_row(requests, packages)


def render_home() -> None:
    inject_global_css()
    initialize_storage()

    role = get_current_role()
    if not role:
        render_role_selector()
        return

    render_role_badge()
    with st.spinner("กำลังโหลดข้อมูล..."):
        requests = read_sheet("Requests")
        packages = build_guard_packages(include_cancelled=False)

    if role == ROLE_GUARD:
        _render_guard_home(packages)
    elif role == ROLE_OFFICER:
        _render_officer_home(requests, packages)
    elif role == ROLE_VIEWER:
        _render_viewer_home(requests, packages)
    elif role == ROLE_ADMIN:
        _render_admin_home(requests, packages)
