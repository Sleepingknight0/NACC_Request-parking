from modules.sheets import _normalize_private_key, _sheet_range, _spreadsheet_id_from_url


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
