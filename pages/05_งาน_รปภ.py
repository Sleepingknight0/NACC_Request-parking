from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.auth import ROLE_ADMIN, ROLE_GUARD, get_current_role, require_role
from modules.guard_packages import build_guard_packages
from modules.pdf_generator import build_parking_pdf
from modules.sheets import read_sheet
from modules.ui import inject_global_css, render_dataframe, render_page_title, status_badge


st.set_page_config(page_title="งาน รปภ.", page_icon="icon.svg", layout="wide")
inject_global_css()
require_role([ROLE_GUARD, ROLE_ADMIN], "guard_tasks")
render_page_title("งาน รปภ.", "หนึ่งเลขหนังสือคือหนึ่งงาน ดาวน์โหลดป้ายและส่งงานจากการ์ดเดียว")

with st.spinner("กำลังโหลดข้อมูล..."):
    packages = build_guard_packages(include_cancelled=False)
    vehicles = read_sheet("Vehicles")

if packages.empty:
    st.info("ยังไม่มีงาน รปภ.")
    st.stop()

today = pd.Timestamp.today().date().isoformat()
tabs = st.tabs(["วันนี้", "งานค้าง", "ส่งแล้วรอตรวจ", "ทั้งหมด"])
sections = [
    packages[
        packages["start_date"].astype(str).le(today)
        & packages["end_date"].astype(str).ge(today)
        & packages["status"].isin(["pending", "in_progress"])
    ],
    packages[packages["status"].isin(["pending", "in_progress"])],
    packages[packages["status"] == "submitted"],
    packages,
]


def _plates_for(request_id: str) -> list[str]:
    if vehicles.empty:
        return []
    rows = vehicles[
        (vehicles["request_id"].astype(str) == str(request_id))
        & (vehicles["status"].astype(str) != "cancelled")
    ]
    return rows["plate_no"].astype(str).tolist()


def _render_cards(df) -> None:
    if df.empty:
        st.caption("ไม่มีรายการ")
        return
    for _, row in df.sort_values(["parking_date", "book_no"]).iterrows():
        plates = _plates_for(row["request_id"])
        with st.container(border=True):
            st.markdown(f"### เลขหนังสือ {row['book_no']}")
            st.markdown(status_badge(row["status"], "guard"), unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            col_a.write(f"**สำนัก/หน่วยงาน:** {row['source_agency']}")
            col_a.write(f"**วันที่จอด:** {row['date_summary']}")
            col_a.write(f"**เวลาที่จอด:** {row['parking_time'] or '-'}")
            col_b.write(f"**จุดจอด:** {row['parking_location']}")
            col_b.write(f"**จำนวนรถ:** {row['car_count']}")
            col_b.write(f"**ทะเบียน:** {', '.join(plates) if plates else 'ไม่มีทะเบียน'}")

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
            action_cols = st.columns(3 if get_current_role() == ROLE_ADMIN else 2)
            action_cols[0].download_button(
                "ดาวน์โหลด PDF",
                pdf_bytes,
                f"parking_sign_{row['book_no']}.pdf",
                "application/pdf",
                use_container_width=True,
                key=f"guard_pdf_{row['request_id']}_{row['status']}",
            )
            if action_cols[1].button("ส่งงาน", key=f"guard_submit_{row['request_id']}", use_container_width=True):
                st.session_state["selected_guard_request_id"] = str(row["request_id"])
                st.switch_page("pages/06_ส่งงาน_รปภ.py")
            if get_current_role() == ROLE_ADMIN:
                if action_cols[2].button("เปิดรายละเอียด", key=f"guard_detail_{row['request_id']}", use_container_width=True):
                    st.session_state["selected_request_id"] = str(row["request_id"])
                    st.switch_page("pages/04_รายละเอียดหนังสือ.py")


for tab, df in zip(tabs, sections):
    with tab:
        _render_cards(df)

if get_current_role() == ROLE_ADMIN:
    with st.expander("ดูตารางงานทั้งหมด"):
        render_dataframe(
            packages,
            ["book_no", "source_agency", "date_summary", "parking_location", "car_count", "status", "task_count"],
            status_kind="guard",
        )
