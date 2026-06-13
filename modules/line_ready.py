from __future__ import annotations

import pandas as pd

from modules.sheets import read_sheet


def _tasks_with_requests() -> pd.DataFrame:
    tasks = read_sheet("Guard_Tasks")
    requests = read_sheet("Requests")
    if tasks.empty:
        return tasks
    return tasks.merge(requests, on="request_id", how="left", suffixes=("", "_request"))


def get_today_tasks_for_line() -> list[dict]:
    today = pd.Timestamp.today().date().isoformat()
    df = _tasks_with_requests()
    if df.empty:
        return []
    return df[df["parking_date"].astype(str) == today].to_dict("records")


def get_pending_tasks_for_line() -> list[dict]:
    df = _tasks_with_requests()
    if df.empty:
        return []
    return df[df["status"].astype(str).isin(["pending", "in_progress"])].to_dict("records")


def search_task_for_line(query: str) -> list[dict]:
    df = _tasks_with_requests()
    text = str(query or "").strip().lower()
    if df.empty or not text:
        return []
    haystack_cols = ["book_no", "source_agency", "parking_location", "request_id"]
    mask = False
    for col in haystack_cols:
        if col in df.columns:
            mask = mask | df[col].astype(str).str.lower().str.contains(text, regex=False)
    return df[mask].to_dict("records")


def format_task_line_message(tasks: list[dict]) -> str:
    if not tasks:
        return "ไม่พบงานที่ตรงกับเงื่อนไข"
    lines = ["งานที่จอดรถ"]
    for index, task in enumerate(tasks, start=1):
        lines.extend(
            [
                "",
                f"{index}. {task.get('source_agency', '-')}",
                f"   อาคาร: {task.get('parking_location', '-')}",
                f"   วันที่: {task.get('parking_date', '-')}",
                f"   จำนวน: {task.get('car_count', '-')} คัน",
                f"   สถานะ: {task.get('status', '-')}",
            ]
        )
    return "\n".join(lines)
