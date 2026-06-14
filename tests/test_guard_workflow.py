from __future__ import annotations

from modules import sheets
from modules.db import accept_guard_package, create_request
from modules.guard_packages import build_guard_packages, guard_open_date, is_guard_job_open
from modules.sheets import initialize_storage, read_sheet


def test_create_request_creates_one_guard_task_for_multi_day_request(tmp_path, monkeypatch):
    monkeypatch.setenv("PARKING_APP_STORAGE_BACKEND", "csv")
    monkeypatch.setattr(sheets, "DATA_DIR", tmp_path)

    initialize_storage()
    request_id = create_request(
        book_no="TEST-ONE-PACKAGE",
        book_date="2026-06-14",
        received_date="2026-06-14",
        source_agency="สำนักบริหารงานกลาง",
        car_count=2,
        parking_location="หน้าอาคาร 3",
        parking_dates=["2026-06-14", "2026-06-15", "2026-06-16"],
        parking_time="08:30-16:30",
        plates=["กข 1234"],
        created_by="tester",
    )

    dates = read_sheet("Request_Dates")
    tasks = read_sheet("Guard_Tasks")
    packages = build_guard_packages()

    assert len(dates[dates["request_id"] == request_id]) == 3
    assert len(tasks[tasks["request_id"] == request_id]) == 1
    task = tasks[tasks["request_id"] == request_id].iloc[0]
    assert task["date_count"] == "3"
    assert task["date_summary"] == "2026-06-14 ถึง 2026-06-16 (3 วัน)"

    package = packages[packages["request_id"] == request_id].iloc[0]
    assert package["book_no"] == "TEST-ONE-PACKAGE"
    assert package["primary_task_id"] == task["task_id"]
    assert package["open_date"] == "2026-06-13"


def test_guard_job_opens_one_day_before_start_date():
    package = {"start_date": "2026-06-20"}

    assert guard_open_date(package) == "2026-06-19"
    assert is_guard_job_open(package, today="2026-06-18") is False
    assert is_guard_job_open(package, today="2026-06-19") is True
    assert is_guard_job_open(package, today="2026-06-20") is True


def test_accept_guard_package_marks_in_progress_once(tmp_path, monkeypatch):
    monkeypatch.setenv("PARKING_APP_STORAGE_BACKEND", "csv")
    monkeypatch.setattr(sheets, "DATA_DIR", tmp_path)

    initialize_storage()
    request_id = create_request(
        book_no="TEST-ACCEPT-PACKAGE",
        book_date="2026-06-14",
        received_date="2026-06-14",
        source_agency="สำนักบริหารงานกลาง",
        car_count=1,
        parking_location="หน้าอาคาร 3",
        parking_dates=["2026-06-14", "2026-06-15"],
        parking_time="08:30-16:30",
        plates=[],
        created_by="tester",
    )

    accept_guard_package(request_id, user="รปภ.")
    accept_guard_package(request_id, user="รปภ.")

    tasks = read_sheet("Guard_Tasks")
    request_tasks = tasks[tasks["request_id"] == request_id]
    assert len(request_tasks) == 1
    assert request_tasks.iloc[0]["status"] == "in_progress"
    assert request_tasks.iloc[0]["assigned_to"] == "รปภ."

    audit = read_sheet("Audit_Log")
    accept_rows = audit[
        (audit["target_id"] == request_id)
        & (audit["action"] == "accept_guard_package")
    ]
    assert len(accept_rows) == 1
