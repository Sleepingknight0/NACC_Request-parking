from __future__ import annotations

from io import BytesIO

from modules.storage import (
    get_file_storage_backend,
    is_drive_url,
    is_local_upload_url,
    make_safe_file_name,
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
