from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.auth import ROLE_ADMIN, ROLE_GUARD, get_current_role, require_role
from modules.db import submit_guard_package
from modules.guard_packages import build_guard_packages, get_guard_package
from modules.locks import begin_action_lock, end_action_lock
from modules.pdf_generator import build_parking_pdf
from modules.sheets import read_sheet
from modules.storage import upload_file
from modules.ui import inject_global_css, render_key_value_table, render_page_title, safe_download_filename, status_badge
from modules.validators import validate_guard_submission


st.set_page_config(page_title="ส่งงาน รปภ.", page_icon="icon.svg", layout="wide")
inject_global_css()
require_role([ROLE_GUARD, ROLE_ADMIN], "guard_submit")

query_request_id = st.query_params.get("request_id", "")
query_task_id = st.query_params.get("task_id", "")
if isinstance(query_request_id, list):
    query_request_id = query_request_id[0] if query_request_id else ""
if isinstance(query_task_id, list):
    query_task_id = query_task_id[0] if query_task_id else ""

request_id = str(query_request_id or st.session_state.get("selected_guard_request_id", "")).strip()
if not request_id and query_task_id:
    package_from_task = get_guard_package(task_id=str(query_task_id).strip())
    request_id = str((package_from_task or {}).get("request_id", ""))

with st.spinner("กำลังโหลดข้อมูล..."):
    packages = build_guard_packages(include_cancelled=False)
    vehicles = read_sheet("Vehicles")

if not request_id:
    render_page_title("ส่งงาน รปภ.", "เลือกงานจากเลขหนังสือ แล้วอัปโหลดรูปใกล้และรูปไกล")
    open_packages = packages[
        packages["status"].isin(["pending", "in_progress"])
        & packages["is_open"].astype(bool)
    ] if not packages.empty else packages
    if open_packages.empty:
        st.info("ยังไม่มีงานที่เปิดให้ส่ง")
        st.stop()
    for _, row in open_packages.sort_values(["parking_date", "book_no"]).iterrows():
        with st.container(border=True):
            st.markdown(f"### เลขหนังสือ {row['book_no']}")
            st.markdown(status_badge(row["status"], "guard"), unsafe_allow_html=True)
            st.write(f"**สำนัก/หน่วยงาน:** {row['source_agency']}")
            st.write(f"**วันที่จอด:** {row['date_summary']}")
            st.write(f"**จุดจอด:** {row['parking_location']} | **จำนวนรถ:** {row['car_count']}")
            if st.button("ส่งงานนี้", key=f"choose_submit_{row['request_id']}", use_container_width=True):
                st.session_state["selected_guard_request_id"] = str(row["request_id"])
                st.rerun()
    st.stop()

package = get_guard_package(request_id=request_id)
if not package:
    render_page_title("ส่งงาน รปภ.", "ไม่พบงาน")
    st.error("ไม่พบงาน รปภ. ของคำขอนี้")
    st.stop()

plates = []
if not vehicles.empty:
    plates = vehicles[
        (vehicles["request_id"].astype(str) == str(request_id))
        & (vehicles["status"].astype(str) != "cancelled")
    ]["plate_no"].astype(str).tolist()

render_page_title(f"ส่งงาน: เลขหนังสือ {package['book_no']}", str(package["source_agency"]))
st.markdown(status_badge(package["status"], "guard"), unsafe_allow_html=True)
render_key_value_table(
    [
        ("สำนัก/หน่วยงาน", package["source_agency"]),
        ("วันที่จอด", package["date_summary"]),
        ("เวลา", package.get("parking_time") or "-"),
        ("จุดจอด", package["parking_location"]),
        ("จำนวนรถ", str(package["car_count"])),
        ("ทะเบียนรถ", ", ".join(plates) if plates else "ไม่มีทะเบียน"),
    ]
)

car_count_value = pd.to_numeric(package["car_count"], errors="coerce")
pdf_bytes = build_parking_pdf(
    agency=package["source_agency"],
    car_count=int(car_count_value) if pd.notna(car_count_value) else 1,
    plates=plates,
    parking_location=package["parking_location"],
    date_summary=package["date_summary"],
    parking_time=package.get("parking_time", ""),
    book_no=package["book_no"],
)
st.download_button(
    "ดาวน์โหลด PDF ป้าย",
    pdf_bytes,
    safe_download_filename("parking_sign", package["book_no"], "pdf"),
    "application/pdf",
    use_container_width=True,
)

if package["status"] == "done":
    st.info("งานนี้ปิดแล้ว")
    if st.button("กลับไปงาน รปภ.", use_container_width=True):
        st.switch_page("pages/05_งาน_รปภ.py")
    st.stop()
if package["status"] == "cancelled":
    st.warning("งานนี้ถูกยกเลิก")
    if st.button("กลับไปงาน รปภ.", use_container_width=True):
        st.switch_page("pages/05_งาน_รปภ.py")
    st.stop()
if package["status"] == "submitted":
    st.info("งานนี้ส่งแล้ว รอเจ้าหน้าที่ตรวจ")
    if st.button("กลับไปงาน รปภ.", use_container_width=True):
        st.switch_page("pages/05_งาน_รปภ.py")
    st.stop()
if package["status"] == "pending" and not bool(package.get("is_open", False)):
    st.warning(f"ยังไม่ถึงวันทำงาน เปิดให้ทำวันที่ {package.get('open_date') or '-'}")
    if st.button("กลับไปงาน รปภ.", use_container_width=True):
        st.switch_page("pages/05_งาน_รปภ.py")
    st.stop()

st.info("อัปโหลดรูปใกล้และรูปไกลก่อนส่งงาน")
near_photo = st.file_uploader("รูปใกล้ *", type=["png", "jpg", "jpeg"], key=f"{request_id}_near", help="เห็นกรวย/กระดาษชัด")
far_photo = st.file_uploader("รูปไกล *", type=["png", "jpg", "jpeg"], key=f"{request_id}_far", help="เห็นตำแหน่งจอดโดยรวม")
extra_photo = st.file_uploader("รูปเสริม", type=["png", "jpg", "jpeg"], key=f"{request_id}_extra")
note = st.text_area("หมายเหตุเพิ่มเติม")
submitted_by = st.text_input("ผู้ส่งงาน", value="รปภ.")
confirmed = st.checkbox("ยืนยันว่ารูปถูกต้องและต้องการส่งงาน")

submitted = st.button("ส่งงาน", type="primary", use_container_width=True)
if submitted:
    if not confirmed:
        st.error("กรุณายืนยันก่อนส่งงาน")
    else:
        ok, message = validate_guard_submission(near_photo, far_photo)
        if not ok:
            st.error(message)
        elif not begin_action_lock(f"submit_{request_id}"):
            st.warning("ระบบกำลังส่งงาน กรุณารอสักครู่")
            st.stop()
        else:
            try:
                with st.spinner("กำลังส่งงาน... กรุณารอสักครู่"):
                    book_prefix = package.get("book_no") or request_id
                    near_meta = upload_file(near_photo, "guard_submissions", f"guard_{book_prefix}_near")
                    far_meta = upload_file(far_photo, "guard_submissions", f"guard_{book_prefix}_far")
                    extra_meta = upload_file(extra_photo, "guard_submissions", f"guard_{book_prefix}_extra") if extra_photo else None
                    submit_guard_package(
                        request_id=request_id,
                        near_photo_meta=near_meta,
                        far_photo_meta=far_meta,
                        extra_photo_meta=extra_meta,
                        note=note,
                        submitted_by=submitted_by,
                    )
                st.success("ส่งงานแล้ว รอเจ้าหน้าที่ตรวจ")
                if get_current_role() == ROLE_ADMIN:
                    col1, col2 = st.columns(2)
                    if col1.button("กลับไปงาน รปภ.", use_container_width=True):
                        st.switch_page("pages/05_งาน_รปภ.py")
                    if col2.button("เปิดรายละเอียดหนังสือ", use_container_width=True):
                        st.session_state["selected_request_id"] = request_id
                        st.switch_page("pages/04_รายละเอียดหนังสือ.py")
                else:
                    if st.button("กลับไปงาน รปภ.", use_container_width=True):
                        st.switch_page("pages/05_งาน_รปภ.py")
            except Exception as exc:
                st.error(str(exc))
            finally:
                end_action_lock(f"submit_{request_id}")
