from __future__ import annotations

import pandas as pd

from modules.guard_packages import build_guard_packages, guard_open_date, is_guard_job_open


def test_one_request_with_many_dates_builds_one_package():
    requests = pd.DataFrame(
        [
            {
                "request_id": "REQ-1",
                "book_no": "QA-PROD-PACKAGE",
                "source_agency": "สำนักทดสอบ",
                "parking_location": "หน้าอาคาร 3",
                "car_count": "3",
                "status": "pending",
            }
        ]
    )
    dates = pd.DataFrame(
        [
            {"request_date_id": "DATE-1", "request_id": "REQ-1", "parking_date": "2026-06-20", "parking_time": "08:30-16:30", "status": "pending"},
            {"request_date_id": "DATE-2", "request_id": "REQ-1", "parking_date": "2026-06-21", "parking_time": "08:30-16:30", "status": "pending"},
            {"request_date_id": "DATE-3", "request_id": "REQ-1", "parking_date": "2026-06-22", "parking_time": "08:30-16:30", "status": "pending"},
        ]
    )
    tasks = pd.DataFrame(
        [
            {
                "task_id": "TASK-1",
                "request_id": "REQ-1",
                "request_date_id": "DATE-1",
                "parking_date": "2026-06-20",
                "status": "pending",
                "created_at": "2026-06-14T08:00:00",
            }
        ]
    )
    vehicles = pd.DataFrame(
        [
            {"vehicle_id": "VEH-1", "request_id": "REQ-1", "plate_no": "TEST1", "status": "active"},
            {"vehicle_id": "VEH-2", "request_id": "REQ-1", "plate_no": "TEST2", "status": "active"},
            {"vehicle_id": "VEH-3", "request_id": "REQ-1", "plate_no": "TEST3", "status": "active"},
        ]
    )

    packages = build_guard_packages(requests=requests, dates=dates, tasks=tasks, vehicles=vehicles)

    assert len(packages) == 1
    package = packages.iloc[0]
    assert package["book_no"] == "QA-PROD-PACKAGE"
    assert package["date_count"] == 3
    assert package["date_summary"] == "2026-06-20 ถึง 2026-06-22 (3 วัน)"
    assert package["plate_summary"] == "TEST1, TEST2, TEST3"


def test_package_status_uses_operational_priority():
    requests = pd.DataFrame([{"request_id": "REQ-1", "book_no": "QA", "status": "pending"}])
    dates = pd.DataFrame([{"request_date_id": "DATE-1", "request_id": "REQ-1", "parking_date": "2026-06-20", "status": "pending"}])
    tasks = pd.DataFrame(
        [
            {"task_id": "TASK-1", "request_id": "REQ-1", "parking_date": "2026-06-20", "status": "done", "created_at": "1"},
            {"task_id": "TASK-2", "request_id": "REQ-1", "parking_date": "2026-06-20", "status": "submitted", "created_at": "2"},
        ]
    )

    packages = build_guard_packages(requests=requests, dates=dates, tasks=tasks, vehicles=pd.DataFrame())

    assert packages.iloc[0]["status"] == "submitted"
    assert packages.iloc[0]["primary_task_id"] == "TASK-2"


def test_orphan_tasks_are_not_operational_packages():
    requests = pd.DataFrame([{"request_id": "REQ-1", "book_no": "QA", "status": "pending"}])
    dates = pd.DataFrame([{"request_date_id": "DATE-1", "request_id": "REQ-1", "parking_date": "2026-06-20", "status": "pending"}])
    tasks = pd.DataFrame(
        [
            {"task_id": "TASK-1", "request_id": "REQ-1", "parking_date": "2026-06-20", "status": "pending", "created_at": "1"},
            {"task_id": "TASK-ORPHAN", "request_id": "", "parking_date": "", "status": "pending", "created_at": "2"},
            {"task_id": "TASK-MISSING", "request_id": "REQ-MISSING", "parking_date": "2026-06-21", "status": "pending", "created_at": "3"},
        ]
    )

    packages = build_guard_packages(requests=requests, dates=dates, tasks=tasks, vehicles=pd.DataFrame())

    assert len(packages) == 1
    assert packages.iloc[0]["request_id"] == "REQ-1"


def test_guard_open_date_is_start_date_minus_one_day():
    package = {"start_date": "2026-06-20"}

    assert guard_open_date(package) == "2026-06-19"
    assert is_guard_job_open(package, today="2026-06-18") is False
    assert is_guard_job_open(package, today="2026-06-19") is True


def test_cancelled_packages_can_be_hidden():
    requests = pd.DataFrame([{"request_id": "REQ-1", "book_no": "QA", "status": "cancelled"}])
    dates = pd.DataFrame([{"request_date_id": "DATE-1", "request_id": "REQ-1", "parking_date": "2026-06-20", "status": "cancelled"}])
    tasks = pd.DataFrame([{"task_id": "TASK-1", "request_id": "REQ-1", "parking_date": "2026-06-20", "status": "cancelled", "created_at": "1"}])

    packages = build_guard_packages(
        requests=requests,
        dates=dates,
        tasks=tasks,
        vehicles=pd.DataFrame(),
        include_cancelled=False,
    )

    assert packages.empty
