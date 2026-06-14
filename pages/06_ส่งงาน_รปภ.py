import streamlit as st

from modules.db import submit_guard_task
from modules.pdf_generator import build_parking_pdf
from modules.sheets import get_request_by_id, list_vehicles, read_sheet
from modules.storage import upload_file
from modules.ui import inject_global_css, render_key_value_table, render_page_title
from modules.validators import validate_guard_submission


st.set_page_config(page_title="ส่งงาน รปภ.", page_icon="icon.svg", layout="wide")
inject_global_css()
render_page_title("ส่งงาน รปภ.", "เลือกงาน ตรวจรายละเอียด แล้วส่งรูปยืนยัน")

tasks = read_sheet("Guard_Tasks")
open_tasks = tasks[tasks["status"].isin(["pending", "in_progress", "submitted"])] if not tasks.empty else tasks
if open_tasks.empty:
    st.info("ยังไม่มีงานที่เปิดให้ส่ง")
    st.stop()

task_id = st.selectbox("เลือกงาน", open_tasks["task_id"].tolist())
task = open_tasks[open_tasks["task_id"] == task_id].iloc[0].to_dict()
request = get_request_by_id(task["request_id"])
if not request:
    st.error("ไม่พบคำขอของงานนี้")
    st.stop()

render_key_value_table(
    [
        ("สำนัก/หน่วยงาน", request["source_agency"]),
        ("เลขหนังสือ", request["book_no"]),
        ("วันที่ปฏิบัติงาน", task["parking_date"]),
        ("จุดจอด", request["parking_location"]),
        ("จำนวนรถ", request["car_count"]),
    ]
)

plates = list_vehicles(request["request_id"])["plate_no"].tolist()
pdf_bytes = build_parking_pdf(
    agency=request["source_agency"],
    car_count=int(request["car_count"]),
    plates=plates,
    parking_location=request["parking_location"],
    parking_date=task["parking_date"],
    book_no=request["book_no"],
)
st.download_button("ดาวน์โหลด PDF ป้าย", pdf_bytes, f"parking_sign_{task_id}.pdf", "application/pdf")

st.info("อัปโหลด 2 รูป: รูปใกล้ให้เห็นกรวย/กระดาษชัด และรูปไกลให้เห็นบริเวณจอดโดยรวม")

with st.form("guard_submission"):
    near_photo = st.file_uploader("รูปใกล้ *", type=["png", "jpg", "jpeg"])
    far_photo = st.file_uploader("รูปไกล *", type=["png", "jpg", "jpeg"])
    extra_photo = st.file_uploader("รูปเสริม", type=["png", "jpg", "jpeg"])
    note = st.text_area("รายละเอียดเพิ่มเติม")
    submitted_by = st.text_input("ผู้ส่งงาน", value="รปภ.")
    confirmed = st.checkbox("ยืนยันว่าภาพถ่ายถูกต้องและต้องการส่งงานนี้")
    submitted = st.form_submit_button("ส่งงาน", type="primary")

if submitted:
    ok, message = validate_guard_submission(near_photo, far_photo)
    if not ok:
        st.error(message)
    elif not confirmed:
        st.error("กรุณายืนยันก่อนส่งงาน")
    else:
        near_meta = upload_file(near_photo, "guard_submissions", f"{task_id}_near")
        far_meta = upload_file(far_photo, "guard_submissions", f"{task_id}_far")
        extra_meta = upload_file(extra_photo, "guard_submissions", f"{task_id}_extra") if extra_photo else None
        submission_id = submit_guard_task(
            task_id=task_id,
            near_photo_meta=near_meta,
            far_photo_meta=far_meta,
            extra_photo_meta=extra_meta,
            note=note,
            submitted_by=submitted_by,
        )
        st.success(f"ส่งงานสำเร็จ: {submission_id}")
