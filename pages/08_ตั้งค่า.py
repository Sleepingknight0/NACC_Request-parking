import pandas as pd
import streamlit as st

from modules.constants import NACC_DEPARTMENTS, PARKING_LOCATIONS, WORKSHEET_SCHEMAS
from modules.sheets import initialize_storage, read_sheet
from modules.ui import inject_global_css, render_dataframe, render_page_title


st.set_page_config(page_title="ตั้งค่า", page_icon="icon.svg", layout="wide")
inject_global_css()
render_page_title("ตั้งค่า", "ค่าคงที่และตรวจสุขภาพข้อมูล")

initialize_storage()

st.subheader("Worksheet schema")
for name, columns in WORKSHEET_SCHEMAS.items():
    with st.expander(name):
        render_dataframe(
            pd.DataFrame(
                {
                    "ลำดับ": range(1, len(columns) + 1),
                    "field_key": columns,
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

st.subheader("Data health checks")
requests = read_sheet("Requests")
dates = read_sheet("Request_Dates")
tasks = read_sheet("Guard_Tasks")

request_ids = set(requests["request_id"].astype(str)) if not requests.empty else set()
orphan_dates = dates[~dates["request_id"].astype(str).isin(request_ids)] if not dates.empty else dates
orphan_tasks = tasks[~tasks["request_id"].astype(str).isin(request_ids)] if not tasks.empty else tasks
cancelled_request_ids = set(requests[requests["status"] == "cancelled"]["request_id"].astype(str)) if not requests.empty else set()
active_tasks_under_cancelled = tasks[
    tasks["request_id"].astype(str).isin(cancelled_request_ids)
    & ~tasks["status"].astype(str).isin(["cancelled", "done"])
] if not tasks.empty else tasks

col1, col2, col3 = st.columns(3)
col1.metric("วันที่กำพร้า", len(orphan_dates))
col2.metric("งานกำพร้า", len(orphan_tasks))
col3.metric("คำขอยกเลิกแต่ยังมีงาน active", len(active_tasks_under_cancelled))
