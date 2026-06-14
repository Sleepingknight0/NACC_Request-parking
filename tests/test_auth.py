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

