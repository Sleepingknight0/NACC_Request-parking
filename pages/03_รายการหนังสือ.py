import pandas as pd
import streamlit as st

from modules.constants import REQUEST_STATUS_LABELS
from modules.sheets import read_sheet
from modules.ui import inject_global_css, render_dataframe, render_page_title, render_record_cards


st.set_page_config(page_title="รายการหนังสือ", page_icon="icon.svg", layout="wide")
inject_global_css()
render_page_title("รายการหนังสือ", "ค้นหาคำขอด้วยข้อมูลที่ใช้จริง")

requests = read_sheet("Requests")
dates = read_sheet("Request_Dates")
vehicles = read_sheet("Vehicles")

query = st.text_input("ค้นหา", placeholder="เลขหนังสือ, รหัสคำขอ, สำนัก/หน่วยงาน หรือทะเบียน")
col1, col2, col3 = st.columns(3)
status_options = ["ทั้งหมด", "draft", "pending", "active", "done", "cancelled"]
status = col1.selectbox(
    "สถานะ",
    status_options,
    format_func=lambda value: "ทั้งหมด" if value == "ทั้งหมด" else REQUEST_STATUS_LABELS.get(value, value),
)
month = col2.text_input("เดือน", placeholder="YYYY-MM")
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
    plate_request_ids = vehicles[vehicles["plate_no"].astype(str).str.contains(query, case=False, regex=False)]["request_id"].unique() if not vehicles.empty else []
    mask = (
        df["request_id"].astype(str).str.contains(query, case=False, regex=False)
        | df["book_no"].astype(str).str.contains(query, case=False, regex=False)
        | df["source_agency"].astype(str).str.contains(query, case=False, regex=False)
        | df["request_id"].astype(str).isin(plate_request_ids)
    )
    df = df[mask]

if not df.empty:
    st.subheader("รายการที่พบ")
    render_record_cards(
        df,
        title_field="book_no",
        fields=["received_date", "source_agency", "car_count", "parking_location", "status"],
        worksheet="Requests",
        status_kind="request",
        max_cards=6,
    )
    show_cols = ["book_no", "received_date", "source_agency", "car_count", "parking_location", "status", "updated_at"]
    render_dataframe(df, show_cols, worksheet="Requests")
    st.download_button("ส่งออก CSV", df.to_csv(index=False).encode("utf-8-sig"), "parking_requests.csv", "text/csv")
else:
    st.info("ไม่พบรายการ")
