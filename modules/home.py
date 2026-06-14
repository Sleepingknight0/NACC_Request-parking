from __future__ import annotations

import pandas as pd
import streamlit as st

from modules.auth import ROLE_ADMIN, ROLE_GUARD, ROLE_OFFICER, get_current_role, render_role_badge, render_role_selector
from modules.db import accept_guard_package, mark_guard_package_done
from modules.guard_packages import build_guard_packages
from modules.locks import begin_action_lock, end_action_lock
from modules.pdf_generator import build_parking_pdf
from modules.sheets import initialize_storage, read_sheet
from modules.ui import inject_global_css, render_action_grid, render_page_title, safe_download_filename, status_badge


def _metric_cards(values: list[tuple[str, int]]) -> None:
    cols = st.columns(min(len(values), 4) or 1)
    for index, (label, value) in enumerate(values):
        cols[index % len(cols)].metric(label, value)


def _show_flash() -> None:
    message = st.session_state.pop("flash_success", "")
    if message:
        st.success(message)


def _split_packages(packages) -> dict[str, object]:
    if packages.empty:
        return {
            "open": packages,
            "upcoming": packages,
            "submitted": packages,
            "done": packages,
            "cancelled": packages,
            "today": packages,
            "pending": packages,
        }

    today = pd.Timestamp.today().date().isoformat()
    active = packages[packages["status"].isin(["pending", "in_progress"])]
    return {
        "open": active[active["is_open"].astype(bool)],
        "upcoming": active[~active["is_open"].astype(bool)],
        "submitted": packages[packages["status"] == "submitted"],
        "done": packages[packages["status"] == "done"],
        "cancelled": packages[packages["status"] == "cancelled"],
        "today": packages[
            packages["start_date"].astype(str).le(today)
            & packages["end_date"].astype(str).ge(today)
            & packages["status"].isin(["pending", "in_progress"])
        ],
        "pending": active,
    }


def _plates_for(vehicles, request_id: str) -> list[str]:
    if vehicles.empty:
        return []
    rows = vehicles[
        (vehicles["request_id"].astype(str) == str(request_id))
        & (vehicles["status"].astype(str) != "cancelled")
    ]
    return rows["plate_no"].astype(str).tolist()


def _package_pdf(row, plates: list[str]) -> bytes:
    car_count = pd.to_numeric(row.get("car_count", 1), errors="coerce")
    return build_parking_pdf(
        agency=str(row.get("source_agency", "")),
        car_count=int(car_count) if pd.notna(car_count) else 1,
        plates=plates,
        parking_location=str(row.get("parking_location", "")),
        date_summary=str(row.get("date_summary", "")),
        parking_time=str(row.get("parking_time", "")),
        book_no=str(row.get("book_no", "")),
    )


def _open_submit(row) -> None:
    st.session_state["selected_guard_request_id"] = str(row["request_id"])
    st.switch_page("pages/06_ส่งงาน_รปภ.py")


def _open_detail(row) -> None:
    st.session_state["selected_request_id"] = str(row["request_id"])
    st.switch_page("pages/04_รายละเอียดหนังสือ.py")


def _render_guard_card(row, vehicles, *, prefix: str, admin: bool = False) -> None:
    request_id = str(row["request_id"])
    plates = _plates_for(vehicles, request_id)
    status = str(row["status"])
    is_open = bool(row.get("is_open", False))
    with st.container(border=True):
        st.markdown(f"### เลขหนังสือ {row['book_no']}")
        st.markdown(status_badge(status, "guard"), unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        col_a.write(f"**สำนัก/หน่วยงาน:** {row['source_agency']}")
        col_a.write(f"**วันที่จอด:** {row['date_summary']}")
        col_a.write(f"**เวลา:** {row.get('parking_time') or '-'}")
        col_b.write(f"**จุดจอด:** {row['parking_location']}")
        col_b.write(f"**จำนวนรถ:** {row['car_count']}")
        col_b.write(f"**ทะเบียน:** {', '.join(plates) if plates else 'ไม่มีทะเบียน'}")

        if not is_open and status in {"pending", "in_progress"}:
            st.caption(f"เปิดให้ทำวันที่ {row.get('open_date') or '-'}")
        if row.get("end_date") and str(row.get("end_date")) < pd.Timestamp.today().date().isoformat() and status in {"in_progress", "submitted", "done"}:
            st.warning("ครบกำหนดแล้ว นำป้าย/กรวยออก")

        pdf_bytes = _package_pdf(row, plates)
        cols = st.columns(3 if admin else 2)
        cols[0].download_button(
            "ดาวน์โหลดป้าย",
            pdf_bytes,
            safe_download_filename("parking_sign", row["book_no"], "pdf"),
            "application/pdf",
            key=f"{prefix}_pdf_{request_id}",
            use_container_width=True,
        )

        if status == "pending":
            if is_open:
                if cols[1].button("รับงาน", key=f"{prefix}_accept_{request_id}", use_container_width=True):
                    lock_key = f"accept_{request_id}"
                    if not begin_action_lock(lock_key):
                        st.warning("ระบบกำลังดำเนินการอยู่ กรุณารอสักครู่")
                    else:
                        try:
                            with st.spinner("กำลังรับงาน..."):
                                accept_guard_package(request_id)
                            st.session_state["flash_success"] = "รับงานแล้ว"
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
                        finally:
                            end_action_lock(lock_key)
            else:
                cols[1].button("ยังไม่ถึงวันทำงาน", key=f"{prefix}_not_open_{request_id}", disabled=True, use_container_width=True)
        elif status == "in_progress":
            cols[1].button("รับงานแล้ว", key=f"{prefix}_accepted_{request_id}", disabled=True, use_container_width=True)
            if st.button("ส่งงาน", key=f"{prefix}_submit_{request_id}", use_container_width=True):
                _open_submit(row)
        elif status == "submitted":
            cols[1].button("ส่งแล้ว รอผู้ดูแลยืนยัน", key=f"{prefix}_submitted_{request_id}", disabled=True, use_container_width=True)
        elif status == "done":
            cols[1].button("เสร็จสิ้น", key=f"{prefix}_done_{request_id}", disabled=True, use_container_width=True)
        elif status == "cancelled":
            cols[1].button("ยกเลิก", key=f"{prefix}_cancelled_{request_id}", disabled=True, use_container_width=True)

        if admin:
            if cols[2].button("เปิดรายละเอียด", key=f"{prefix}_detail_{request_id}", use_container_width=True):
                _open_detail(row)


def _render_guard_section(title: str, packages, vehicles, *, prefix: str, limit: int = 6, admin: bool = False) -> None:
    st.subheader(title)
    if packages.empty:
        st.caption("ไม่มีรายการ")
        return
    for _, row in packages.head(limit).iterrows():
        _render_guard_card(row, vehicles, prefix=f"{prefix}_{row['request_id']}", admin=admin)


def _render_admin_submitted(packages, vehicles, submissions) -> None:
    st.subheader("งานรอยืนยัน")
    if packages.empty:
        st.caption("ไม่มีรายการ")
        return
    for _, row in packages.head(8).iterrows():
        request_id = str(row["request_id"])
        request_submissions = submissions[submissions["request_id"].astype(str) == request_id] if not submissions.empty else submissions
        latest = request_submissions.sort_values("submitted_at", ascending=False).head(1)
        near_ok = "มี" if not latest.empty and str(latest.iloc[0].get("near_photo_url", "")).strip() else "ไม่มี"
        far_ok = "มี" if not latest.empty and str(latest.iloc[0].get("far_photo_url", "")).strip() else "ไม่มี"
        with st.container(border=True):
            st.markdown(f"### เลขหนังสือ {row['book_no']}")
            st.write(f"**สำนัก:** {row['source_agency']}")
            st.write(f"**วันที่จอด:** {row['date_summary']} | **จุดจอด:** {row['parking_location']}")
            st.write(f"**เวลาส่งงาน:** {row.get('submitted_at') or '-'}")
            st.write(f"**รูปใกล้:** {near_ok} | **รูปไกล:** {far_ok}")
            col1, col2 = st.columns(2)
            if col1.button("ยืนยันงานเสร็จ", key=f"admin_confirm_{request_id}", type="primary", use_container_width=True):
                lock_key = f"confirm_{request_id}"
                if not begin_action_lock(lock_key):
                    st.warning("กรุณารอสักครู่ อย่ากดซ้ำ")
                else:
                    try:
                        with st.spinner("กำลังยืนยันงาน..."):
                            mark_guard_package_done(request_id, user="แอดมิน")
                        st.session_state["flash_success"] = "ยืนยันงานเสร็จแล้ว"
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
                    finally:
                        end_action_lock(lock_key)
            if col2.button("เปิดรายละเอียด", key=f"admin_submitted_detail_{request_id}", use_container_width=True):
                _open_detail(row)


def _render_guard_home(packages, vehicles) -> None:
    render_page_title("งาน รปภ.", "รับงาน ดาวน์โหลดป้าย และส่งรูปงาน")
    groups = _split_packages(packages)
    _metric_cards(
        [
            ("งานเปิดให้ทำ", len(groups["open"])),
            ("งานวันนี้", len(groups["today"])),
            ("งานใกล้ถึง", len(groups["upcoming"])),
            ("ส่งแล้วรอตรวจ", len(groups["submitted"])),
            ("เสร็จแล้ว", len(groups["done"])),
        ]
    )
    _render_guard_section("งานเปิดให้ทำ", groups["open"], vehicles, prefix="guard_open")
    _render_guard_section("งานวันนี้", groups["today"], vehicles, prefix="guard_today")
    _render_guard_section("งานใกล้ถึง", groups["upcoming"], vehicles, prefix="guard_upcoming")
    _render_guard_section("ส่งแล้วรอตรวจ", groups["submitted"], vehicles, prefix="guard_submitted")
    _render_guard_section("เสร็จแล้ว", groups["done"], vehicles, prefix="guard_done")


def _render_officer_home(requests, packages) -> None:
    render_page_title("งานเจ้าหน้าที่", "บันทึกหนังสือ ค้นหา และดูประวัติคำขอ")
    groups = _split_packages(packages)
    today = pd.Timestamp.today().date().isoformat()
    created_today = requests[requests["created_at"].astype(str).str.startswith(today)] if not requests.empty else requests
    render_action_grid(
        [
            ("บันทึกหนังสือใหม่", "/บันทึกหนังสือ", "เพิ่มคำขอใหม่"),
            ("ค้นหาเลขหนังสือ", "/รายการหนังสือ", "ค้นหาด้วยเลขหนังสือหรือทะเบียน"),
            ("ประวัติคำขอ", "/รายการหนังสือ", "ดูคำขอล่าสุดและสถานะ"),
        ]
    )
    _metric_cards(
        [
            ("บันทึกวันนี้", len(created_today)),
            ("คำขอทั้งหมด", len(requests)),
            ("รอ รปภ.", len(groups["pending"])),
            ("ส่งแล้วรอยืนยัน", len(groups["submitted"])),
            ("เสร็จสิ้น", len(groups["done"])),
            ("ยกเลิก", len(groups["cancelled"])),
        ]
    )
    st.subheader("งานที่รอ รปภ.")
    if groups["pending"].empty:
        st.caption("ไม่มีรายการ")
    else:
        for _, row in groups["pending"].head(6).iterrows():
            with st.container(border=True):
                st.markdown(f"### เลขหนังสือ {row['book_no']}")
                st.write(f"**สำนัก/หน่วยงาน:** {row['source_agency']}")
                st.write(f"**วันที่จอด:** {row['date_summary']}")
                st.write(f"**จุดจอด:** {row['parking_location']} | **สถานะ:** {status_badge(row['status'], 'guard')}", unsafe_allow_html=True)
    st.subheader("งานที่ส่งแล้วรอยืนยัน")
    if groups["submitted"].empty:
        st.caption("ไม่มีรายการ")
    else:
        for _, row in groups["submitted"].head(6).iterrows():
            with st.container(border=True):
                st.markdown(f"### เลขหนังสือ {row['book_no']}")
                st.write(f"**สำนัก/หน่วยงาน:** {row['source_agency']}")
                st.write(f"**วันที่จอด:** {row['date_summary']}")
                st.write(f"**จุดจอด:** {row['parking_location']} | **สถานะ:** {status_badge(row['status'], 'guard')}", unsafe_allow_html=True)


def _render_admin_home(requests, packages, vehicles, submissions) -> None:
    render_page_title("ผู้ดูแลระบบ", "ยืนยันงาน ซ่อมข้อมูล และดูรายงาน")
    groups = _split_packages(packages)
    render_action_grid(
        [
            ("Dashboard", "/แดชบอร์ด", "ภาพรวมทั้งหมด"),
            ("รายการทั้งหมด", "/รายการหนังสือ", "ค้นหาและเปิดรายละเอียด"),
            ("งาน รปภ.", "/งาน_รปภ", "ดูงานและเปลี่ยนสถานะ"),
            ("รายงาน", "/รายงานรายเดือน", "ส่งออกรายงาน"),
            ("ตั้งค่า", "/ตั้งค่า", "ซ่อมข้อมูลและตรวจระบบ"),
        ]
    )
    _metric_cards(
        [
            ("งานรอยืนยัน", len(groups["submitted"])),
            ("งานค้าง", len(groups["pending"])),
            ("งานวันนี้", len(groups["today"])),
            ("งานใกล้ถึง", len(groups["upcoming"])),
            ("งานเสร็จ", len(groups["done"])),
            ("งานยกเลิก", len(groups["cancelled"])),
            ("คำขอทั้งหมด", len(requests)),
        ]
    )
    _render_admin_submitted(groups["submitted"], vehicles, submissions)
    _render_guard_section("งานค้าง/เปิดให้ทำ", groups["open"], vehicles, prefix="admin_open", admin=True)
    _render_guard_section("งานใกล้ถึง", groups["upcoming"], vehicles, prefix="admin_upcoming", admin=True)


def render_home() -> None:
    inject_global_css()
    initialize_storage()

    role = get_current_role()
    if not role:
        render_role_selector()
        return

    render_role_badge()
    _show_flash()
    with st.spinner("กำลังโหลดข้อมูล..."):
        requests = read_sheet("Requests")
        packages = build_guard_packages()
        vehicles = read_sheet("Vehicles")
        submissions = read_sheet("Guard_Submissions")

    if role == ROLE_GUARD:
        _render_guard_home(packages[packages["status"] != "cancelled"] if not packages.empty else packages, vehicles)
    elif role == ROLE_OFFICER:
        _render_officer_home(requests, packages)
    elif role == ROLE_ADMIN:
        _render_admin_home(requests, packages, vehicles, submissions)
