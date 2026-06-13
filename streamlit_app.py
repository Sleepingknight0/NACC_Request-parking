"""Streamlit Cloud entrypoint.

The main app lives in app.py for local development. Streamlit Cloud commonly
defaults to streamlit_app.py, so this wrapper keeps both entrypoints working.
"""

import app  # noqa: F401
