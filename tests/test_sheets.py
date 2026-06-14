import pytest

from modules import sheets
from modules.sheets import (
    _normalize_private_key,
    _normalize_columns,
    _sheet_range,
    _spreadsheet_id_from_url,
    _to_sheet_headers,
    append_rows,
)


def test_normalize_private_key_converts_escaped_newlines():
    raw_key = "-----BEGIN PRIVATE KEY-----\\nABC123\\n-----END PRIVATE KEY-----\\n"

    assert _normalize_private_key(raw_key) == (
        "-----BEGIN PRIVATE KEY-----\nABC123\n-----END PRIVATE KEY-----"
    )


def test_normalize_private_key_repairs_dot_after_pem_markers():
    raw_key = "-----BEGIN PRIVATE KEY-----.ABC123.-----END PRIVATE KEY-----"

    assert _normalize_private_key(raw_key) == (
        "-----BEGIN PRIVATE KEY-----\nABC123\n-----END PRIVATE KEY-----"
    )


def test_normalize_private_key_handles_triple_quoted_secret_shape():
    raw_key = """-----BEGIN PRIVATE KEY-----
\\nABC123\\n
-----END PRIVATE KEY-----"""

    assert _normalize_private_key(raw_key) == (
        "-----BEGIN PRIVATE KEY-----\nABC123\n-----END PRIVATE KEY-----"
    )


def test_spreadsheet_id_from_url_accepts_url_or_raw_id():
    assert _spreadsheet_id_from_url(
        "https://docs.google.com/spreadsheets/d/1abc_DEF-123/edit?usp=sharing"
    ) == "1abc_DEF-123"
    assert _spreadsheet_id_from_url("1abc_DEF-123") == "1abc_DEF-123"


def test_sheet_range_quotes_thai_sheet_names():
    assert _sheet_range("คำขอ", "A1") == "%27%E0%B8%84%E0%B8%B3%E0%B8%82%E0%B8%AD%27%21A1"


def test_google_sheet_rows_are_padded_to_header_width():
    headers = ["a", "b", "c"]
    rows = [["1"], ["2", "3", "4", "extra"]]

    normalized_rows = [(row + [""] * len(headers))[: len(headers)] for row in rows]

    assert normalized_rows == [["1", "", ""], ["2", "3", "4"]]


def test_sheet_status_and_boolean_values_are_thai_on_write_and_internal_on_read():
    import pandas as pd

    internal = pd.DataFrame(
        [
            {
                "request_id": "REQ-1",
                "book_no": "QA",
                "book_date": "",
                "received_date": "2026-06-14",
                "source_agency": "สำนักทดสอบ",
                "car_count": "1",
                "parking_location": "หน้าอาคาร 3",
                "note": "",
                "status": "pending",
                "has_vehicle_plates": "FALSE",
                "book_file_url": "",
                "created_by": "tester",
                "created_at": "2026-06-14T00:00:00",
                "updated_at": "2026-06-14T00:00:00",
                "cancelled_at": "",
                "cancelled_by": "",
                "cancelled_reason": "",
            }
        ]
    )

    sheet_df = _to_sheet_headers("Requests", internal)

    assert sheet_df.loc[0, "สถานะคำขอ"] == "รอดำเนินการ"
    assert sheet_df.loc[0, "มีทะเบียนรถ"] == "ไม่มี"

    normalized = _normalize_columns("Requests", sheet_df)

    assert normalized.loc[0, "status"] == "pending"
    assert normalized.loc[0, "has_vehicle_plates"] == "FALSE"


def test_normalize_columns_cleans_sheet_datetime_dates_and_month_keys():
    import pandas as pd

    sheet_df = pd.DataFrame(
        [
            {
                "รหัสวันที่จอด": "DATE-1",
                "รหัสคำขอ": "REQ-1",
                "วันที่จอด": "2026-06-14 00:00:00",
                "เวลาที่จอด": "08:30-16:30",
                "เดือนรายงาน": "2026-06-01 00:00:00",
                "สถานะวันที่จอด": "รอดำเนินการ",
                "วันที่สร้างข้อมูล": "",
                "วันที่ยกเลิก": "",
                "เหตุผลยกเลิก": "",
            }
        ]
    )

    normalized = _normalize_columns("Request_Dates", sheet_df)

    assert normalized.loc[0, "parking_date"] == "2026-06-14"
    assert normalized.loc[0, "month_key"] == "2026-06"


def test_append_rows_does_not_write_when_gsheet_read_fails(monkeypatch):
    writes = []

    monkeypatch.setattr(sheets, "_use_gsheets", lambda: True)

    def fail_read(worksheet, *args, **kwargs):
        if kwargs.get("strict"):
            raise RuntimeError("read failed")
        return sheets._empty_df(worksheet)

    monkeypatch.setattr(sheets, "_read_gsheet", fail_read)
    monkeypatch.setattr(sheets, "_write_gsheet", lambda *args, **kwargs: writes.append(args))

    with pytest.raises(RuntimeError, match="read failed"):
        append_rows("Audit_Log", [{"log_id": "LOG-1", "action": "test"}])

    assert writes == []
