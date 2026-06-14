import streamlit as st

from modules.sheets import initialize_storage, read_sheet
from modules.ui import inject_global_css, render_action_grid, render_page_title, render_record_cards


def render_home() -> None:
    inject_global_css()
    initialize_storage()

    render_page_title("ระบบขอที่จอดรถ ป.ป.ช.", "บันทึกคำขอ ติดตามงาน รปภ. และออกข้อมูลอ้างอิงจากฐานข้อมูลเดียว")

    requests = read_sheet("Requests")
    tasks = read_sheet("Guard_Tasks")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("หนังสือทั้งหมด", len(requests))
    col2.metric("งาน รปภ.", len(tasks))
    col3.metric("งานค้าง", len(tasks[tasks["status"].isin(["pending", "in_progress"])]))
    col4.metric("ส่งแล้วรอตรวจ", len(tasks[tasks["status"].astype(str) == "submitted"]) if not tasks.empty else 0)

    render_action_grid(
        [
            ("บันทึกหนังสือ", "/บันทึกหนังสือ", "เพิ่มคำขอใหม่และสร้างงาน รปภ. อัตโนมัติ"),
            ("ดูงานวันนี้", "/งาน_รปภ", "ดูงานที่ต้องปฏิบัติและดาวน์โหลด PDF"),
            ("ค้นหารายการ", "/รายการหนังสือ", "ค้นหาด้วยเลขหนังสือ สำนัก จุดจอด หรือทะเบียน"),
            ("รายงานรายเดือน", "/รายงานรายเดือน", "สรุปงานเพื่อใช้อ้างอิงและทำรายงาน"),
        ]
    )

    if not tasks.empty:
        urgent = tasks[tasks["status"].isin(["pending", "in_progress"])].sort_values("parking_date")
        st.subheader("งานที่ต้องติดตาม")
        render_record_cards(
            urgent,
            title_field="parking_date",
            fields=["parking_location", "status", "task_id"],
            worksheet="Guard_Tasks",
            status_kind="guard",
            empty_text="ไม่มีงานค้าง",
            max_cards=6,
        )
