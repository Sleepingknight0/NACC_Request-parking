from __future__ import annotations

import streamlit as st


def _lock_key(action_key: str) -> str:
    return f"nacc_action_lock_{action_key}"


def is_action_locked(action_key: str) -> bool:
    return bool(st.session_state.get(_lock_key(action_key), False))


def begin_action_lock(action_key: str) -> bool:
    key = _lock_key(action_key)
    if st.session_state.get(key):
        return False
    st.session_state[key] = True
    return True


def end_action_lock(action_key: str) -> None:
    st.session_state.pop(_lock_key(action_key), None)
