from modules.constants import sheet_title_for, thai_headers_for


def test_sheet_title_for_google_sheets_uses_visible_thai_tabs():
    assert sheet_title_for("Requests") == "คำขอ"
    assert sheet_title_for("Guard_Tasks") == "งาน รปภ."


def test_thai_headers_follow_schema_order():
    assert thai_headers_for("Requests")[:4] == [
        "รหัสคำขอ",
        "เลขหนังสือ",
        "วันที่หนังสือ",
        "วันที่รับเรื่อง",
    ]
