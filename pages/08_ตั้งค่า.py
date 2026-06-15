import importlib

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
from modules.audit import write_audit_log
from modules.db import cancel_requests, repair_guard_task_packages
from modules.drive_preview import load_drive_file_for_preview, render_drive_image_preview
from modules.sheets import initialize_storage, normalize_all_worksheets, read_sheet, validate_storage_schema
import modules.storage as storage

storage = importlib.reload(storage)
from modules.storage import check_drive_connection, check_drive_write_access, get_drive_config_status, get_service_account_email, is_drive_url
from modules.ui import inject_global_css, is_local_upload_url, render_dataframe, render_page_title


st.set_page_config(page_title="ตั้งค่า", page_icon="icon.svg", layout="wide")
inject_global_css()
require_role([ROLE_ADMIN], "settings")
render_page_title("ตั้งค่า", "ตรวจฐานข้อมูลและข้อมูลอ้างอิงที่ใช้ในระบบ")

initialize_storage()

st.subheader("สถานะที่เก็บไฟล์")
storage_status = get_drive_config_status()
status_col1, status_col2, status_col3 = st.columns(3)
status_col1.metric("file_storage_backend", storage_status["file_storage_backend"])
status_col2.metric("drive_auth_mode", storage_status["drive_auth_mode"])
status_col3.metric("share_uploaded_files", "true" if storage_status["share_uploaded_files"] else "false")
st.caption(f"OAuth Drive: {'ตั้งค่าแล้ว' if storage_status['oauth_configured'] else 'ยังไม่ตั้งค่า'}")
st.caption(f"root_folder_id: {'ตั้งค่าแล้ว' if storage_status['root_folder_configured'] else 'ยังไม่ตั้งค่า'}")
service_account_email = get_service_account_email()
if service_account_email and storage_status["drive_auth_mode"] == "service_account":
    st.caption(f"Service account: {service_account_email}")

folder_status_rows = pd.DataFrame(
    {
        "folder": list(storage_status["folder_configured"].keys()),
        "configured": ["ตั้งค่าแล้ว" if value else "ยังไม่ตั้งค่า" for value in storage_status["folder_configured"].values()],
    }
)
render_dataframe(folder_status_rows, empty_text="ไม่มีข้อมูลโฟลเดอร์")

if st.button("ตรวจการเชื่อมต่อ Google Drive", use_container_width=True):
    with st.spinner("กำลังตรวจ Google Drive..."):
        drive_check = check_drive_connection()
    if drive_check.get("ok"):
        st.success(f"เชื่อมต่อ Google Drive ได้: {drive_check.get('root_name') or 'folder พร้อมใช้งาน'}")
        if not drive_check.get("root_upload_ready", True):
            st.warning("อ่านโฟลเดอร์ได้ แต่ยังไม่พร้อมอัปโหลด production ถ้าโฟลเดอร์ยังอยู่ใน My Drive ต้องใช้ Google Shared Drive")
        folder_rows = pd.DataFrame(
            [
                {
                    "folder": key,
                    "configured": "ตั้งค่าแล้ว" if result.get("configured") else "ยังไม่ตั้งค่า",
                    "status": "อ่านได้" if result.get("ok") else "ไม่ได้ตรวจ",
                    "name": result.get("name", ""),
                    "location": result.get("storage_location", ""),
                    "upload_ready": "พร้อม" if result.get("upload_ready") else "ยังไม่พร้อม",
                }
                for key, result in drive_check.get("folders", {}).items()
            ]
        )
        render_dataframe(folder_rows, empty_text="ไม่มี folder เฉพาะที่ตั้งค่าไว้")
    else:
        st.error("เชื่อมต่อ Google Drive ไม่สำเร็จ")
        with st.expander("รายละเอียดสำหรับผู้ดูแล"):
            st.code(str(drive_check.get("error", "")))

write_check_folder = st.selectbox(
    "โฟลเดอร์สำหรับตรวจสิทธิ์อัปโหลด",
    ["book_files", "guard_submissions"],
    format_func=lambda value: {
        "book_files": "book_files - หนังสือผู้ขอที่จอด",
        "guard_submissions": "guard_submissions - รูปส่งงาน รปภ.",
    }.get(value, value),
)
if st.button("ตรวจสิทธิ์อัปโหลด Google Drive", use_container_width=True):
    with st.spinner("กำลังตรวจสิทธิ์อัปโหลด Google Drive..."):
        write_check = check_drive_write_access(write_check_folder)
    if write_check.get("ok"):
        st.success(f"อัปโหลดไฟล์ทดสอบได้: {write_check.get('file_name')}")
        if write_check.get("trashed"):
            st.caption("ลบไฟล์ทดสอบเข้าถังขยะแล้ว")
        else:
            st.warning("อัปโหลดได้ แต่ยังลบไฟล์ทดสอบเข้าถังขยะไม่สำเร็จ")
    else:
        st.error(f"อัปโหลดไฟล์ทดสอบไป Google Drive ไม่สำเร็จ: {write_check.get('error', '')}")
        with st.expander("รายละเอียดสำหรับผู้ดูแล"):
            st.code(str(write_check.get("technical_error") or write_check.get("error") or ""))

st.subheader("เครื่องมือซ่อมระบบ")
confirm_repair = st.checkbox("ยืนยันการเขียนข้อมูลสำหรับเครื่องมือซ่อมระบบ")
tool_col1, tool_col2, tool_col3 = st.columns(3)
if tool_col1.button("ปรับฐานข้อมูลให้เป็นภาษาไทย", type="primary", use_container_width=True, disabled=not confirm_repair):
    with st.spinner("กำลังปรับฐานข้อมูล..."):
        normalize_all_worksheets()
        write_audit_log("normalize_worksheets", "all", "all", new_value={"tool": "thai_headers"}, user="แอดมิน")
    st.success("ปรับหัวตาราง สถานะ ค่าใช่/ไม่ใช่ และรูปแบบวันที่แล้ว")

if tool_col2.button("ซ่อมรูปแบบวันที่ในฐานข้อมูล", use_container_width=True, disabled=not confirm_repair):
    with st.spinner("กำลังซ่อมรูปแบบวันที่..."):
        normalize_all_worksheets()
        write_audit_log("repair_date_formats", "all", "all", new_value={"format": "YYYY-MM-DD/YYYY-MM"}, user="แอดมิน")
    st.success("ซ่อมวันที่และเดือนรายงานเป็นรูปแบบ YYYY-MM-DD / YYYY-MM แล้ว")

if tool_col3.button("รวมงาน รปภ. ตามเลขหนังสือ", use_container_width=True, disabled=not confirm_repair):
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
drive_attachment_rows = attachments[
    attachments["file_url"].astype(str).map(is_drive_url)
] if not attachments.empty else attachments
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

with st.expander("ตรวจรูปจาก Google Drive"):
    if drive_attachment_rows.empty:
        st.caption("ยังไม่มีไฟล์ Google Drive ให้ตรวจ")
    else:
        sample = drive_attachment_rows.iloc[0].to_dict()
        st.write(f"ไฟล์ตัวอย่าง: {sample.get('file_name') or '-'}")
        if st.button("ตรวจการแสดงรูปตัวอย่าง", use_container_width=True):
            with st.spinner("กำลังโหลดไฟล์จาก Google Drive..."):
                result = load_drive_file_for_preview(sample.get("file_url", ""))
            if result.get("ok"):
                st.success("โหลดไฟล์จาก Google Drive ได้")
                render_drive_image_preview(sample.get("file_url", ""), "ไฟล์ตัวอย่าง")
            else:
                st.error("โหลดไฟล์จาก Google Drive ไม่สำเร็จ")
                with st.expander("รายละเอียดสำหรับผู้ดูแล"):
                    st.code(str(result.get("error") or ""))

st.subheader("QA cleanup")
qa_rows = requests[
    requests["book_no"].astype(str).str.startswith("QA-PROD-")
    & (requests["status"].astype(str) != "cancelled")
] if not requests.empty else requests
st.metric("QA rows ที่ยังไม่ยกเลิก", len(qa_rows))
with st.expander("ยกเลิกข้อมูลทดสอบ QA-PROD"):
    confirm_qa_cleanup = st.checkbox("ยืนยันการยกเลิกข้อมูลทดสอบ production QA")
    render_dataframe(
        qa_rows,
        ["book_no", "received_date", "source_agency", "parking_location", "status"],
        worksheet="Requests",
        empty_text="ไม่มี QA row ที่ต้อง cleanup",
    )
    if not qa_rows.empty and st.button("ยกเลิก QA rows ทั้งหมด", type="primary", disabled=not confirm_qa_cleanup):
        with st.spinner("กำลังยกเลิกข้อมูลทดสอบ..."):
            cancelled_count = cancel_requests(
                qa_rows["request_id"].astype(str).tolist(),
                "ข้อมูลทดสอบ production QA",
                user="แอดมิน",
            )
        st.success(f"ยกเลิก QA rows แล้ว {cancelled_count} รายการ")
        st.rerun()
