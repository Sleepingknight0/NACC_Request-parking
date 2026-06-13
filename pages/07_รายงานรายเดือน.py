import pandas as pd
import streamlit as st

from modules.sheets import read_sheet
from modules.ui import inject_global_css, render_page_title


st.set_page_config(page_title="รายงานรายเดือน", page_icon="📅", layout="wide")
inject_global_css()
render_page_title("รายงานรายเดือน", "สรุปตามวันที่ สำนัก และจุดจอด")

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
st.dataframe(joined, use_container_width=True, hide_index=True)

st.subheader("สรุปตามสำนัก")
agency_summary = joined.groupby("source_agency", dropna=False).agg(
    requests=("request_id", "nunique"),
    parking_dates=("request_date_id", "count"),
    cars=("car_count", lambda values: pd.to_numeric(values, errors="coerce").fillna(0).sum()),
).reset_index()
st.dataframe(agency_summary, use_container_width=True, hide_index=True)

st.subheader("สรุปตามจุดจอด")
location_summary = joined.groupby("parking_location", dropna=False).agg(
    requests=("request_id", "nunique"),
    parking_dates=("request_date_id", "count"),
    cars=("car_count", lambda values: pd.to_numeric(values, errors="coerce").fillna(0).sum()),
).reset_index()
st.dataframe(location_summary, use_container_width=True, hide_index=True)

st.download_button(
    "ส่งออก CSV",
    joined.to_csv(index=False).encode("utf-8-sig"),
    f"parking_report_{selected_month}.csv",
    "text/csv",
)
