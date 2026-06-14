from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.auth import ROLE_ADMIN, ROLE_OFFICER, get_current_role, require_role
from modules.constants import REQUEST_STATUS_LABELS
from modules.guard_packages import summarize_dates
from modules.pdf_generator import build_parking_pdf
from modules.sheets import read_sheet
from modules.ui import inject_global_css, render_dataframe, render_page_title, status_badge


st.set_page_config(page_title="รายการหนังสือ", page_icon="icon.svg", layout="wide")
inject_global_css()
require_role([ROLE_OFFICER, ROLE_ADMIN], "request_list")
render_page_title("รายการหนังสือ", "ค้นหาด้วยเลขหนังสือ สำนัก/หน่วยงาน หรือทะเบียน")

with st.spinner("กำลังโหลดข้อมูล..."):
    requests = read_sheet("Requests")
    dates = read_sheet("Request_Dates")
    vehicles = read_sheet("Vehicles")

query = st.text_input(
    "ค้นหาด้วยเลขหนังสือ / สำนัก / ทะเบียน",
    placeholder="เลขหนังสือ, สำนัก/หน่วยงาน, ทะเบียน",
)

with st.expander("ตัวกรองเพิ่มเติม"):
    col1, col2, col3 = st.columns(3)
    status_options = ["ทั้งหมด", "draft", "pending", "active", "done", "cancelled"]
    status = col1.selectbox(
        "สถานะ",
        status_options,
        format_func=lambda value: "ทั้งหมด" if value == "ทั้งหมด" else REQUEST_STATUS_LABELS.get(value, value),
    )
    month = col2.text_input("เดือนที่จอด", placeholder="YYYY-MM")
    location = col3.text_input("จุดจอด")

df = requests.copy()
if status != "ทั้งหมด" and not df.empty:
    df = df[df["status"].astype(str) == status]
if location and not df.empty:
    df = df[df["parking_location"].astype(str).str.contains(location, case=False, regex=False)]
if month and not df.empty and not dates.empty:
    request_ids = dates[dates["month_key"].astype(str) == month]["request_id"].unique()
    df = df[df["request_id"].astype(str).isin(request_ids)]
if query and not df.empty:
    plate_request_ids = (
        vehicles[vehicles["plate_no"].astype(str).str.contains(query, case=False, regex=False)]["request_id"].unique()
        if not vehicles.empty
        else []
    )
    mask = (
        df["book_no"].astype(str).str.contains(query, case=False, regex=False)
        | df["source_agency"].astype(str).str.contains(query, case=False, regex=False)
        | df["parking_location"].astype(str).str.contains(query, case=False, regex=False)
        | df["request_id"].astype(str).isin(plate_request_ids)
    )
    df = df[mask]

if df.empty:
    st.info("ไม่พบรายการ")
    st.stop()

date_summary = {}
if not dates.empty:
    for request_id, group in dates.groupby(dates["request_id"].astype(str)):
        active = group[group["status"].astype(str) != "cancelled"]
        source = active if not active.empty else group
        date_summary[str(request_id)] = summarize_dates(source["parking_date"].tolist())

plate_lookup = {}
if not vehicles.empty:
    for request_id, group in vehicles.groupby(vehicles["request_id"].astype(str)):
        active = group[group["status"].astype(str) != "cancelled"]
        plate_lookup[str(request_id)] = active["plate_no"].astype(str).tolist()

st.subheader("รายการที่พบ")
for _, row in df.sort_values("updated_at", ascending=False).head(30).iterrows():
    request_id = str(row["request_id"])
    dates_text = date_summary.get(request_id, "-")
    plates = plate_lookup.get(request_id, [])
    with st.container(border=True):
        st.markdown(f"### เลขหนังสือ {row['book_no']}")
        st.markdown(status_badge(row["status"]), unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        col_a.write(f"**สำนัก/หน่วยงาน:** {row['source_agency']}")
        col_a.write(f"**วันที่รับเรื่อง:** {row['received_date']}")
        col_a.write(f"**วันที่จอด:** {dates_text}")
        col_b.write(f"**จุดจอด:** {row['parking_location']}")
        col_b.write(f"**จำนวนรถ:** {row['car_count']}")
        col_b.write(f"**ทะเบียน:** {', '.join(plates) if plates else 'ไม่มีทะเบียน'}")
        action_col1, action_col2 = st.columns(2)
        if action_col1.button("เปิดรายละเอียด", key=f"open_detail_{request_id}", use_container_width=True):
            st.session_state["selected_request_id"] = request_id
            st.switch_page("pages/04_รายละเอียดหนังสือ.py")
        car_count_value = pd.to_numeric(row["car_count"], errors="coerce")
        pdf_bytes = build_parking_pdf(
            agency=str(row["source_agency"]),
            car_count=int(car_count_value) if pd.notna(car_count_value) else 1,
            plates=plates,
            parking_location=str(row["parking_location"]),
            date_summary=dates_text,
            book_no=str(row["book_no"]),
        )
        action_col2.download_button(
            "ดาวน์โหลด PDF",
            pdf_bytes,
            f"parking_sign_{row['book_no']}.pdf",
            "application/pdf",
            use_container_width=True,
            key=f"list_pdf_{request_id}",
        )

if len(df) > 30:
    st.caption(f"แสดง 30 รายการแรกจากทั้งหมด {len(df)} รายการ")

if get_current_role() == ROLE_ADMIN:
    with st.expander("ดูตารางข้อมูล"):
        show_cols = ["book_no", "received_date", "source_agency", "car_count", "parking_location", "status", "updated_at"]
        render_dataframe(df, show_cols, worksheet="Requests")
        st.download_button("ส่งออก CSV", df.to_csv(index=False).encode("utf-8-sig"), "parking_requests.csv", "text/csv")
