from __future__ import annotations

import streamlit as st

from modules.auth import ROLE_ADMIN, ROLE_OFFICER, get_current_role, require_role
from modules.constants import NACC_DEPARTMENTS, PARKING_LOCATIONS
from modules.dates import expand_date_range, parse_multiline_dates, to_iso_date
from modules.db import create_request
from modules.guard_packages import summarize_dates
from modules.locks import begin_action_lock, end_action_lock, is_action_locked
from modules.storage import upload_file
from modules.ui import inject_global_css, render_key_value_table, render_page_title
from modules.validators import (
    OTHER_LABEL,
    validate_book_no,
    validate_car_count,
    validate_location,
    validate_parking_dates,
    validate_plates,
)


st.set_page_config(page_title="บันทึกหนังสือ", page_icon="icon.svg", layout="wide")
inject_global_css()
require_role([ROLE_OFFICER, ROLE_ADMIN], "new_request")
render_page_title("บันทึกหนังสือ", "กรอกเท่าที่จำเป็น ระบบสร้างงาน รปภ. หนึ่งงานต่อคำขอ")

if is_action_locked("create_request"):
    st.info("ระบบกำลังดำเนินการอยู่ กรุณารอสักครู่")

st.subheader("ข้อมูลหนังสือและที่จอด")
col1, col2 = st.columns(2)
book_no = col1.text_input("เลขหนังสือ *", placeholder="เช่น ปช 0001/1234")
received_date = col1.date_input("วันที่รับเรื่อง *")
book_date = col2.date_input("วันที่หนังสือ", value=None)
source_agency = col2.selectbox("สำนัก/หน่วยงาน *", NACC_DEPARTMENTS)
other_agency = ""
if source_agency == OTHER_LABEL:
    other_agency = st.text_input("ระบุสำนัก/หน่วยงาน")

col3, col4 = st.columns(2)
car_count = col3.number_input("จำนวนรถ *", min_value=1, value=1, step=1)
selected_location = col4.selectbox("จุดจอด *", PARKING_LOCATIONS)
other_location = ""
if selected_location == OTHER_LABEL:
    other_location = st.text_input("ระบุจุดจอดอื่นๆ")
parking_time = st.text_input("เวลาที่จอด ถ้ามี", placeholder="เช่น 08:30-16:30")

st.subheader("วันที่จอดและทะเบียน")
multi_day = st.checkbox("จอดมากกว่า 1 วัน", value=False)
parking_dates: list[str] = []
if multi_day:
    date_col1, date_col2, date_col3 = st.columns([1, 1, 1])
    start_date = date_col1.date_input("วันที่เริ่ม")
    end_date = date_col2.date_input("วันที่สิ้นสุด")
    include_weekends = date_col3.checkbox("รวมเสาร์-อาทิตย์", value=True)
    try:
        parking_dates = expand_date_range(start_date, end_date, include_weekends=include_weekends)
    except ValueError as exc:
        st.warning(str(exc))
else:
    single_date = st.date_input("วันที่จอด")
    parking_dates = [to_iso_date(single_date)]

with st.expander("ระบุวันที่เอง"):
    manual_dates = st.text_area("วันที่จอดหลายวัน", placeholder="2026-06-30\n2026-07-01")
    if manual_dates.strip():
        try:
            parking_dates = parse_multiline_dates(manual_dates)
        except ValueError as exc:
            st.warning(f"รูปแบบวันที่ไม่ถูกต้อง: {exc}")

if parking_dates:
    st.caption("วันที่จอด: " + summarize_dates(parking_dates))

has_plates = st.checkbox("มีทะเบียนรถ", value=False)
plate_text = ""
if has_plates:
    plate_text = st.text_area("ใส่ทะเบียน บรรทัดละ 1 คัน", placeholder="กข 1234\nTEST1")
    st.caption("ตัวอย่าง: กข 1234 หรือ TEST1")

book_file = st.file_uploader("แนบไฟล์หนังสือ", type=["pdf", "png", "jpg", "jpeg"])
note = st.text_area("หมายเหตุคำขอ", placeholder="กรอกเฉพาะข้อมูลที่จำเป็นต่อการประสานงาน")
with st.expander("ข้อมูลเพิ่มเติม"):
    created_by = st.text_input("ผู้บันทึก", value="เจ้าหน้าที่")

final_agency = other_agency.strip() if source_agency == OTHER_LABEL else source_agency
final_location = other_location.strip() if selected_location == OTHER_LABEL else selected_location
plates = [line.strip() for line in plate_text.splitlines() if line.strip()] if has_plates else []

with st.expander("ตรวจสอบก่อนบันทึก", expanded=True):
    render_key_value_table(
        [
            ("เลขหนังสือ", book_no or "-"),
            ("สำนัก/หน่วยงาน", final_agency or "-"),
            ("วันที่จอด", summarize_dates(parking_dates)),
            ("เวลาที่จอด", parking_time or "-"),
            ("จำนวนรถ", str(car_count)),
            ("จุดจอด", final_location or "-"),
            ("ทะเบียนรถ", ", ".join(plates) if plates else "ไม่มีทะเบียน"),
        ]
    )

last_created = st.session_state.get("last_created_request")
if last_created:
    st.success(f"บันทึกเลขหนังสือ {last_created['book_no']} แล้ว")
    col_success1, col_success2, col_success3 = st.columns(3)
    if col_success1.button("เปิดรายละเอียด", use_container_width=True):
        st.session_state["selected_request_id"] = last_created["request_id"]
        st.switch_page("pages/04_รายละเอียดหนังสือ.py")
    if col_success2.button("บันทึกคำขอใหม่", use_container_width=True):
        st.session_state.pop("last_created_request", None)
        st.rerun()
    if col_success3.button("ไปงาน รปภ.", use_container_width=True):
        if get_current_role() == ROLE_ADMIN:
            st.session_state["selected_guard_request_id"] = last_created["request_id"]
            st.switch_page("pages/05_งาน_รปภ.py")
        else:
            st.session_state["selected_request_id"] = last_created["request_id"]
            st.switch_page("pages/04_รายละเอียดหนังสือ.py")

submitted = st.button("บันทึกคำขอ", type="primary", use_container_width=True)

if submitted:
    if not begin_action_lock("create_request"):
        st.warning("ระบบกำลังดำเนินการอยู่ กรุณารอสักครู่")
        st.stop()

    try:
        errors = []
        for ok, message in [
            validate_book_no(book_no),
            validate_car_count(car_count),
            validate_location(selected_location, other_location),
            validate_parking_dates(parking_dates),
        ]:
            if not ok:
                errors.append(message)
        if source_agency == OTHER_LABEL and not final_agency:
            errors.append("กรุณาระบุสำนัก/หน่วยงาน")
        if has_plates:
            ok, message = validate_plates(plates, int(car_count))
            if not ok:
                errors.append(message)

        if errors:
            for error in errors:
                st.error(error)
        else:
            with st.spinner("กำลังบันทึกข้อมูล... กรุณารอสักครู่"):
                file_meta = upload_file(book_file, "book_files", f"book_{book_no}") if book_file else None
                request_id = create_request(
                    book_no=book_no,
                    book_date=to_iso_date(book_date) if book_date else "",
                    received_date=to_iso_date(received_date),
                    source_agency=final_agency,
                    car_count=int(car_count),
                    parking_location=final_location,
                    parking_dates=parking_dates,
                    parking_time=parking_time,
                    plates=plates,
                    note=note,
                    book_file_meta=file_meta,
                    created_by=created_by,
                )
            st.session_state["last_created_request"] = {"request_id": request_id, "book_no": book_no}
            st.rerun()
    except Exception as exc:
        st.error(str(exc))
    finally:
        end_action_lock("create_request")
