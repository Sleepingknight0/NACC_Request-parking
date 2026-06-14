from __future__ import annotations

from modules import sheets
from modules.db import create_request
from modules.guard_packages import build_guard_packages
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
