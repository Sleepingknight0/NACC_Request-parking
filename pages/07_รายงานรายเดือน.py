import pandas as pd
import streamlit as st

from modules.sheets import read_sheet
from modules.ui import inject_global_css, render_dataframe, render_page_title


st.set_page_config(page_title="รายงานรายเดือน", page_icon="icon.svg", layout="wide")
inject_global_css()
render_page_title("รายงานรายเดือน", "ข้อมูลสรุปพร้อมใช้สำหรับอ้างอิงและส่งออกรายงาน")

requests = read_sheet("Requests")
dates = read_sheet("Request_Dates")
if dates.empty:
    st.info("ยังไม่มีข้อมูลวันที่จอด")
    st.stop()

month_options = sorted(dates["month_key"].dropna().unique().tolist())
selected_month = st.selectbox("เดือน", month_options)
month_dates = dates[dates["month_key"] == selected_month]
joined = month_dates.merge(requests, on="request_id", how="left", suffixes=("", "_request"))

st.subheader("ข้อมูลรายวัน")
render_dataframe(
    joined,
    ["parking_date", "parking_time", "source_agency", "parking_location", "car_count", "status"],
    worksheet="Request_Dates",
)

st.subheader("สรุปตามสำนัก")
agency_summary = joined.groupby("source_agency", dropna=False).agg(
    requests=("request_id", "nunique"),
    parking_dates=("request_date_id", "count"),
    cars=("car_count", lambda values: pd.to_numeric(values, errors="coerce").fillna(0).sum()),
).reset_index().rename(
    columns={
        "source_agency": "สำนัก/หน่วยงาน",
        "requests": "จำนวนหนังสือ",
        "parking_dates": "จำนวนวันจอด",
        "cars": "จำนวนรถ",
    }
)
render_dataframe(agency_summary)

st.subheader("สรุปตามจุดจอด")
location_summary = joined.groupby("parking_location", dropna=False).agg(
    requests=("request_id", "nunique"),
    parking_dates=("request_date_id", "count"),
    cars=("car_count", lambda values: pd.to_numeric(values, errors="coerce").fillna(0).sum()),
).reset_index().rename(
    columns={
        "parking_location": "จุดจอด",
        "requests": "จำนวนหนังสือ",
        "parking_dates": "จำนวนวันจอด",
        "cars": "จำนวนรถ",
    }
)
render_dataframe(location_summary)

st.download_button(
    "ส่งออก CSV",
    joined.to_csv(index=False).encode("utf-8-sig"),
    f"parking_report_{selected_month}.csv",
    "text/csv",
)
