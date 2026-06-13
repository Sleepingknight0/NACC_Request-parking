from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from modules.constants import WORKSHEET_SCHEMAS


DATA_DIR = Path(os.getenv("PARKING_APP_DATA_DIR", "data"))


def _path_for(worksheet: str) -> Path:
    if worksheet not in WORKSHEET_SCHEMAS:
        raise KeyError(f"Unknown worksheet: {worksheet}")
    return DATA_DIR / f"{worksheet}.csv"


def _empty_df(worksheet: str) -> pd.DataFrame:
    return pd.DataFrame(columns=WORKSHEET_SCHEMAS[worksheet])


def _normalize_columns(worksheet: str, df: pd.DataFrame) -> pd.DataFrame:
    for column in WORKSHEET_SCHEMAS[worksheet]:
        if column not in df.columns:
            df[column] = ""
    extra_cols = [col for col in df.columns if col not in WORKSHEET_SCHEMAS[worksheet]]
    return df[WORKSHEET_SCHEMAS[worksheet] + extra_cols].fillna("")


def initialize_storage() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for worksheet in WORKSHEET_SCHEMAS:
        path = _path_for(worksheet)
        if not path.exists():
            _empty_df(worksheet).to_csv(path, index=False, encoding="utf-8-sig")


def get_connection():
    """Reserved for future Google Sheets connection wiring."""
    return None


def read_sheet(worksheet: str, ttl: int = 0) -> pd.DataFrame:
    initialize_storage()
    path = _path_for(worksheet)
    if path.stat().st_size == 0:
        return _empty_df(worksheet)
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return _normalize_columns(worksheet, df)


def write_sheet(worksheet: str, df: pd.DataFrame) -> None:
    initialize_storage()
    normalized = _normalize_columns(worksheet, df.copy())
    normalized.to_csv(_path_for(worksheet), index=False, encoding="utf-8-sig")


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
