from __future__ import annotations

from io import BytesIO

import pytest

from modules.storage import (
    DriveStorageConfigError,
    describe_drive_upload_error,
    get_drive_config,
    get_file_storage_backend,
    is_drive_url,
    is_local_upload_url,
    make_safe_file_name,
    upload_file,
    upload_file_to_local,
)


class FakeUpload(BytesIO):
    def __init__(self, data: bytes, name: str, mime_type: str):
        super().__init__(data)
        self.name = name
        self.type = mime_type

    def getbuffer(self):
        return memoryview(self.getvalue())


def test_make_safe_file_name_removes_path_separators_and_preserves_extension():
    name = make_safe_file_name("book_QA/123", "../หนังสือ ทดสอบ.pdf", timestamp="20260614_091500")

    assert "/" not in name
    assert "\\" not in name
    assert name.endswith(".pdf")
    assert "book_QA_123_20260614_091500" in name


def test_storage_url_classifiers():
    assert is_local_upload_url("uploads/book_files/example.pdf") is True
    assert is_local_upload_url("uploads\\book_files\\example.pdf") is True
    assert is_drive_url("https://drive.google.com/file/d/FILE_ID/view") is True
    assert is_drive_url("https://drive.google.com/open?id=FILE_ID") is True
    assert is_drive_url("uploads/book_files/example.pdf") is False


def test_get_file_storage_backend_prefers_env(monkeypatch):
    monkeypatch.setenv("PARKING_APP_FILE_STORAGE_BACKEND", "local")

    assert get_file_storage_backend() == "local"


def test_upload_file_to_local_returns_compatible_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.storage.UPLOAD_DIR", tmp_path)
    upload = FakeUpload(b"hello", "test image.jpg", "image/jpeg")

    meta = upload_file_to_local(upload, "guard_submissions", "guard_QA_near")

    assert meta["file_name"].endswith(".jpg")
    assert meta["file_url"].startswith(str((tmp_path / "guard_submissions").as_posix()))
    assert meta["mime_type"] == "image/jpeg"
    assert meta["storage_key"] == meta["file_url"]
    assert meta["storage_backend"] == "local"
    assert meta["drive_file_id"] == ""


def test_upload_file_blocks_when_drive_selected_without_folder_config(monkeypatch):
    monkeypatch.setenv("PARKING_APP_FILE_STORAGE_BACKEND", "google_drive")
    monkeypatch.setattr("modules.storage._secret_get", lambda *args, default="": default)
    upload = FakeUpload(b"hello", "test image.jpg", "image/jpeg")

    with pytest.raises(DriveStorageConfigError, match="ยังไม่ได้ตั้งค่า Google Drive"):
        upload_file(upload, "other", "other_QA")


def test_drive_config_includes_production_folder_defaults(monkeypatch):
    monkeypatch.delenv("PARKING_APP_GDRIVE_BOOK_FILES_FOLDER_ID", raising=False)
    monkeypatch.delenv("PARKING_APP_GDRIVE_GUARD_SUBMISSIONS_FOLDER_ID", raising=False)
    monkeypatch.setattr("modules.storage._secret_get", lambda *args, default="": default)

    config = get_drive_config()

    assert config["folders"]["book_files"] == "1mhxxhIUUUse3_kUPJ8qA6xLIN0h1pOmx"
    assert config["folders"]["guard_submissions"] == "1Hi9EVC7sWk7ZnnhlUdp58s3mwjH1L7dQ"


def test_describe_drive_upload_error_explains_service_account_quota():
    exc = RuntimeError(
        "Service Accounts do not have storage quota. reason: storageQuotaExceeded"
    )

    message = describe_drive_upload_error(exc)

    assert "Service account" in message
    assert "Shared Drive" in message
    assert "OAuth" in message


def test_describe_drive_upload_error_explains_permission_denied():
    exc = RuntimeError("HttpError 403 insufficientFilePermissions")

    message = describe_drive_upload_error(exc)

    assert "สิทธิ์" in message
    assert "service account" in message
