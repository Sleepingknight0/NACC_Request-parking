import pandas as pd
import streamlit as st

from modules.auth import ROLE_ADMIN, require_role
from modules.constants import (
    NACC_DEPARTMENTS,
    PARKING_LOCATIONS,
    WORKSHEET_HEADER_LABELS,
    WORKSHEET_SCHEMAS,
    sheet_title_for,
)
from modules.db import cancel_request, repair_guard_task_packages
from modules.sheets import initialize_storage, normalize_all_worksheets, read_sheet, validate_storage_schema
from modules.ui import inject_global_css, is_local_upload_url, render_dataframe, render_page_title


st.set_page_config(page_title="ตั้งค่า", page_icon="icon.svg", layout="wide")
inject_global_css()
require_role([ROLE_ADMIN], "settings")
render_page_title("ตั้งค่า", "ตรวจฐานข้อมูลและข้อมูลอ้างอิงที่ใช้ในระบบ")

initialize_storage()

st.subheader("เครื่องมือซ่อมระบบ")
tool_col1, tool_col2, tool_col3 = st.columns(3)
if tool_col1.button("ปรับฐานข้อมูลให้เป็นภาษาไทย", type="primary", use_container_width=True):
    with st.spinner("กำลังปรับฐานข้อมูล..."):
        normalize_all_worksheets()
    st.success("ปรับหัวตาราง สถานะ ค่าใช่/ไม่ใช่ และรูปแบบวันที่แล้ว")

if tool_col2.button("ซ่อมรูปแบบวันที่ในฐานข้อมูล", use_container_width=True):
    with st.spinner("กำลังซ่อมรูปแบบวันที่..."):
        normalize_all_worksheets()
    st.success("ซ่อมวันที่และเดือนรายงานเป็นรูปแบบ YYYY-MM-DD / YYYY-MM แล้ว")

if tool_col3.button("รวมงาน รปภ. ตามเลขหนังสือ", use_container_width=True):
    with st.spinner("กำลังเติมข้อมูล package ของงาน รปภ...."):
        repaired = repair_guard_task_packages(user="แอดมิน")
    st.success(f"ปรับข้อมูลสรุปงาน รปภ. แล้ว {repaired} แถว")

schema_problems = validate_storage_schema()
with st.expander("ตรวจ schema"):
    if not schema_problems:
        st.success("schema ภายในอ่านได้ครบทุก worksheet")
    else:
        for worksheet, missing in schema_problems.items():
            st.error(f"{sheet_title_for(worksheet)} ขาดคอลัมน์: {', '.join(missing)}")

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
attachments = read_sheet("Attachments")

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

st.subheader("ตรวจไฟล์แนบ")
local_attachment_rows = attachments[
    attachments["file_url"].astype(str).map(is_local_upload_url)
] if not attachments.empty else attachments
local_request_files = requests[
    requests["book_file_url"].astype(str).map(is_local_upload_url)
] if not requests.empty else requests
st.caption("Production ควรใช้ Google Drive หรือ Cloud Storage สำหรับไฟล์แนบ")
col_file1, col_file2 = st.columns(2)
col_file1.metric("ไฟล์แนบชั่วคราว", len(local_attachment_rows))
col_file2.metric("ไฟล์หนังสือชั่วคราว", len(local_request_files))
with st.expander("รายการไฟล์ที่ยังไม่ใช่ลิงก์ถาวร"):
    render_dataframe(
        local_attachment_rows,
        ["request_id", "task_id", "file_type", "file_name", "file_url", "uploaded_at"],
        worksheet="Attachments",
        empty_text="ไม่พบไฟล์แนบชั่วคราว",
    )
    render_dataframe(
        local_request_files,
        ["book_no", "source_agency", "book_file_url", "created_at"],
        worksheet="Requests",
        empty_text="ไม่พบไฟล์หนังสือชั่วคราว",
    )

st.subheader("QA cleanup")
qa_rows = requests[
    requests["book_no"].astype(str).str.startswith("QA-PROD-")
    & (requests["status"].astype(str) != "cancelled")
] if not requests.empty else requests
st.metric("QA rows ที่ยังไม่ยกเลิก", len(qa_rows))
with st.expander("ยกเลิกข้อมูลทดสอบ QA-PROD"):
    render_dataframe(
        qa_rows,
        ["book_no", "received_date", "source_agency", "parking_location", "status"],
        worksheet="Requests",
        empty_text="ไม่มี QA row ที่ต้อง cleanup",
    )
    if not qa_rows.empty and st.button("ยกเลิก QA rows ทั้งหมด", type="primary"):
        with st.spinner("กำลังยกเลิกข้อมูลทดสอบ..."):
            for _, row in qa_rows.iterrows():
                cancel_request(row["request_id"], "QA cleanup", user="แอดมิน")
        st.success("ยกเลิก QA rows แล้ว")
        st.rerun()
