import streamlit as st

from modules.constants import APP_NAME
from modules.home import render_home


st.set_page_config(
    page_title=APP_NAME,
    page_icon="📝",
    layout="wide",
)

render_home()
