from __future__ import annotations

from modules.drive_preview import extract_drive_file_id, is_google_drive_url


def test_extract_drive_file_id_from_file_view_url():
    value = "https://drive.google.com/file/d/1AbC_def-123/view?usp=drivesdk"

    assert extract_drive_file_id(value) == "1AbC_def-123"
    assert is_google_drive_url(value) is True


def test_extract_drive_file_id_from_open_url():
    value = "https://drive.google.com/open?id=1AbC_def-456"

    assert extract_drive_file_id(value) == "1AbC_def-456"
    assert is_google_drive_url(value) is True


def test_extract_drive_file_id_from_uc_url():
    value = "https://drive.google.com/uc?export=view&id=1AbC_def-789"

    assert extract_drive_file_id(value) == "1AbC_def-789"
    assert is_google_drive_url(value) is True


def test_extract_drive_file_id_accepts_raw_file_id():
    assert extract_drive_file_id("1AbC_def-rawFileId") == "1AbC_def-rawFileId"


def test_extract_drive_file_id_rejects_local_upload_path():
    assert extract_drive_file_id("uploads/guard_submissions/near.jpg") is None
    assert is_google_drive_url("uploads/guard_submissions/near.jpg") is False


def test_extract_drive_file_id_rejects_unrelated_url():
    assert extract_drive_file_id("https://example.com/file/1AbC_def") is None
    assert is_google_drive_url("https://example.com/file/1AbC_def") is False
