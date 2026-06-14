from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from modules.dates import to_iso_date
from modules.sheets import read_sheet


PACKAGE_COLUMNS = [
    "request_id",
    "book_no",
    "source_agency",
    "parking_location",
    "car_count",
    "status",
    "primary_task_id",
    "task_ids",
    "task_count",
    "parking_date",
    "start_date",
    "end_date",
    "date_summary",
    "parking_time",
    "date_count",
    "source_request_date_ids",
    "plate_summary",
    "submitted_at",
    "completed_at",
    "open_date",
    "is_open",
]


def _clean_dates(values) -> list[str]:
    dates: set[str] = set()
    for value in values:
        try:
            dates.add(to_iso_date(value))
        except Exception:
            text = str(value or "").strip()
            if text:
                dates.add(text[:10])
    return sorted(dates)


def summarize_dates(values) -> str:
    dates = _clean_dates(values)
    if not dates:
        return "-"
    if len(dates) == 1:
        return dates[0]

    parsed = []
    for value in dates:
        try:
            parsed.append(pd.Timestamp(value).date())
        except Exception:
            parsed = []
            break

    if parsed:
        expected = [parsed[0] + timedelta(days=index) for index in range(len(parsed))]
        if parsed == expected:
            return f"{dates[0]} ถึง {dates[-1]} ({len(dates)} วัน)"

    if len(dates) <= 4:
        return f"{', '.join(dates)} ({len(dates)} วัน)"
    return f"{dates[0]} ถึง {dates[-1]} ({len(dates)} วัน)"


def guard_open_date(package_or_start_date) -> str:
    if isinstance(package_or_start_date, dict):
        raw_value = package_or_start_date.get("start_date") or package_or_start_date.get("parking_date")
    else:
        raw_value = package_or_start_date
    try:
        start = pd.Timestamp(to_iso_date(raw_value)).date()
    except Exception:
        return ""
    return (start - timedelta(days=1)).isoformat()


def is_guard_job_open(package: dict, today=None) -> bool:
    if today is None:
        today_date = date.today()
    else:
        today_date = pd.Timestamp(to_iso_date(today)).date()

    open_value = guard_open_date(package)
    if not open_value:
        return False
    return today_date >= pd.Timestamp(open_value).date()


def _package_status(task_statuses: list[str], request_status: str = "") -> str:
    if request_status == "cancelled":
        return "cancelled"

    statuses = [str(status or "").strip() for status in task_statuses if str(status or "").strip()]
    if not statuses:
        return request_status or "pending"
    if all(status == "cancelled" for status in statuses):
        return "cancelled"

    active_statuses = [status for status in statuses if status != "cancelled"]
    if active_statuses and all(status == "done" for status in active_statuses):
        return "done"
    if "submitted" in active_statuses:
        return "submitted"
    if "in_progress" in active_statuses:
        return "in_progress"
    if "pending" in active_statuses:
        return "pending"
    if "done" in active_statuses:
        return "done"
    return active_statuses[0] if active_statuses else "pending"


def _primary_task_id(tasks: pd.DataFrame) -> str:
    if tasks.empty or "task_id" not in tasks.columns:
        return ""
    priority = {"submitted": 0, "in_progress": 1, "pending": 2, "done": 3, "cancelled": 4}
    ordered = tasks.copy()
    ordered["_priority"] = ordered["status"].map(lambda value: priority.get(str(value), 9))
    ordered = ordered.sort_values(["_priority", "parking_date", "created_at"], ascending=[True, True, True])
    return str(ordered.iloc[0].get("task_id", ""))


def build_guard_packages(
    *,
    requests: pd.DataFrame | None = None,
    dates: pd.DataFrame | None = None,
    tasks: pd.DataFrame | None = None,
    vehicles: pd.DataFrame | None = None,
    include_cancelled: bool = True,
) -> pd.DataFrame:
    requests = read_sheet("Requests") if requests is None else requests
    dates = read_sheet("Request_Dates") if dates is None else dates
    tasks = read_sheet("Guard_Tasks") if tasks is None else tasks
    vehicles = read_sheet("Vehicles") if vehicles is None else vehicles

    if tasks.empty or "request_id" not in tasks.columns:
        return pd.DataFrame(columns=PACKAGE_COLUMNS)

    rows: list[dict] = []
    request_lookup = {
        str(row.get("request_id", "")): row
        for row in requests.to_dict(orient="records")
    } if not requests.empty else {}

    for request_id, task_group in tasks.groupby(tasks["request_id"].astype(str), dropna=False):
        request = request_lookup.get(str(request_id), {})
        request_status = str(request.get("status", ""))
        status = _package_status(task_group.get("status", pd.Series(dtype=str)).astype(str).tolist(), request_status)
        if not include_cancelled and status == "cancelled":
            continue

        request_dates = dates[dates["request_id"].astype(str) == str(request_id)].copy() if not dates.empty else pd.DataFrame()
        active_dates = request_dates[request_dates["status"].astype(str) != "cancelled"] if not request_dates.empty else request_dates
        date_source = active_dates if not active_dates.empty else request_dates
        date_values = date_source["parking_date"].tolist() if not date_source.empty else task_group["parking_date"].tolist()
        clean_dates = _clean_dates(date_values)

        request_date_ids = (
            date_source["request_date_id"].astype(str).tolist()
            if not date_source.empty and "request_date_id" in date_source.columns
            else task_group.get("request_date_id", pd.Series(dtype=str)).astype(str).tolist()
        )
        parking_times = (
            [str(value).strip() for value in date_source.get("parking_time", pd.Series(dtype=str)).tolist() if str(value).strip()]
            if not date_source.empty else []
        )
        if not parking_times:
            parking_times = [str(value).strip() for value in task_group.get("parking_time", pd.Series(dtype=str)).tolist() if str(value).strip()]

        request_vehicles = vehicles[vehicles["request_id"].astype(str) == str(request_id)].copy() if not vehicles.empty else pd.DataFrame()
        active_plates = (
            request_vehicles[request_vehicles["status"].astype(str) != "cancelled"]["plate_no"].astype(str).tolist()
            if not request_vehicles.empty and "plate_no" in request_vehicles.columns
            else []
        )
        clean_plates = [plate for plate in active_plates if str(plate).strip()]

        rows.append(
            {
                "request_id": request_id,
                "book_no": request.get("book_no", "") or request_id,
                "source_agency": request.get("source_agency", "ไม่ระบุสำนัก"),
                "parking_location": request.get("parking_location", "") or task_group.iloc[0].get("parking_location", ""),
                "car_count": request.get("car_count", ""),
                "status": status,
                "primary_task_id": _primary_task_id(task_group),
                "task_ids": "|".join(task_group["task_id"].astype(str).tolist()),
                "task_count": len(task_group),
                "parking_date": clean_dates[0] if clean_dates else "",
                "start_date": clean_dates[0] if clean_dates else "",
                "end_date": clean_dates[-1] if clean_dates else "",
                "date_summary": summarize_dates(clean_dates),
                "parking_time": parking_times[0] if parking_times else "",
                "date_count": len(clean_dates),
                "source_request_date_ids": "|".join([value for value in request_date_ids if value]),
                "plate_summary": ", ".join(clean_plates) if clean_plates else "ไม่มีทะเบียน",
                "submitted_at": max([str(value) for value in task_group.get("submitted_at", pd.Series(dtype=str)).tolist() if str(value)], default=""),
                "completed_at": max([str(value) for value in task_group.get("completed_at", pd.Series(dtype=str)).tolist() if str(value)], default=""),
            }
        )

    result = pd.DataFrame(rows)
    if result.empty:
        return pd.DataFrame(columns=PACKAGE_COLUMNS)

    result["open_date"] = result.apply(lambda row: guard_open_date(row.to_dict()), axis=1)
    result["is_open"] = result.apply(lambda row: is_guard_job_open(row.to_dict()), axis=1)
    result = result.reindex(columns=PACKAGE_COLUMNS).fillna("")
    result = result.sort_values(["parking_date", "book_no"], ascending=[True, True]).reset_index(drop=True)
    return result


def get_guard_package(*, request_id: str | None = None, task_id: str | None = None) -> dict | None:
    packages = build_guard_packages()
    if request_id:
        matches = packages[packages["request_id"].astype(str) == str(request_id)]
    elif task_id:
        matches = packages[packages["task_ids"].astype(str).str.split("|").map(lambda values: str(task_id) in values)]
    else:
        matches = packages.iloc[0:0]

    if matches.empty:
        return None
    return matches.iloc[0].to_dict()
