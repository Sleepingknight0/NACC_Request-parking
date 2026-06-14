import pandas as pd
import streamlit as st

from modules.sheets import read_sheet
from modules.ui import inject_global_css, render_dataframe, render_page_title, render_record_cards


st.set_page_config(page_title="แดชบอร์ด", page_icon="icon.svg", layout="wide")
inject_global_css()
render_page_title("แดชบอร์ด", "ดูเฉพาะตัวเลขและงานที่ต้องตัดสินใจก่อน")

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

if not month_tasks.empty and not requests.empty:
    task_view = month_tasks.merge(
        requests[["request_id", "book_no", "source_agency", "car_count"]],
        on="request_id",
        how="left",
    )
else:
    task_view = month_tasks

st.subheader("งานวันนี้")
today = pd.Timestamp.today().date().isoformat()
today_tasks = task_view[task_view["parking_date"].astype(str) == today] if not task_view.empty else task_view
render_record_cards(
    today_tasks,
    title_field="source_agency",
    fields=["parking_date", "parking_location", "car_count", "status"],
    worksheet="Guard_Tasks",
    status_kind="guard",
    empty_text="วันนี้ไม่มีงาน รปภ.",
    max_cards=6,
)

st.subheader("งานค้าง")
pending = task_view[task_view["status"].isin(["pending", "in_progress"])] if not task_view.empty else task_view
render_dataframe(
    pending,
    ["parking_date", "source_agency", "parking_location", "car_count", "status"],
    worksheet="Guard_Tasks",
    status_kind="guard",
    empty_text="ไม่มีงานค้าง",
)

st.subheader("งานส่งแล้วรอตรวจ")
submitted = task_view[task_view["status"] == "submitted"] if not task_view.empty else task_view
render_dataframe(
    submitted,
    ["parking_date", "source_agency", "parking_location", "car_count", "status"],
    worksheet="Guard_Tasks",
    status_kind="guard",
    empty_text="ไม่มีงานส่งแล้วรอตรวจ",
)
