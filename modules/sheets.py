from __future__ import annotations

import os
import re
from pathlib import Path

import pandas as pd

from modules.constants import (
    WORKSHEET_SCHEMAS,
    field_to_thai_map,
    sheet_title_for,
    thai_to_field_map,
)

try:
    import streamlit as st
    from streamlit_gsheets import GSheetsConnection
except Exception:  # pragma: no cover
    st = None
    GSheetsConnection = None

try:
    import gspread
    from google.oauth2.service_account import Credentials
except Exception:  # pragma: no cover
    gspread = None
    Credentials = None


DATA_DIR = Path(os.getenv("PARKING_APP_DATA_DIR", "data"))
GSHEETS_SCOPES = (
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
)


def _get_secret_value(section: str, key: str, default: str = "") -> str:
    if st is None:
        return default

    try:
        value = st.secrets.get(section, {}).get(key, default)
    except Exception:
        return default

    return str(value or default)


def _storage_backend() -> str:
    """
    Storage backend priority:
    1. Environment variable PARKING_APP_STORAGE_BACKEND
    2. Streamlit secrets [app].storage_backend
    3. csv fallback

    Valid values:
    - csv
    - gsheets
    """
    env_value = os.getenv("PARKING_APP_STORAGE_BACKEND", "").strip().lower()
    if env_value:
        return env_value

    secret_value = _get_secret_value("app", "storage_backend", "csv").strip().lower()
    return secret_value or "csv"


def _spreadsheet_url() -> str:
    if st is not None:
        try:
            value = st.secrets.get("connections", {}).get("gsheets", {}).get("spreadsheet", "")
            if value:
                return str(value)
        except Exception:
            pass

    return os.getenv("PARKING_APP_SPREADSHEET_URL", "")


def _normalize_private_key(private_key: str) -> str:
    key = str(private_key or "").strip().strip('"').strip("'")
    key = key.replace("\\n", "\n").replace("\r\n", "\n").replace("\r", "\n")
    key = key.replace("-----BEGIN PRIVATE KEY-----.", "-----BEGIN PRIVATE KEY-----\n")
    key = key.replace(".-----END PRIVATE KEY-----", "\n-----END PRIVATE KEY-----")
    key = re.sub(r"(-----BEGIN PRIVATE KEY-----)\s*", r"\1\n", key)
    key = re.sub(r"\s*(-----END PRIVATE KEY-----)", r"\n\1", key)
    return key.strip()


def _use_gsheets() -> bool:
    backend = _storage_backend()
    return backend in {"gsheets", "google_sheets", "google-sheets"}


def _path_for(worksheet: str) -> Path:
    if worksheet not in WORKSHEET_SCHEMAS:
        raise KeyError(f"Unknown worksheet: {worksheet}")

    return DATA_DIR / f"{worksheet}.csv"


def _empty_df(worksheet: str) -> pd.DataFrame:
    return pd.DataFrame(columns=WORKSHEET_SCHEMAS[worksheet])


def _to_internal_headers(worksheet: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert Thai sheet headers to internal English field keys.

    External sheet:
        รหัสคำขอ, เลขหนังสือ, วันที่รับเรื่อง

    Internal code:
        request_id, book_no, received_date
    """
    if df is None:
        return _empty_df(worksheet)

    result = df.copy()
    reverse_map = thai_to_field_map(worksheet)

    result.columns = [
        reverse_map.get(str(column).strip(), str(column).strip())
        for column in result.columns
    ]

    return result


def _to_sheet_headers(worksheet: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert internal English field keys to Thai headers before writing.
    """
    result = df.copy()
    header_map = field_to_thai_map(worksheet)

    result.columns = [
        header_map.get(str(column).strip(), str(column).strip())
        for column in result.columns
    ]

    return result


def _normalize_columns(worksheet: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize dataframe to internal English field keys and required schema order.
    """
    if df is None or df.empty:
        return _empty_df(worksheet)

    normalized = _to_internal_headers(worksheet, df)

    for column in WORKSHEET_SCHEMAS[worksheet]:
        if column not in normalized.columns:
            normalized[column] = ""

    extra_cols = [
        col for col in normalized.columns
        if col not in WORKSHEET_SCHEMAS[worksheet]
    ]

    return normalized[WORKSHEET_SCHEMAS[worksheet] + extra_cols].fillna("")


def get_connection():
    """
    Return Streamlit Google Sheets connection.

    Required Streamlit secrets:

    [connections.gsheets]
    spreadsheet = "https://docs.google.com/spreadsheets/d/xxxx/edit"

    [google_service_account]
    ...
    """
    if st is None or GSheetsConnection is None:
        raise RuntimeError(
            "ไม่สามารถใช้ Google Sheets backend ได้ เพราะ streamlit_gsheets ยังไม่พร้อมใช้งาน"
        )

    return st.connection("gsheets", type=GSheetsConnection)


def _get_gspread_spreadsheet():
    if st is None or gspread is None or Credentials is None:
        raise RuntimeError("gspread backend is not available")

    spreadsheet_url = _spreadsheet_url()
    if not spreadsheet_url:
        raise RuntimeError("missing [connections.gsheets].spreadsheet")

    try:
        service_account_info = dict(st.secrets.get("google_service_account", {}))
    except Exception as exc:
        raise RuntimeError("missing [google_service_account] secrets") from exc

    service_account_info["private_key"] = _normalize_private_key(
        service_account_info.get("private_key", "")
    )

    credentials = Credentials.from_service_account_info(
        service_account_info,
        scopes=list(GSHEETS_SCOPES),
    )
    client = gspread.authorize(credentials)
    return client.open_by_url(spreadsheet_url)


def _read_gsheet_with_gspread(sheet_title: str) -> pd.DataFrame:
    spreadsheet = _get_gspread_spreadsheet()
    worksheet = spreadsheet.worksheet(sheet_title)
    values = worksheet.get_all_values()
    if not values:
        return pd.DataFrame()

    headers = values[0]
    rows = values[1:]
    return pd.DataFrame(rows, columns=headers)


def _write_gsheet_with_gspread(sheet_title: str, sheet_df: pd.DataFrame) -> None:
    spreadsheet = _get_gspread_spreadsheet()
    worksheet = spreadsheet.worksheet(sheet_title)
    payload = [sheet_df.columns.tolist()] + sheet_df.fillna("").astype(str).values.tolist()
    worksheet.clear()
    worksheet.update(range_name="A1", values=payload)


def initialize_storage() -> None:
    """
    CSV mode:
        Create local CSV files with Thai headers.

    Google Sheets mode:
        Do not create worksheets automatically.
        The spreadsheet must already contain worksheets named exactly:
        Requests, Request_Dates, Vehicles, Guard_Tasks, Guard_Submissions,
        Attachments, Audit_Log
    """
    if _use_gsheets():
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for worksheet in WORKSHEET_SCHEMAS:
        path = _path_for(worksheet)

        if not path.exists():
            empty_internal = _empty_df(worksheet)
            empty_sheet = _to_sheet_headers(worksheet, empty_internal)
            empty_sheet.to_csv(path, index=False, encoding="utf-8-sig")


def _read_csv_sheet(worksheet: str) -> pd.DataFrame:
    initialize_storage()

    path = _path_for(worksheet)

    if path.stat().st_size == 0:
        return _empty_df(worksheet)

    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return _normalize_columns(worksheet, df)


def _write_csv_sheet(worksheet: str, df: pd.DataFrame) -> None:
    initialize_storage()

    normalized = _normalize_columns(worksheet, df.copy())
    sheet_df = _to_sheet_headers(worksheet, normalized)

    sheet_df.to_csv(_path_for(worksheet), index=False, encoding="utf-8-sig")


def _read_gsheet(worksheet: str, ttl: int = 0) -> pd.DataFrame:
    sheet_title = sheet_title_for(worksheet)
    try:
        if gspread is not None and Credentials is not None:
            df = _read_gsheet_with_gspread(sheet_title)
        else:
            conn = get_connection()
            df = conn.read(worksheet=sheet_title, ttl=ttl)
    except Exception as exc:
        if st is not None:
            st.error(f"อ่านข้อมูลจาก Google Sheets ไม่สำเร็จ: {sheet_title}")
            st.info(
                "ตรวจสอบ 4 จุดนี้: "
                "1) ชื่อแท็บใน Google Sheet ต้องตรงกับชื่อแท็บภาษาไทยที่ระบบใช้ "
                "2) แชร์ไฟล์ Google Sheet ให้ service account แล้ว "
                "3) ตั้งค่า Streamlit Secrets ถูกต้อง "
                "4) private_key ต้องเป็น PEM key ที่ขึ้นต้นด้วย BEGIN PRIVATE KEY"
            )

            with st.expander("รายละเอียด error สำหรับแก้ระบบ"):
                st.code(str(exc))

            st.stop()

        raise RuntimeError(
            f"อ่าน worksheet '{sheet_title}' จาก Google Sheets ไม่สำเร็จ"
        ) from exc

    return _normalize_columns(worksheet, df)


def _write_gsheet(worksheet: str, df: pd.DataFrame) -> None:
    sheet_title = sheet_title_for(worksheet)

    normalized = _normalize_columns(worksheet, df.copy())
    sheet_df = _to_sheet_headers(worksheet, normalized)

    try:
        if gspread is not None and Credentials is not None:
            _write_gsheet_with_gspread(sheet_title, sheet_df)
        else:
            conn = get_connection()
            conn.update(worksheet=sheet_title, data=sheet_df)
    except Exception as exc:
        if st is not None:
            st.error(f"เขียนข้อมูลไปยัง Google Sheets ไม่สำเร็จ: {sheet_title}")
            st.info(
                "ตรวจสอบ 4 จุดนี้: "
                "1) service account ต้องมีสิทธิ์ Editor "
                "2) ชื่อแท็บภาษาไทยต้องตรง "
                "3) หัวคอลัมน์ภาษาไทยต้องตรงกับ mapping "
                "4) Google Sheet ไม่ควรถูกป้องกันช่วงเซลล์ที่แอปต้องเขียน"
            )

            with st.expander("รายละเอียด error สำหรับแก้ระบบ"):
                st.code(str(exc))

            st.stop()

        raise RuntimeError(
            f"เขียน worksheet '{sheet_title}' ไปยัง Google Sheets ไม่สำเร็จ"
        ) from exc


def read_sheet(worksheet: str, ttl: int = 0) -> pd.DataFrame:
    """
    Read worksheet and return internal English field keys.
    """
    if worksheet not in WORKSHEET_SCHEMAS:
        raise KeyError(f"Unknown worksheet: {worksheet}")

    if _use_gsheets():
        return _read_gsheet(worksheet, ttl=ttl)

    return _read_csv_sheet(worksheet)


def write_sheet(worksheet: str, df: pd.DataFrame) -> None:
    """
    Write dataframe to selected backend.

    Callers use English field keys.
    External storage uses Thai headers.
    """
    if worksheet not in WORKSHEET_SCHEMAS:
        raise KeyError(f"Unknown worksheet: {worksheet}")

    if _use_gsheets():
        _write_gsheet(worksheet, df)
        return

    _write_csv_sheet(worksheet, df)


def append_rows(worksheet: str, rows: list[dict]) -> None:
    if not rows:
        return

    existing = read_sheet(worksheet)
    new_rows = pd.DataFrame(rows)
    combined = pd.concat([existing, new_rows], ignore_index=True)

    write_sheet(worksheet, combined)


def update_row_by_id(worksheet: str, id_col: str, id_value: str, updates: dict) -> None:
    df = read_sheet(worksheet)

    if id_col not in df.columns:
        raise KeyError(f"{id_col} not found in {worksheet}")

    mask = df[id_col].astype(str) == str(id_value)

    if not mask.any():
        raise KeyError(f"{id_value} not found in {worksheet}")

    for key, value in updates.items():
        if key not in df.columns:
            df[key] = ""
        df.loc[mask, key] = "" if value is None else str(value)

    write_sheet(worksheet, df)


def get_request_by_id(request_id: str) -> dict | None:
    df = read_sheet("Requests")
    matches = df[df["request_id"].astype(str) == str(request_id)]

    if matches.empty:
        return None

    return matches.iloc[0].to_dict()


def get_request_by_book_no(book_no: str) -> dict | None:
    df = read_sheet("Requests")

    matches = df[
        (df["book_no"].astype(str).str.strip() == str(book_no).strip())
        & (df["status"].astype(str) != "cancelled")
    ]

    if matches.empty:
        return None

    return matches.iloc[0].to_dict()


def list_request_dates(request_id: str) -> pd.DataFrame:
    df = read_sheet("Request_Dates")
    return df[df["request_id"].astype(str) == str(request_id)].copy()


def list_vehicles(request_id: str, active_only: bool = True) -> pd.DataFrame:
    df = read_sheet("Vehicles")
    result = df[df["request_id"].astype(str) == str(request_id)].copy()

    if active_only:
        result = result[result["status"].astype(str) == "active"]

    return result


def list_guard_tasks(request_id: str | None = None) -> pd.DataFrame:
    df = read_sheet("Guard_Tasks")

    if request_id:
        return df[df["request_id"].astype(str) == str(request_id)].copy()

    return df.copy()


def list_guard_submissions(task_id: str | None = None) -> pd.DataFrame:
    df = read_sheet("Guard_Submissions")

    if task_id:
        return df[df["task_id"].astype(str) == str(task_id)].copy()

    return df.copy()


def validate_storage_schema() -> dict[str, list[str]]:
    """
    Return missing internal fields after Thai-to-English header conversion.

    Returns:
        {} if schema is healthy.
    """
    problems: dict[str, list[str]] = {}

    for worksheet, required_columns in WORKSHEET_SCHEMAS.items():
        df = read_sheet(worksheet)
        missing = [col for col in required_columns if col not in df.columns]

        if missing:
            problems[worksheet] = missing

    return problems
