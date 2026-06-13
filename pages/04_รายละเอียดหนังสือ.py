import streamlit as st

from modules.db import cancel_request, cancel_request_date, cancel_vehicle, mark_task_done
from modules.pdf_generator import build_parking_pdf
from modules.sheets import (
    get_request_by_id,
    list_guard_submissions,
    list_guard_tasks,
    list_request_dates,
    list_vehicles,
    read_sheet,
)
from modules.ui import inject_global_css, render_dataframe, render_page_title, render_status


st.set_page_config(page_title="รายละเอียดหนังสือ", page_icon="icon.svg", layout="wide")
inject_global_css()
render_page_title("รายละเอียดหนังสือ", "ตรวจสอบ แก้สถานะ ยกเลิก และดาวน์โหลด PDF")

requests = read_sheet("Requests")
if requests.empty:
    st.info("ยังไม่มีคำขอ")
    st.stop()

request_id = st.selectbox("เลือกคำขอ", requests["request_id"].tolist())
request = get_request_by_id(request_id)
if not request:
    st.error("ไม่พบคำขอ")
    st.stop()

col1, col2, col3 = st.columns([2, 1, 1])
col1.subheader(request["book_no"])
col1.write(request["source_agency"])
col2.metric("จำนวนรถ", request["car_count"])
with col3:
    render_status(request["status"])

st.write(f"จุดจอด: {request['parking_location']}")
if request.get("book_file_url"):
    st.link_button("เปิดไฟล์หนังสือ", request["book_file_url"])

dates = list_request_dates(request_id)
vehicles = list_vehicles(request_id, active_only=False)
active_plates = vehicles[vehicles["status"] == "active"]["plate_no"].tolist() if not vehicles.empty else []
tasks = list_guard_tasks(request_id)

st.subheader("วันที่จอด")
render_dataframe(dates)

st.subheader("ทะเบียนรถ")
render_dataframe(vehicles)

st.subheader("งาน รปภ.")
render_dataframe(tasks)

if not tasks.empty:
    selected_task = st.selectbox("เลือกงานสำหรับ PDF/ตรวจงาน", tasks["task_id"].tolist())
    task_row = tasks[tasks["task_id"] == selected_task].iloc[0]
    pdf_bytes = build_parking_pdf(
        agency=request["source_agency"],
        car_count=int(request["car_count"]),
        plates=active_plates,
        parking_location=request["parking_location"],
        parking_date=task_row["parking_date"],
        book_no=request["book_no"],
    )
    st.download_button(
        "ดาวน์โหลด PDF ป้าย",
        pdf_bytes,
        file_name=f"parking_sign_{request_id}_{task_row['parking_date']}.pdf",
        mime="application/pdf",
    )
    if st.button("ปิดงานหลังตรวจรูปแล้ว"):
        mark_task_done(selected_task, user="เจ้าหน้าที่")
        st.success("ปิดงานแล้ว")
        st.rerun()

st.subheader("รูปส่งงาน")
submissions = list_guard_submissions()
request_submissions = submissions[submissions["request_id"].astype(str) == request_id] if not submissions.empty else submissions
render_dataframe(request_submissions)

with st.expander("ยกเลิกข้อมูล"):
    reason = st.text_area("เหตุผลยกเลิก")
    user = st.text_input("ผู้ดำเนินการ", value="เจ้าหน้าที่")
    if st.button("ยกเลิกคำขอทั้งหมด", type="primary", disabled=not reason.strip()):
        cancel_request(request_id, reason, user=user)
        st.success("ยกเลิกคำขอแล้ว")
        st.rerun()

    if not dates.empty:
        date_id = st.selectbox("ยกเลิกเฉพาะวันที่", dates["request_date_id"].tolist())
        if st.button("ยกเลิกวันที่นี้", disabled=not reason.strip()):
            cancel_request_date(date_id, reason, user=user)
            st.success("ยกเลิกวันที่แล้ว")
            st.rerun()

    if not vehicles.empty:
        vehicle_id = st.selectbox("ยกเลิกทะเบียน", vehicles["vehicle_id"].tolist())
        if st.button("ยกเลิกทะเบียนนี้", disabled=not reason.strip()):
            cancel_vehicle(vehicle_id, reason, user=user)
            st.success("ยกเลิกทะเบียนแล้ว")
            st.rerun()
