import streamlit as st

from modules.constants import NACC_DEPARTMENTS, PARKING_LOCATIONS
from modules.dates import expand_date_range, parse_multiline_dates, to_iso_date
from modules.db import create_request
from modules.storage import upload_file
from modules.ui import inject_global_css, render_page_title
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
render_page_title("บันทึกหนังสือ", "กรอกครั้งเดียว ระบบสร้างวันที่จอดและงาน รปภ. ให้พร้อมติดตาม")

if "plate_count" not in st.session_state:
    st.session_state.plate_count = 1

with st.form("create_request_form", clear_on_submit=False):
    st.subheader("1. ข้อมูลหนังสือ")
    col1, col2 = st.columns([1, 1])
    book_no = col1.text_input("เลขหนังสือ *")
    book_date = col2.date_input("วันที่หนังสือ", value=None)
    received_date = col1.date_input("วันที่รับเรื่อง *")
    source_agency = col2.selectbox("สำนัก/หน่วยงาน *", NACC_DEPARTMENTS)
    other_agency = ""
    if source_agency == OTHER_LABEL:
        other_agency = st.text_input("ระบุสำนัก/หน่วยงาน")
    book_file = st.file_uploader("แนบไฟล์หนังสือ", type=["pdf", "png", "jpg", "jpeg"])

    st.subheader("2. รายละเอียดที่จอด")
    col3, col4 = st.columns(2)
    car_count = col3.number_input("จำนวนรถ *", min_value=1, value=1, step=1)
    selected_location = col4.selectbox("จุดจอด *", PARKING_LOCATIONS)
    other_location = ""
    if selected_location == OTHER_LABEL:
        other_location = st.text_input("ระบุจุดจอดอื่นๆ")
    parking_time = st.text_input("เวลาที่จอด ถ้ามี", placeholder="เช่น 08:30-16:30")

    mode = st.radio("เลือกวิธีระบุวันที่", ["วันที่เดียว", "ช่วงวันที่", "ระบุหลายวันเอง"], horizontal=True)
    parking_dates: list[str] = []
    if mode == "วันที่เดียว":
        single_date = st.date_input("วันที่จอด")
        parking_dates = [to_iso_date(single_date)]
    elif mode == "ช่วงวันที่":
        start_date = st.date_input("วันที่เริ่ม")
        end_date = st.date_input("วันที่สิ้นสุด")
        include_weekends = st.checkbox("รวมเสาร์-อาทิตย์", value=True)
        try:
            parking_dates = expand_date_range(start_date, end_date, include_weekends=include_weekends)
        except ValueError as exc:
            st.warning(str(exc))
    else:
        manual_dates = st.text_area("วันที่จอดหลายวัน", placeholder="2026-06-30\n2026-07-01\n01/07/2026")
        try:
            parking_dates = parse_multiline_dates(manual_dates)
        except ValueError as exc:
            st.warning(f"รูปแบบวันที่ไม่ถูกต้อง: {exc}")

    if parking_dates:
        st.caption("วันที่จอด: " + ", ".join(parking_dates))

    st.subheader("3. ทะเบียนและหมายเหตุ")
    has_plates = st.checkbox("มีทะเบียนรถ", value=False)
    plate_text = ""
    if has_plates:
        plate_text = st.text_area("ทะเบียนรถ 1 รายการต่อ 1 บรรทัด", placeholder="กข 1234\nขค 5678")

    note = st.text_area("หมายเหตุคำขอ", placeholder="กรอกเฉพาะข้อมูลที่จำเป็นต่อการประสานงาน")
    with st.expander("ข้อมูลผู้บันทึก"):
        created_by = st.text_input("ผู้บันทึก", value="เจ้าหน้าที่")
    submitted = st.form_submit_button("บันทึกคำขอ", type="primary")

if submitted:
    errors = []
    final_agency = other_agency.strip() if source_agency == OTHER_LABEL else source_agency
    final_location = other_location.strip() if selected_location == OTHER_LABEL else selected_location
    plates = [line.strip() for line in plate_text.splitlines() if line.strip()] if has_plates else []

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
        try:
            file_meta = upload_file(book_file, "book_files", "book") if book_file else None
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
            st.success(f"บันทึกสำเร็จ: {request_id}")
        except Exception as exc:
            st.error(str(exc))
