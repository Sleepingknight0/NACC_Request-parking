from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.auth import ROLE_ADMIN, ROLE_VIEWER, require_role
from modules.guard_packages import build_guard_packages
from modules.sheets import read_sheet
from modules.ui import inject_global_css, render_dataframe, render_page_title, status_badge


st.set_page_config(page_title="แดชบอร์ด", page_icon="icon.svg", layout="wide")
inject_global_css()
require_role([ROLE_ADMIN, ROLE_VIEWER], "dashboard")
render_page_title("แดชบอร์ด", "วันนี้มีงานอะไร งานไหนค้าง และงานไหนส่งแล้วรอตรวจ")

with st.spinner("กำลังโหลดข้อมูล..."):
    requests = read_sheet("Requests")
    dates = read_sheet("Request_Dates")
    packages = build_guard_packages()

default_month = pd.Timestamp.today().strftime("%Y-%m")
month_options = sorted([value for value in dates["month_key"].dropna().unique().tolist() if str(value).strip()]) if not dates.empty else []
selected_month = st.selectbox("เดือน", month_options or [default_month], index=0)

month_dates = dates[dates["month_key"].astype(str) == selected_month] if not dates.empty else dates
month_request_ids = set(month_dates["request_id"].astype(str)) if not month_dates.empty else set()
month_requests = requests[requests["request_id"].astype(str).isin(month_request_ids)] if month_request_ids else requests.iloc[0:0]
month_packages = packages[packages["request_id"].astype(str).isin(month_request_ids)] if month_request_ids and not packages.empty else packages.iloc[0:0]

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("หนังสือเดือนนี้", len(month_requests))
col2.metric("งาน รปภ.", len(month_packages))
col3.metric("งานค้าง", len(month_packages[month_packages["status"].isin(["pending", "in_progress"])]) if not month_packages.empty else 0)
col4.metric("ส่งแล้วรอตรวจ", len(month_packages[month_packages["status"] == "submitted"]) if not month_packages.empty else 0)
col5.metric("เสร็จสิ้น", len(month_packages[month_packages["status"] == "done"]) if not month_packages.empty else 0)
col6.metric("ยกเลิก", len(month_packages[month_packages["status"] == "cancelled"]) if not month_packages.empty else 0)


def _render_cards(df, empty_text: str) -> None:
    if df.empty:
        st.caption(empty_text)
        return
    for _, row in df.head(8).iterrows():
        with st.container(border=True):
            st.markdown(f"### เลขหนังสือ {row['book_no']}")
            st.markdown(status_badge(row["status"], "guard"), unsafe_allow_html=True)
            st.write(f"**สำนัก/หน่วยงาน:** {row['source_agency']}")
            st.write(f"**วันที่จอด:** {row['date_summary']}")
            st.write(f"**จุดจอด:** {row['parking_location']} | **จำนวนรถ:** {row['car_count']}")
            if st.button("เปิดรายละเอียด", key=f"dash_detail_{row['request_id']}", use_container_width=True):
                st.session_state["selected_request_id"] = str(row["request_id"])
                st.switch_page("pages/04_รายละเอียดหนังสือ.py")


today = pd.Timestamp.today().date().isoformat()
st.subheader("งานวันนี้")
today_packages = month_packages[
    month_packages["start_date"].astype(str).le(today)
    & month_packages["end_date"].astype(str).ge(today)
] if not month_packages.empty else month_packages
_render_cards(today_packages, "วันนี้ไม่มีงาน")

st.subheader("งานค้าง")
pending = month_packages[month_packages["status"].isin(["pending", "in_progress"])] if not month_packages.empty else month_packages
_render_cards(pending, "ไม่มีงานค้าง")

st.subheader("ส่งแล้วรอตรวจ")
submitted = month_packages[month_packages["status"] == "submitted"] if not month_packages.empty else month_packages
_render_cards(submitted, "ไม่มีงานส่งแล้วรอตรวจ")

with st.expander("ดูตาราง"):
    render_dataframe(
        month_packages,
        ["book_no", "source_agency", "date_summary", "parking_location", "car_count", "status", "submitted_at", "completed_at"],
        status_kind="guard",
        empty_text="ไม่มีข้อมูล",
    )
