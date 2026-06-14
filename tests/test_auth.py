from __future__ import annotations

from types import SimpleNamespace

from modules import auth


def test_get_current_role_does_not_trust_query_params(monkeypatch):
    fake_streamlit = SimpleNamespace(
        session_state={},
        query_params={"role": auth.ROLE_ADMIN},
    )
    monkeypatch.setattr(auth, "st", fake_streamlit)

    assert auth.get_current_role() is None
    assert "user_role" not in fake_streamlit.session_state


def test_clear_role_removes_role_scoped_state_and_query_params(monkeypatch):
    fake_streamlit = SimpleNamespace(
        session_state={
            "user_role": auth.ROLE_GUARD,
            "selected_request_id": "REQ-1",
            "selected_guard_request_id": "REQ-2",
            "selected_task_id": "TASK-1",
            "selected_package_id": "REQ-3",
            "admin_pin_input": "1234",
            "unrelated": "keep",
        },
        query_params={"role": "guard", "request_id": "REQ-1", "task_id": "TASK-1", "theme": "day"},
    )
    monkeypatch.setattr(auth, "st", fake_streamlit)

    auth.clear_role()

    assert fake_streamlit.session_state == {"unrelated": "keep"}
    assert fake_streamlit.query_params == {"theme": "day"}
