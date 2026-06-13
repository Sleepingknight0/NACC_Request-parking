import pandas as pd
import streamlit as st

from modules.sheets import read_sheet
from modules.ui import inject_global_css, render_dataframe, render_page_title


st.set_page_config(page_title="แดชบอร์ด", page_icon="icon.svg", layout="wide")
inject_global_css()
render_page_title("แดชบอร์ด", "ภาพรวมงานตามเดือน สถานะ และงานค้าง")

requests = read_sheet("Requests")
dates = read_sheet("Request_Dates")
tasks = read_sheet("Guard_Tasks")

month_options = sorted(dates["month_key"].dropna().unique().tolist()) if not dates.empty else []
default_month = pd.Timestamp.today().strftime("%Y-%m")
selected_month = st.selectbox("เดือน", month_options or [default_month], index=0)

month_dates = dates[dates["month_key"].astype(str) == selected_month] if not dates.empty else dates
month_tasks = tasks[tasks["parking_date"].astype(str).str.startswith(selected_month)] if not tasks.empty else tasks
active_request_ids = set(month_dates["request_id"].astype(str)) if not month_dates.empty else set()
month_requests = requests[requests["request_id"].astype(str).isin(active_request_ids)] if active_request_ids else requests.iloc[0:0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("หนังสือทั้งหมด", len(month_requests))
col2.metric("วันที่ขอจอด", len(month_dates))
col3.metric("จำนวนรถรวม", int(pd.to_numeric(month_requests.get("car_count"), errors="coerce").fillna(0).sum()) if not month_requests.empty else 0)
col4.metric("งานค้าง", len(month_tasks[month_tasks["status"].isin(["pending", "in_progress"])]) if not month_tasks.empty else 0)

col5, col6, col7 = st.columns(3)
col5.metric("งานส่งแล้ว", len(month_tasks[month_tasks["status"] == "submitted"]) if not month_tasks.empty else 0)
col6.metric("งานเสร็จ", len(month_tasks[month_tasks["status"] == "done"]) if not month_tasks.empty else 0)
col7.metric("งานยกเลิก", len(month_tasks[month_tasks["status"] == "cancelled"]) if not month_tasks.empty else 0)

st.subheader("งานวันนี้")
today = pd.Timestamp.today().date().isoformat()
today_tasks = month_tasks[month_tasks["parking_date"].astype(str) == today] if not month_tasks.empty else month_tasks
render_dataframe(today_tasks)

st.subheader("งานค้าง")
pending = month_tasks[month_tasks["status"].isin(["pending", "in_progress"])] if not month_tasks.empty else month_tasks
render_dataframe(pending)

st.subheader("งานส่งแล้วรอตรวจ")
submitted = month_tasks[month_tasks["status"] == "submitted"] if not month_tasks.empty else month_tasks
render_dataframe(submitted)
