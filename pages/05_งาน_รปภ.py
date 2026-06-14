from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.auth import ROLE_ADMIN, ROLE_GUARD, get_current_role, require_role
from modules.db import accept_guard_package
from modules.guard_packages import build_guard_packages
from modules.locks import begin_action_lock, end_action_lock
from modules.pdf_generator import build_parking_pdf
from modules.sheets import read_sheet
from modules.ui import inject_global_css, render_dataframe, render_page_title, status_badge


st.set_page_config(page_title="งาน รปภ.", page_icon="icon.svg", layout="wide")
inject_global_css()
require_role([ROLE_GUARD, ROLE_ADMIN], "guard_tasks")
render_page_title("งาน รปภ.", "รับงาน ดาวน์โหลดป้าย และส่งรูปงาน")

with st.spinner("กำลังโหลดข้อมูล..."):
    packages = build_guard_packages()
    vehicles = read_sheet("Vehicles")

if packages.empty:
    st.info("ยังไม่มีงาน รปภ.")
    st.stop()

if get_current_role() != ROLE_ADMIN:
    packages = packages[packages["status"] != "cancelled"]

active = packages[packages["status"].isin(["pending", "in_progress"])] if not packages.empty else packages
open_jobs = active[active["is_open"].astype(bool)] if not active.empty else active
upcoming_jobs = active[~active["is_open"].astype(bool)] if not active.empty else active
submitted_jobs = packages[packages["status"] == "submitted"] if not packages.empty else packages
done_jobs = packages[packages["status"] == "done"] if not packages.empty else packages
cancelled_jobs = packages[packages["status"] == "cancelled"] if not packages.empty else packages

metric_cols = st.columns(5)
metric_cols[0].metric("งานเปิดให้ทำ", len(open_jobs))
metric_cols[1].metric("งานใกล้ถึง", len(upcoming_jobs))
metric_cols[2].metric("ส่งแล้วรอตรวจ", len(submitted_jobs))
metric_cols[3].metric("เสร็จแล้ว", len(done_jobs))
metric_cols[4].metric("ยกเลิก", len(cancelled_jobs))


def _plates_for(request_id: str) -> list[str]:
    if vehicles.empty:
        return []
    rows = vehicles[
        (vehicles["request_id"].astype(str) == str(request_id))
        & (vehicles["status"].astype(str) != "cancelled")
    ]
    return rows["plate_no"].astype(str).tolist()


def _download_pdf(row, plates: list[str], key: str) -> None:
    car_count_value = pd.to_numeric(row["car_count"], errors="coerce")
    pdf_bytes = build_parking_pdf(
        agency=row["source_agency"],
        car_count=int(car_count_value) if pd.notna(car_count_value) else 1,
        plates=plates,
        parking_location=row["parking_location"],
        date_summary=row["date_summary"],
        parking_time=row["parking_time"],
        book_no=row["book_no"],
    )
    st.download_button(
        "ดาวน์โหลดป้าย",
        pdf_bytes,
        f"parking_sign_{row['book_no']}.pdf",
        "application/pdf",
        use_container_width=True,
        key=key,
    )


def _render_cards(df, prefix: str) -> None:
    if df.empty:
        st.caption("ไม่มีรายการ")
        return
    for _, row in df.sort_values(["parking_date", "book_no"]).iterrows():
        request_id = str(row["request_id"])
        plates = _plates_for(request_id)
        status = str(row["status"])
        is_open = bool(row.get("is_open", False))
        with st.container(border=True):
            st.markdown(f"### เลขหนังสือ {row['book_no']}")
            st.markdown(status_badge(status, "guard"), unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            col_a.write(f"**สำนัก/หน่วยงาน:** {row['source_agency']}")
            col_a.write(f"**วันที่จอด:** {row['date_summary']}")
            col_a.write(f"**เวลา:** {row['parking_time'] or '-'}")
            col_b.write(f"**จุดจอด:** {row['parking_location']}")
            col_b.write(f"**จำนวนรถ:** {row['car_count']}")
            col_b.write(f"**ทะเบียน:** {', '.join(plates) if plates else 'ไม่มีทะเบียน'}")
            if not is_open and status in {"pending", "in_progress"}:
                st.caption(f"เปิดให้ทำวันที่ {row.get('open_date') or '-'}")

            action_cols = st.columns(3 if get_current_role() == ROLE_ADMIN else 2)
            with action_cols[0]:
                _download_pdf(row, plates, f"{prefix}_pdf_{request_id}_{status}")

            if status == "pending":
                if is_open:
                    if action_cols[1].button("รับงาน", key=f"{prefix}_accept_{request_id}", use_container_width=True):
                        lock_key = f"accept_{request_id}"
                        if not begin_action_lock(lock_key):
                            st.warning("กรุณารอสักครู่ อย่ากดซ้ำ")
                        else:
                            try:
                                with st.spinner("กำลังรับงาน..."):
                                    accept_guard_package(request_id)
                                st.success("รับงานแล้ว")
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))
                            finally:
                                end_action_lock(lock_key)
                else:
                    action_cols[1].button("ยังไม่ถึงวันทำงาน", key=f"{prefix}_not_open_{request_id}", disabled=True, use_container_width=True)
            elif status == "in_progress":
                if action_cols[1].button("ส่งงาน", key=f"{prefix}_submit_{request_id}", use_container_width=True):
                    st.session_state["selected_guard_request_id"] = request_id
                    st.switch_page("pages/06_ส่งงาน_รปภ.py")
            elif status == "submitted":
                action_cols[1].button("ส่งแล้ว รอผู้ดูแลยืนยัน", key=f"{prefix}_submitted_{request_id}", disabled=True, use_container_width=True)
            elif status == "done":
                action_cols[1].button("เสร็จสิ้น", key=f"{prefix}_done_{request_id}", disabled=True, use_container_width=True)
            elif status == "cancelled":
                action_cols[1].button("ยกเลิก", key=f"{prefix}_cancelled_{request_id}", disabled=True, use_container_width=True)

            if get_current_role() == ROLE_ADMIN:
                if action_cols[2].button("เปิดรายละเอียด", key=f"{prefix}_detail_{request_id}", use_container_width=True):
                    st.session_state["selected_request_id"] = request_id
                    st.switch_page("pages/04_รายละเอียดหนังสือ.py")


tabs = ["งานเปิดให้ทำ", "งานใกล้ถึง", "ส่งแล้วรอตรวจ", "เสร็จแล้ว"]
frames = [open_jobs, upcoming_jobs, submitted_jobs, done_jobs]
if get_current_role() == ROLE_ADMIN:
    tabs.append("ยกเลิก")
    frames.append(cancelled_jobs)

for tab, df in zip(st.tabs(tabs), frames):
    with tab:
        _render_cards(df, tab)

if get_current_role() == ROLE_ADMIN:
    with st.expander("ดูตารางงานทั้งหมด"):
        render_dataframe(
            packages,
            ["book_no", "source_agency", "date_summary", "parking_location", "car_count", "status", "task_count"],
            status_kind="guard",
        )
