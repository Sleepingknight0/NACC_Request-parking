from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_book_upload_page_checks_uploaded_file_by_none_not_truthiness():
    source = (ROOT / "pages" / "02_บันทึกหนังสือ.py").read_text(encoding="utf-8")

    assert "if book_file is not None" in source
    assert "if book_file else" not in source


def test_guard_submit_page_checks_extra_upload_by_none_not_truthiness():
    source = (ROOT / "pages" / "06_ส่งงาน_รปภ.py").read_text(encoding="utf-8")

    assert "if extra_photo is not None" in source
    assert "if extra_photo else" not in source
