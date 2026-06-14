import pandas as pd
import streamlit as st

from modules.constants import (
    NACC_DEPARTMENTS,
    PARKING_LOCATIONS,
    WORKSHEET_HEADER_LABELS,
    WORKSHEET_SCHEMAS,
    sheet_title_for,
)
from modules.sheets import initialize_storage, read_sheet, write_sheet
from modules.ui import inject_global_css, render_dataframe, render_page_title


st.set_page_config(page_title="ตั้งค่า", page_icon="icon.svg", layout="wide")
inject_global_css()
render_page_title("ตั้งค่า", "ตรวจฐานข้อมูลและข้อมูลอ้างอิงที่ใช้ในระบบ")

initialize_storage()

if st.button("ปรับฐานข้อมูลให้เป็นภาษาไทย", type="primary"):
    for worksheet in WORKSHEET_SCHEMAS:
        write_sheet(worksheet, read_sheet(worksheet))
    st.success("ปรับหัวตาราง สถานะ และค่าใช่/ไม่ใช่ในฐานข้อมูลหลักเป็นภาษาไทยแล้ว")

st.subheader("พจนานุกรมข้อมูล")
for name, columns in WORKSHEET_SCHEMAS.items():
    with st.expander(sheet_title_for(name)):
        labels = WORKSHEET_HEADER_LABELS[name]
        render_dataframe(
            pd.DataFrame(
                {
                    "ลำดับ": range(1, len(columns) + 1),
                    "ชื่อคอลัมน์ใน Google Sheet": [labels.get(column, column) for column in columns],
                    "รหัสภายในระบบ": columns,
                }
            )
        )

st.subheader("สำนัก/หน่วยงาน")
render_dataframe(
    pd.DataFrame(
        {
            "ลำดับ": range(1, len(NACC_DEPARTMENTS) + 1),
            "สำนัก/หน่วยงาน": NACC_DEPARTMENTS,
        }
    )
)

st.subheader("จุดจอด")
render_dataframe(
    pd.DataFrame(
        {
            "ลำดับ": range(1, len(PARKING_LOCATIONS) + 1),
            "จุดจอด": PARKING_LOCATIONS,
        }
    )
)

st.subheader("ตรวจสุขภาพข้อมูล")
requests = read_sheet("Requests")
dates = read_sheet("Request_Dates")
tasks = read_sheet("Guard_Tasks")

request_ids = set(requests["request_id"].astype(str)) if not requests.empty else set()
orphan_dates = dates[~dates["request_id"].astype(str).isin(request_ids)] if not dates.empty else dates
orphan_tasks = tasks[~tasks["request_id"].astype(str).isin(request_ids)] if not tasks.empty else tasks
cancelled_request_ids = set(requests[requests["status"] == "cancelled"]["request_id"].astype(str)) if not requests.empty else set()
active_tasks_under_cancelled = tasks[
    tasks["request_id"].astype(str).isin(cancelled_request_ids)
    & ~tasks["status"].astype(str).isin(["cancelled", "done"])
] if not tasks.empty else tasks

col1, col2, col3 = st.columns(3)
col1.metric("วันที่ไม่มีคำขอแม่", len(orphan_dates))
col2.metric("งานไม่มีคำขอแม่", len(orphan_tasks))
col3.metric("ยกเลิกแล้วแต่งานยังเปิด", len(active_tasks_under_cancelled))

with st.expander("รายละเอียดข้อมูลที่ควรตรวจ"):
    render_dataframe(
        orphan_dates,
        ["request_date_id", "request_id", "parking_date", "status"],
        worksheet="Request_Dates",
        empty_text="ไม่พบวันที่กำพร้า",
    )
    render_dataframe(
        orphan_tasks,
        ["task_id", "request_id", "parking_date", "status"],
        worksheet="Guard_Tasks",
        status_kind="guard",
        empty_text="ไม่พบงานกำพร้า",
    )
    render_dataframe(
        active_tasks_under_cancelled,
        ["task_id", "request_id", "parking_date", "status"],
        worksheet="Guard_Tasks",
        status_kind="guard",
        empty_text="ไม่พบงานที่ยังเปิดใต้คำขอยกเลิก",
    )
