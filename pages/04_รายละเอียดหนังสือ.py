from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.auth import ROLE_ADMIN, ROLE_OFFICER, ROLE_VIEWER, get_current_role, require_role
from modules.db import cancel_request, cancel_request_date, cancel_vehicle, mark_guard_package_done
from modules.guard_packages import build_guard_packages, get_guard_package, summarize_dates
from modules.locks import begin_action_lock, end_action_lock
from modules.pdf_generator import build_parking_pdf
from modules.sheets import (
    get_request_by_id,
    list_guard_submissions,
    list_guard_tasks,
    list_request_dates,
    list_vehicles,
    read_sheet,
)
from modules.ui import (
    inject_global_css,
    render_dataframe,
    render_key_value_table,
    render_page_title,
    render_system_info_expander,
    safe_file_link,
    status_badge,
)


st.set_page_config(page_title="รายละเอียดหนังสือ", page_icon="icon.svg", layout="wide")
inject_global_css()
require_role([ROLE_OFFICER, ROLE_ADMIN, ROLE_VIEWER], "request_detail")

requests = read_sheet("Requests")
if requests.empty:
    render_page_title("รายละเอียดหนังสือ", "ยังไม่มีคำขอในระบบ")
    st.info("ยังไม่มีคำขอ")
    st.stop()

query_request_id = st.query_params.get("request_id", "")
if isinstance(query_request_id, list):
    query_request_id = query_request_id[0] if query_request_id else ""

request_id = str(query_request_id or st.session_state.get("selected_request_id", "")).strip()
if not request_id:
    render_page_title("รายละเอียดหนังสือ", "ค้นหาด้วยเลขหนังสือก่อนเปิดรายละเอียด")
    query = st.text_input("ค้นหาเลขหนังสือ / สำนัก / ทะเบียน", placeholder="เลขหนังสือ, สำนัก/หน่วยงาน, ทะเบียน")
    vehicles_all = read_sheet("Vehicles")
    df = requests.copy()
    if query:
        plate_request_ids = (
            vehicles_all[vehicles_all["plate_no"].astype(str).str.contains(query, case=False, regex=False)]["request_id"].unique()
            if not vehicles_all.empty
            else []
        )
        df = df[
            df["book_no"].astype(str).str.contains(query, case=False, regex=False)
            | df["source_agency"].astype(str).str.contains(query, case=False, regex=False)
            | df["request_id"].astype(str).isin(plate_request_ids)
        ]
    for _, row in df.sort_values("updated_at", ascending=False).head(12).iterrows():
        with st.container(border=True):
            st.markdown(f"### เลขหนังสือ {row['book_no']}")
            st.write(f"**สำนัก/หน่วยงาน:** {row['source_agency']}")
            st.write(f"**จุดจอด:** {row['parking_location']} | **จำนวนรถ:** {row['car_count']}")
            st.markdown(status_badge(row["status"]), unsafe_allow_html=True)
            if st.button("เปิดรายละเอียด", key=f"detail_select_{row['request_id']}", use_container_width=True):
                st.session_state["selected_request_id"] = str(row["request_id"])
                st.rerun()
    st.stop()

request = get_request_by_id(request_id)
if not request:
    render_page_title("รายละเอียดหนังสือ", "ไม่พบคำขอ")
    st.error("ไม่พบคำขอ")
    st.stop()

dates = list_request_dates(request_id)
vehicles = list_vehicles(request_id, active_only=False)
active_vehicles = vehicles[vehicles["status"].astype(str) != "cancelled"] if not vehicles.empty else vehicles
active_plates = active_vehicles["plate_no"].astype(str).tolist() if not active_vehicles.empty else []
tasks = list_guard_tasks(request_id)
package = get_guard_package(request_id=request_id) or {}
submissions = list_guard_submissions()
request_submissions = submissions[submissions["request_id"].astype(str) == request_id] if not submissions.empty else submissions

active_dates = dates[dates["status"].astype(str) != "cancelled"] if not dates.empty else dates
dates_text = package.get("date_summary") or summarize_dates(active_dates["parking_date"].tolist() if not active_dates.empty else [])
parking_time = package.get("parking_time") or (
    active_dates["parking_time"].astype(str).replace("", pd.NA).dropna().iloc[0]
    if not active_dates.empty and "parking_time" in active_dates.columns and not active_dates["parking_time"].astype(str).replace("", pd.NA).dropna().empty
    else ""
)

render_page_title(f"เลขหนังสือ {request['book_no']}", str(request["source_agency"]))
st.markdown(status_badge(request["status"]), unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric("จำนวนรถ", request["car_count"])
col2.metric("จุดจอด", request["parking_location"])
col3.metric("วันที่จอด", dates_text)
col4.metric("งาน รปภ.", package.get("status", request.get("status", "")))

st.subheader("สรุปคำขอ")
render_key_value_table(
    [
        ("เลขหนังสือ", request["book_no"]),
        ("สำนัก/หน่วยงาน", request["source_agency"]),
        ("วันที่รับเรื่อง", request["received_date"]),
        ("วันที่หนังสือ", request.get("book_date", "") or "-"),
        ("จุดจอด", request["parking_location"]),
        ("จำนวนรถ", str(request["car_count"])),
        ("วันที่จอด", dates_text),
        ("เวลาที่จอด", parking_time or "-"),
        ("ทะเบียนรถ", ", ".join(active_plates) if active_plates else "ไม่มีทะเบียน"),
    ]
)

action_col1, action_col2 = st.columns(2)
with action_col1:
    safe_file_link(request.get("book_file_url"), "เปิดไฟล์หนังสือ")
with action_col2:
    car_count_value = pd.to_numeric(request["car_count"], errors="coerce")
    pdf_bytes = build_parking_pdf(
        agency=request["source_agency"],
        car_count=int(car_count_value) if pd.notna(car_count_value) else 1,
        plates=active_plates,
        parking_location=request["parking_location"],
        date_summary=dates_text,
        parking_time=parking_time,
        book_no=request["book_no"],
    )
    st.download_button(
        "ดาวน์โหลด PDF ป้าย",
        pdf_bytes,
        file_name=f"parking_sign_{request['book_no']}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

with st.expander("วันที่จอดทั้งหมด"):
    render_dataframe(
        dates,
        ["parking_date", "parking_time", "month_key", "status"],
        worksheet="Request_Dates",
        empty_text="ไม่มีวันที่จอด",
    )

with st.expander("ทะเบียนรถ"):
    render_dataframe(
        vehicles,
        ["plate_no", "vehicle_note", "status"],
        worksheet="Vehicles",
        empty_text="ไม่มีทะเบียนรถ",
    )

with st.expander("งาน รปภ."):
    render_dataframe(
        tasks,
        ["date_summary", "parking_date", "parking_location", "status", "submitted_at", "completed_at"],
        worksheet="Guard_Tasks",
        status_kind="guard",
        empty_text="ไม่มีงาน รปภ.",
    )

with st.expander("รูปส่งงาน"):
    if request_submissions.empty:
        st.caption("ยังไม่มีการส่งงาน")
    else:
        for _, row in request_submissions.sort_values("submitted_at", ascending=False).iterrows():
            st.write(f"**ส่งเมื่อ:** {row['submitted_at']} | **ผู้ส่ง:** {row['submitted_by'] or '-'}")
            link_col1, link_col2, link_col3 = st.columns(3)
            with link_col1:
                safe_file_link(row.get("near_photo_url"), "รูปใกล้")
            with link_col2:
                safe_file_link(row.get("far_photo_url"), "รูปไกล")
            with link_col3:
                safe_file_link(row.get("extra_photo_url"), "รูปเสริม")
            if row.get("note"):
                st.caption(row["note"])

if get_current_role() == ROLE_ADMIN:
    st.subheader("การดำเนินการแอดมิน")
    package_status = str(package.get("status", request.get("status", "")))
    if package_status == "done":
        st.info("งานนี้ปิดแล้ว")
    elif package_status == "cancelled":
        st.info("คำขอนี้ถูกยกเลิกแล้ว")
    elif st.button("ปิดงานหลังตรวจรูปแล้ว", type="primary", use_container_width=True):
        if not begin_action_lock(f"done_{request_id}"):
            st.warning("ระบบกำลังปิดงาน กรุณารอสักครู่")
            st.stop()
        try:
            with st.spinner("กำลังปิดงาน..."):
                mark_guard_package_done(request_id, user="แอดมิน")
            st.success("ปิดงานแล้ว")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))
        finally:
            end_action_lock(f"done_{request_id}")

    with st.expander("ยกเลิกข้อมูล"):
        st.warning("การยกเลิกจะไม่ลบข้อมูล แต่จะเปลี่ยนสถานะเป็นยกเลิกและบันทึกประวัติไว้")
        reason = st.text_area("เหตุผลยกเลิก")
        user = st.text_input("ผู้ดำเนินการ", value="แอดมิน")
        if st.button("ยกเลิกคำขอทั้งหมด", type="primary"):
            if not reason.strip():
                st.error("กรุณาระบุเหตุผลยกเลิก")
            elif begin_action_lock(f"cancel_request_{request_id}"):
                try:
                    with st.spinner("กำลังยกเลิกข้อมูล..."):
                        cancel_request(request_id, reason, user=user)
                    st.success("ยกเลิกคำขอแล้ว")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
                finally:
                    end_action_lock(f"cancel_request_{request_id}")

        if not dates.empty:
            date_options = dates["request_date_id"].tolist()
            date_id = st.selectbox(
                "ยกเลิกเฉพาะวันที่",
                date_options,
                format_func=lambda value: dates[dates["request_date_id"].astype(str) == str(value)].iloc[0]["parking_date"],
            )
            if st.button("ยกเลิกวันที่นี้"):
                if not reason.strip():
                    st.error("กรุณาระบุเหตุผลยกเลิก")
                else:
                    with st.spinner("กำลังยกเลิกข้อมูล..."):
                        cancel_request_date(date_id, reason, user=user)
                    st.success("ยกเลิกวันที่แล้ว")
                    st.rerun()

        if not vehicles.empty:
            vehicle_options = vehicles["vehicle_id"].tolist()
            vehicle_id = st.selectbox(
                "ยกเลิกทะเบียน",
                vehicle_options,
                format_func=lambda value: vehicles[vehicles["vehicle_id"].astype(str) == str(value)].iloc[0]["plate_no"],
            )
            if st.button("ยกเลิกทะเบียนนี้"):
                if not reason.strip():
                    st.error("กรุณาระบุเหตุผลยกเลิก")
                else:
                    with st.spinner("กำลังยกเลิกข้อมูล..."):
                        cancel_vehicle(vehicle_id, reason, user=user)
                    st.success("ยกเลิกทะเบียนแล้ว")
                    st.rerun()

with st.expander("ประวัติ"):
    audit = read_sheet("Audit_Log")
    request_audit = audit[audit["target_id"].astype(str).isin([request_id] + tasks.get("task_id", pd.Series(dtype=str)).astype(str).tolist())] if not audit.empty else audit
    render_dataframe(
        request_audit.sort_values("created_at", ascending=False) if not request_audit.empty else request_audit,
        ["created_at", "action", "target_table", "user"],
        worksheet="Audit_Log",
        empty_text="ยังไม่มีประวัติ",
    )

system_row = {**request, **package}
render_system_info_expander(system_row)
