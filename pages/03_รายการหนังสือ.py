import pandas as pd
import streamlit as st

from modules.sheets import read_sheet
from modules.ui import inject_global_css, render_page_title


st.set_page_config(page_title="รายการหนังสือ", page_icon="🔎", layout="wide")
inject_global_css()
render_page_title("รายการหนังสือ", "ค้นหาและกรองคำขอที่จอดรถ")

requests = read_sheet("Requests")
dates = read_sheet("Request_Dates")
vehicles = read_sheet("Vehicles")

query = st.text_input("ค้นหา", placeholder="request_id, เลขหนังสือ, สำนัก, ทะเบียน")
col1, col2, col3 = st.columns(3)
status = col1.selectbox("สถานะ", ["ทั้งหมด", "draft", "pending", "active", "done", "cancelled"])
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
    show_cols = ["request_id", "book_no", "received_date", "source_agency", "car_count", "parking_location", "status", "updated_at"]
    st.dataframe(df[show_cols], use_container_width=True, hide_index=True)
    st.download_button("ส่งออก CSV", df.to_csv(index=False).encode("utf-8-sig"), "parking_requests.csv", "text/csv")
else:
    st.info("ไม่พบรายการ")
