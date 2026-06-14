from __future__ import annotations

from datetime import datetime

from modules.audit import write_audit_log
from modules.constants import ID_PREFIXES
from modules.dates import to_iso_date, to_month_key
from modules.guard_packages import build_guard_packages, is_guard_job_open, summarize_dates
from modules.ids import make_id
from modules.sheets import (
    append_rows,
    get_request_by_book_no,
    get_request_by_id,
    list_guard_tasks,
    list_request_dates,
    read_sheet,
    update_row_by_id,
)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def create_request(
    *,
    book_no: str,
    book_date: str,
    received_date: str,
    source_agency: str,
    car_count: int,
    parking_location: str,
    parking_dates: list[str],
    parking_time: str = "",
    plates: list[str] | None = None,
    note: str = "",
    book_file_meta: dict | None = None,
    created_by: str = "",
) -> str:
    if get_request_by_book_no(book_no):
        raise ValueError("เลขหนังสือนี้มีอยู่ในระบบแล้ว")

    timestamp = now_iso()
    request_id = make_id(ID_PREFIXES["Requests"])
    clean_plates = [str(plate).strip() for plate in plates or [] if str(plate).strip()]
    book_file_url = (book_file_meta or {}).get("file_url", "")

    request_row = {
        "request_id": request_id,
        "book_no": str(book_no).strip(),
        "book_date": to_iso_date(book_date) if book_date else "",
        "received_date": to_iso_date(received_date),
        "source_agency": source_agency,
        "car_count": int(car_count),
        "parking_location": parking_location,
        "note": note,
        "status": "pending",
        "has_vehicle_plates": "TRUE" if clean_plates else "FALSE",
        "book_file_url": book_file_url,
        "created_by": created_by,
        "created_at": timestamp,
        "updated_at": timestamp,
        "cancelled_at": "",
        "cancelled_by": "",
        "cancelled_reason": "",
    }

    date_rows = []
    request_date_ids = []
    for parking_date in sorted({to_iso_date(value) for value in parking_dates}):
        request_date_id = make_id(ID_PREFIXES["Request_Dates"])
        request_date_ids.append(request_date_id)
        date_rows.append(
            {
                "request_date_id": request_date_id,
                "request_id": request_id,
                "parking_date": parking_date,
                "parking_time": parking_time,
                "month_key": to_month_key(parking_date),
                "status": "pending",
                "created_at": timestamp,
                "cancelled_at": "",
                "cancelled_reason": "",
            }
        )

    clean_dates = [row["parking_date"] for row in date_rows]
    task_rows = [
        {
            "task_id": make_id(ID_PREFIXES["Guard_Tasks"]),
            "request_id": request_id,
            "request_date_id": request_date_ids[0] if request_date_ids else "",
            "parking_date": clean_dates[0] if clean_dates else "",
            "start_date": clean_dates[0] if clean_dates else "",
            "end_date": clean_dates[-1] if clean_dates else "",
            "date_summary": summarize_dates(clean_dates),
            "parking_time": parking_time,
            "date_count": len(clean_dates),
            "source_request_date_ids": "|".join(request_date_ids),
            "parking_location": parking_location,
            "status": "pending",
            "assigned_to": "",
            "submitted_at": "",
            "completed_at": "",
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    ]

    vehicle_rows = [
        {
            "vehicle_id": make_id(ID_PREFIXES["Vehicles"]),
            "request_id": request_id,
            "plate_no": plate,
            "vehicle_note": "",
            "status": "active",
            "created_at": timestamp,
            "cancelled_at": "",
            "cancelled_reason": "",
        }
        for plate in clean_plates
    ]

    append_rows("Requests", [request_row])
    append_rows("Request_Dates", date_rows)
    append_rows("Guard_Tasks", task_rows)
    append_rows("Vehicles", vehicle_rows)

    if book_file_meta and book_file_meta.get("file_url"):
        append_rows(
            "Attachments",
            [
                {
                    "attachment_id": make_id(ID_PREFIXES["Attachments"]),
                    "request_id": request_id,
                    "task_id": "",
                    "file_type": "book",
                    "file_name": book_file_meta.get("file_name", ""),
                    "file_url": book_file_meta.get("file_url", ""),
                    "mime_type": book_file_meta.get("mime_type", ""),
                    "uploaded_by": created_by,
                    "uploaded_at": timestamp,
                    "status": "active",
                }
            ],
        )

    write_audit_log("create_request", "Requests", request_id, new_value=request_row, user=created_by)
    return request_id


def cancel_request(request_id: str, reason: str, user: str = "") -> None:
    request = get_request_by_id(request_id)
    if not request:
        raise ValueError("ไม่พบคำขอ")
    if str(request.get("status", "")) == "cancelled":
        return
    timestamp = now_iso()
    request_updates = {
        "status": "cancelled",
        "cancelled_at": timestamp,
        "cancelled_by": user,
        "cancelled_reason": reason,
        "updated_at": timestamp,
    }
    update_row_by_id("Requests", "request_id", request_id, request_updates)

    for _, row in list_request_dates(request_id).iterrows():
        update_row_by_id(
            "Request_Dates",
            "request_date_id",
            row["request_date_id"],
            {"status": "cancelled", "cancelled_at": timestamp, "cancelled_reason": reason},
        )
    for _, row in list_guard_tasks(request_id).iterrows():
        update_row_by_id(
            "Guard_Tasks",
            "task_id",
            row["task_id"],
            {"status": "cancelled", "updated_at": timestamp},
        )

    vehicles = read_sheet("Vehicles")
    for _, row in vehicles[vehicles["request_id"].astype(str) == str(request_id)].iterrows():
        update_row_by_id(
            "Vehicles",
            "vehicle_id",
            row["vehicle_id"],
            {"status": "cancelled", "cancelled_at": timestamp, "cancelled_reason": reason},
        )
    write_audit_log("cancel_request", "Requests", request_id, old_value=request, new_value=request_updates, user=user)


def cancel_request_date(request_date_id: str, reason: str, user: str = "") -> None:
    dates = read_sheet("Request_Dates")
    match = dates[dates["request_date_id"].astype(str) == str(request_date_id)]
    if match.empty:
        raise ValueError("ไม่พบวันที่จอด")
    timestamp = now_iso()
    request_id = match.iloc[0]["request_id"]
    if str(match.iloc[0].get("status", "")) == "cancelled":
        return
    update_row_by_id(
        "Request_Dates",
        "request_date_id",
        request_date_id,
        {"status": "cancelled", "cancelled_at": timestamp, "cancelled_reason": reason},
    )
    updated_dates = list_request_dates(request_id)
    active_dates = updated_dates[updated_dates["status"].astype(str) != "cancelled"]
    tasks = list_guard_tasks(request_id)

    if active_dates.empty:
        for _, row in tasks[tasks["status"].astype(str) != "cancelled"].iterrows():
            update_row_by_id("Guard_Tasks", "task_id", row["task_id"], {"status": "cancelled", "updated_at": timestamp})
    else:
        active_dates = active_dates.sort_values("parking_date")
        active_ids = set(active_dates["request_date_id"].astype(str).tolist())
        active_values = active_dates["parking_date"].astype(str).tolist()
        parking_times = [str(value).strip() for value in active_dates.get("parking_time", []).tolist() if str(value).strip()]
        task_updates = {
            "request_date_id": active_dates.iloc[0]["request_date_id"],
            "parking_date": active_values[0],
            "start_date": active_values[0],
            "end_date": active_values[-1],
            "date_summary": summarize_dates(active_values),
            "parking_time": parking_times[0] if parking_times else "",
            "date_count": len(active_values),
            "source_request_date_ids": "|".join(active_dates["request_date_id"].astype(str).tolist()),
            "updated_at": timestamp,
        }

        for _, row in tasks.iterrows():
            if str(row.get("status", "")) == "cancelled":
                continue
            source_ids = [
                value
                for value in str(row.get("source_request_date_ids") or row.get("request_date_id") or "").split("|")
                if value
            ]
            if source_ids and request_date_id in source_ids and not active_ids.intersection(source_ids):
                update_row_by_id("Guard_Tasks", "task_id", row["task_id"], {"status": "cancelled", "updated_at": timestamp})
            else:
                update_row_by_id("Guard_Tasks", "task_id", row["task_id"], task_updates)
    write_audit_log("cancel_date", "Request_Dates", request_date_id, new_value={"reason": reason}, user=user)


def cancel_vehicle(vehicle_id: str, reason: str, user: str = "") -> None:
    vehicles = read_sheet("Vehicles")
    match = vehicles[vehicles["vehicle_id"].astype(str) == str(vehicle_id)]
    if match.empty:
        raise ValueError("ไม่พบทะเบียนรถ")
    if str(match.iloc[0].get("status", "")) == "cancelled":
        return

    timestamp = now_iso()
    update_row_by_id(
        "Vehicles",
        "vehicle_id",
        vehicle_id,
        {"status": "cancelled", "cancelled_at": timestamp, "cancelled_reason": reason},
    )
    write_audit_log("cancel_vehicle", "Vehicles", vehicle_id, new_value={"reason": reason}, user=user)


def _package_for_request(request_id: str) -> dict:
    package = build_guard_packages().query("request_id == @request_id")
    if package.empty:
        raise ValueError("ไม่พบงาน รปภ. ของคำขอนี้")
    return package.iloc[0].to_dict()


def _ensure_package_open(package: dict) -> None:
    if not is_guard_job_open(package):
        open_date = package.get("open_date") or "-"
        raise ValueError(f"งานนี้ยังไม่เปิดให้ทำ เปิดให้ทำวันที่ {open_date}")


def submit_guard_task(
    *,
    task_id: str,
    near_photo_meta: dict,
    far_photo_meta: dict,
    extra_photo_meta: dict | None = None,
    note: str = "",
    submitted_by: str = "",
    is_final: bool = True,
) -> str:
    tasks = read_sheet("Guard_Tasks")
    match = tasks[tasks["task_id"].astype(str) == str(task_id)]
    if match.empty:
        raise ValueError("ไม่พบงาน รปภ.")
    task = match.iloc[0].to_dict()
    request = get_request_by_id(task["request_id"])
    if request and str(request.get("status", "")) == "cancelled":
        raise ValueError("คำขอนี้ถูกยกเลิกแล้ว ไม่สามารถส่งงานได้")

    request_tasks = tasks[tasks["request_id"].astype(str) == str(task["request_id"])].copy()
    active_tasks = request_tasks[request_tasks["status"].astype(str) != "cancelled"]
    active_statuses = set(active_tasks["status"].astype(str).tolist())
    if "done" in active_statuses and active_statuses <= {"done"}:
        raise ValueError("งานนี้ปิดแล้ว")
    if "submitted" in active_statuses:
        raise ValueError("งานนี้ส่งแล้ว รอเจ้าหน้าที่ตรวจ")

    timestamp = now_iso()
    submission_id = make_id(ID_PREFIXES["Guard_Submissions"])
    submission_row = {
        "submission_id": submission_id,
        "task_id": task_id,
        "request_id": task["request_id"],
        "near_photo_url": near_photo_meta.get("file_url", ""),
        "far_photo_url": far_photo_meta.get("file_url", ""),
        "extra_photo_url": (extra_photo_meta or {}).get("file_url", ""),
        "note": note,
        "submitted_by": submitted_by,
        "submitted_at": timestamp,
        "is_final": "TRUE" if is_final else "FALSE",
    }
    append_rows("Guard_Submissions", [submission_row])

    attachment_rows = []
    for file_type, meta in [
        ("guard_photo", near_photo_meta),
        ("guard_photo", far_photo_meta),
        ("guard_photo", extra_photo_meta or {}),
    ]:
        if meta.get("file_url"):
            attachment_rows.append(
                {
                    "attachment_id": make_id(ID_PREFIXES["Attachments"]),
                    "request_id": task["request_id"],
                    "task_id": task_id,
                    "file_type": file_type,
                    "file_name": meta.get("file_name", ""),
                    "file_url": meta.get("file_url", ""),
                    "mime_type": meta.get("mime_type", ""),
                    "uploaded_by": submitted_by,
                    "uploaded_at": timestamp,
                    "status": "active",
                }
            )
    append_rows("Attachments", attachment_rows)
    for _, row in active_tasks.iterrows():
        if str(row.get("status", "")) in {"pending", "in_progress"}:
            update_row_by_id(
                "Guard_Tasks",
                "task_id",
                row["task_id"],
                {"status": "submitted", "submitted_at": timestamp, "updated_at": timestamp},
            )
    write_audit_log("submit_guard_task", "Guard_Tasks", task_id, new_value=submission_row, user=submitted_by)
    return submission_id


def accept_guard_package(request_id: str, user: str = "รปภ.") -> None:
    request = get_request_by_id(request_id)
    if request and str(request.get("status", "")) == "cancelled":
        raise ValueError("งานนี้ถูกยกเลิก")

    tasks = list_guard_tasks(request_id)
    if tasks.empty:
        raise ValueError("ไม่พบงาน รปภ.")

    active_tasks = tasks[tasks["status"].astype(str) != "cancelled"]
    active_statuses = set(active_tasks["status"].astype(str).tolist())
    if not active_tasks.empty and active_statuses <= {"in_progress"}:
        return
    if "submitted" in active_statuses:
        raise ValueError("งานนี้ส่งแล้ว")
    if "done" in active_statuses and active_statuses <= {"done"}:
        raise ValueError("งานนี้เสร็จสิ้นแล้ว")
    if active_tasks.empty:
        raise ValueError("งานนี้ถูกยกเลิก")
    if "pending" in active_statuses:
        _ensure_package_open(_package_for_request(request_id))

    timestamp = now_iso()
    changed = 0
    for _, row in active_tasks.iterrows():
        if str(row.get("status", "")) == "pending":
            update_row_by_id(
                "Guard_Tasks",
                "task_id",
                row["task_id"],
                {"status": "in_progress", "assigned_to": user, "updated_at": timestamp},
            )
            changed += 1

    if changed:
        write_audit_log(
            "accept_guard_package",
            "Guard_Tasks",
            request_id,
            new_value={"status": "in_progress", "accepted_by": user},
            user=user,
        )


def submit_guard_package(
    *,
    request_id: str,
    near_photo_meta: dict,
    far_photo_meta: dict,
    extra_photo_meta: dict | None = None,
    note: str = "",
    submitted_by: str = "",
    is_final: bool = True,
) -> str:
    package_row = _package_for_request(request_id)
    status = str(package_row.get("status", ""))
    if status == "cancelled":
        raise ValueError("งานนี้ถูกยกเลิก")
    if status == "done":
        raise ValueError("งานนี้ปิดแล้ว")
    if status == "submitted":
        raise ValueError("งานนี้ส่งแล้ว รอเจ้าหน้าที่ตรวจ")
    if status in {"pending", "in_progress"}:
        _ensure_package_open(package_row)
    if status == "pending":
        accept_guard_package(request_id, user=submitted_by or "รปภ.")
    task_id = str(package_row["primary_task_id"])
    return submit_guard_task(
        task_id=task_id,
        near_photo_meta=near_photo_meta,
        far_photo_meta=far_photo_meta,
        extra_photo_meta=extra_photo_meta,
        note=note,
        submitted_by=submitted_by,
        is_final=is_final,
    )


def mark_guard_package_done(request_id: str, user: str = "") -> None:
    request = get_request_by_id(request_id)
    if request and str(request.get("status", "")) == "cancelled":
        raise ValueError("คำขอนี้ถูกยกเลิกแล้ว")

    tasks = list_guard_tasks(request_id)
    if tasks.empty:
        raise ValueError("ไม่พบงาน รปภ.")

    active_tasks = tasks[tasks["status"].astype(str) != "cancelled"]
    if active_tasks.empty or set(active_tasks["status"].astype(str).tolist()) <= {"done"}:
        return

    timestamp = now_iso()
    for _, row in active_tasks.iterrows():
        update_row_by_id(
            "Guard_Tasks",
            "task_id",
            row["task_id"],
            {"status": "done", "completed_at": timestamp, "updated_at": timestamp},
        )

    for _, row in list_request_dates(request_id).iterrows():
        if str(row.get("status", "")) != "cancelled":
            update_row_by_id(
                "Request_Dates",
                "request_date_id",
                row["request_date_id"],
                {"status": "done"},
            )

    if request and str(request.get("status", "")) != "done":
        update_row_by_id("Requests", "request_id", request_id, {"status": "done", "updated_at": timestamp})

    write_audit_log("mark_done", "Requests", request_id, new_value={"status": "done"}, user=user)


def mark_task_done(task_id: str, user: str = "") -> None:
    tasks = read_sheet("Guard_Tasks")
    match = tasks[tasks["task_id"].astype(str) == str(task_id)]
    if match.empty:
        raise ValueError("ไม่พบงาน รปภ.")
    mark_guard_package_done(str(match.iloc[0]["request_id"]), user=user)


def set_guard_package_status(
    request_id: str,
    status: str,
    *,
    reason: str = "",
    user: str = "แอดมิน",
) -> None:
    valid_statuses = {"pending", "in_progress", "submitted", "done", "cancelled"}
    if status not in valid_statuses:
        raise ValueError("สถานะไม่ถูกต้อง")
    if status == "cancelled" and not str(reason or "").strip():
        raise ValueError("กรุณาระบุเหตุผลยกเลิก")
    if status == "done":
        mark_guard_package_done(request_id, user=user)
        return

    request = get_request_by_id(request_id)
    if request and str(request.get("status", "")) == "cancelled" and status != "cancelled":
        raise ValueError("คำขอนี้ถูกยกเลิกแล้ว")

    tasks = list_guard_tasks(request_id)
    if tasks.empty:
        raise ValueError("ไม่พบงาน รปภ.")

    active_tasks = tasks if status == "cancelled" else tasks[tasks["status"].astype(str) != "cancelled"]
    if active_tasks.empty:
        return

    current_statuses = set(active_tasks["status"].astype(str).tolist())
    if current_statuses <= {status}:
        return

    timestamp = now_iso()
    updates = {"status": status, "updated_at": timestamp}
    if status in {"pending", "in_progress"}:
        updates.update({"submitted_at": "", "completed_at": ""})
    if status == "submitted":
        updates.update({"submitted_at": timestamp, "completed_at": ""})
    if status == "cancelled":
        updates.update({"completed_at": "", "submitted_at": ""})

    for _, row in active_tasks.iterrows():
        update_row_by_id("Guard_Tasks", "task_id", row["task_id"], updates)

    write_audit_log(
        "override_guard_package_status",
        "Guard_Tasks",
        request_id,
        old_value={"statuses": sorted(current_statuses)},
        new_value={"status": status, "reason": reason},
        user=user,
    )


def repair_guard_task_packages(user: str = "admin") -> int:
    tasks = read_sheet("Guard_Tasks")
    if tasks.empty:
        return 0

    packages = build_guard_packages(tasks=tasks)
    repaired = 0
    for _, package in packages.iterrows():
        updates = {
            "start_date": package.get("start_date", ""),
            "end_date": package.get("end_date", ""),
            "date_summary": package.get("date_summary", ""),
            "parking_time": package.get("parking_time", ""),
            "date_count": package.get("date_count", ""),
            "source_request_date_ids": package.get("source_request_date_ids", ""),
        }
        for task_id in str(package.get("task_ids", "")).split("|"):
            if task_id:
                update_row_by_id("Guard_Tasks", "task_id", task_id, updates)
                repaired += 1

    write_audit_log(
        "repair_guard_packages",
        "Guard_Tasks",
        "all",
        new_value={"repaired_rows": repaired},
        user=user,
    )
    return repaired
