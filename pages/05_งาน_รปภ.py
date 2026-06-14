import pandas as pd
import streamlit as st

from modules.pdf_generator import build_parking_pdf
from modules.sheets import get_request_by_id, list_vehicles, read_sheet
from modules.ui import inject_global_css, render_dataframe, render_page_title, render_record_cards


st.set_page_config(page_title="งาน รปภ.", page_icon="icon.svg", layout="wide")
inject_global_css()
render_page_title("งาน รปภ.", "ดูงานที่ต้องทำก่อน ดาวน์โหลดป้ายได้จากงานที่เลือก")

tasks = read_sheet("Guard_Tasks")
requests = read_sheet("Requests")
if tasks.empty:
    st.info("ยังไม่มีงาน รปภ.")
    st.stop()

joined = tasks.merge(requests, on="request_id", how="left", suffixes=("", "_request"))
today = pd.Timestamp.today().date()
tomorrow = today + pd.Timedelta(days=1)

sections = {
    "งานวันนี้": joined[joined["parking_date"].astype(str) == today.isoformat()],
    "งานพรุ่งนี้": joined[joined["parking_date"].astype(str) == tomorrow.isoformat()],
    "งานค้าง": joined[joined["status"].isin(["pending", "in_progress"])],
    "งานส่งแล้วรอตรวจ": joined[joined["status"] == "submitted"],
}

for title, df in sections.items():
    st.subheader(title)
    if df.empty:
        st.caption("ไม่มีรายการ")
        continue
    render_record_cards(
        df.sort_values("parking_date"),
        title_field="source_agency",
        fields=["parking_date", "parking_location", "car_count", "status"],
        worksheet="Guard_Tasks",
        status_kind="guard",
        max_cards=6,
    )

with st.expander("ดูตารางงานทั้งหมด"):
    render_dataframe(
        joined,
        ["parking_date", "source_agency", "parking_location", "car_count", "status"],
        worksheet="Guard_Tasks",
        status_kind="guard",
    )

st.subheader("ดาวน์โหลด PDF งานที่เลือก")
task_id = st.selectbox("เลือกงาน", tasks["task_id"].tolist())
task = tasks[tasks["task_id"] == task_id].iloc[0]
request = get_request_by_id(task["request_id"])
if request:
    plates = list_vehicles(request["request_id"])["plate_no"].tolist()
    pdf_bytes = build_parking_pdf(
        agency=request["source_agency"],
        car_count=int(request["car_count"]),
        plates=plates,
        parking_location=request["parking_location"],
        parking_date=task["parking_date"],
        book_no=request["book_no"],
    )
    st.download_button("ดาวน์โหลด PDF", pdf_bytes, f"parking_sign_{task_id}.pdf", "application/pdf")
