import streamlit as st

from modules.constants import APP_NAME
from modules.sheets import initialize_storage, read_sheet
from modules.ui import inject_global_css, render_page_title


st.set_page_config(
    page_title=APP_NAME,
    page_icon="📝",
    layout="wide",
)

inject_global_css()
initialize_storage()

render_page_title(APP_NAME, "ระบบบันทึก ติดตาม และปิดงานคำขอที่จอดรถ")

requests = read_sheet("Requests")
tasks = read_sheet("Guard_Tasks")

col1, col2, col3 = st.columns(3)
col1.metric("หนังสือทั้งหมด", len(requests))
col2.metric("งาน รปภ.", len(tasks))
col3.metric("งานค้าง", len(tasks[tasks["status"].isin(["pending", "in_progress"])]))

st.markdown(
    """
    <div class="nacc-card">
    <strong>เริ่มใช้งาน</strong>
    <div class="nacc-muted">
    ใช้เมนูด้านซ้ายเพื่อบันทึกหนังสือใหม่ ดูแดชบอร์ด ค้นหารายการ และส่งงาน รปภ.
    ข้อมูลรอบพัฒนานี้บันทึกลงไฟล์ CSV ในโฟลเดอร์ <code>data/</code> ก่อนเชื่อม Google Sheets จริง
    </div>
    </div>
    """,
    unsafe_allow_html=True,
)
