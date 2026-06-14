from __future__ import annotations

import pytest

from modules import sheets
from modules.db import (
    accept_guard_package,
    cancel_request,
    cancel_request_date,
    cancel_requests,
    cancel_vehicle,
    create_request,
    mark_guard_package_done,
    set_guard_package_status,
    submit_guard_package,
)
from modules.sheets import initialize_storage, read_sheet


def _setup_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("PARKING_APP_STORAGE_BACKEND", "csv")
    monkeypatch.setattr(sheets, "DATA_DIR", tmp_path)
    initialize_storage()


def _create_request(tmp_path, monkeypatch, *, book_no="QA-STATUS", dates=None, plates=None):
    _setup_storage(tmp_path, monkeypatch)
    return create_request(
        book_no=book_no,
        book_date="2026-06-14",
        received_date="2026-06-14",
        source_agency="สำนักบริหารงานกลาง",
        car_count=max(1, len(plates or [])),
        parking_location="หน้าอาคาร 3",
        parking_dates=dates or ["2026-06-20"],
        parking_time="08:30-16:30",
        plates=plates or [],
        created_by="tester",
    )


def _photo(name):
    return {"file_url": f"uploads/guard_submissions/{name}.jpg", "file_name": f"{name}.jpg", "mime_type": "image/jpeg"}


def test_accept_pending_package_changes_to_in_progress_once(tmp_path, monkeypatch):
    request_id = _create_request(tmp_path, monkeypatch, dates=["2026-06-14"])

    accept_guard_package(request_id, user="รปภ.")
    accept_guard_package(request_id, user="รปภ.")

    task = read_sheet("Guard_Tasks").iloc[0]
    assert task["status"] == "in_progress"
    assert task["assigned_to"] == "รปภ."
    audit = read_sheet("Audit_Log")
    assert len(audit[audit["action"] == "accept_guard_package"]) == 1


def test_accept_not_yet_open_package_is_blocked(tmp_path, monkeypatch):
    request_id = _create_request(tmp_path, monkeypatch, dates=["2099-06-20"])

    with pytest.raises(ValueError, match="เปิดให้ทำวันที่"):
        accept_guard_package(request_id, user="รปภ.")


def test_submit_in_progress_package_changes_to_submitted(tmp_path, monkeypatch):
    request_id = _create_request(tmp_path, monkeypatch, dates=["2026-06-14"])
    accept_guard_package(request_id, user="รปภ.")

    submit_guard_package(
        request_id=request_id,
        near_photo_meta=_photo("near"),
        far_photo_meta=_photo("far"),
        submitted_by="รปภ.",
    )

    task = read_sheet("Guard_Tasks").iloc[0]
    assert task["status"] == "submitted"
    assert len(read_sheet("Guard_Submissions")) == 1
    assert len(read_sheet("Attachments")) == 2


def test_submit_not_yet_open_package_is_blocked(tmp_path, monkeypatch):
    request_id = _create_request(tmp_path, monkeypatch, dates=["2099-06-20"])

    with pytest.raises(ValueError, match="เปิดให้ทำวันที่"):
        submit_guard_package(
            request_id=request_id,
            near_photo_meta=_photo("near"),
            far_photo_meta=_photo("far"),
            submitted_by="รปภ.",
        )


def test_submit_done_and_cancelled_packages_are_blocked(tmp_path, monkeypatch):
    done_request_id = _create_request(tmp_path / "done", monkeypatch, book_no="QA-DONE", dates=["2026-06-14"])
    set_guard_package_status(done_request_id, "submitted", user="admin")
    mark_guard_package_done(done_request_id, user="admin")
    with pytest.raises(ValueError, match="ปิดแล้ว|เสร็จ"):
        submit_guard_package(
            request_id=done_request_id,
            near_photo_meta=_photo("near"),
            far_photo_meta=_photo("far"),
            submitted_by="รปภ.",
        )

    cancelled_request_id = _create_request(tmp_path / "cancelled", monkeypatch, book_no="QA-CANCELLED", dates=["2026-06-14"])
    cancel_request(cancelled_request_id, "test", user="admin")
    with pytest.raises(ValueError, match="ยกเลิก"):
        submit_guard_package(
            request_id=cancelled_request_id,
            near_photo_meta=_photo("near"),
            far_photo_meta=_photo("far"),
            submitted_by="รปภ.",
        )


def test_mark_done_submitted_package_is_idempotent(tmp_path, monkeypatch):
    request_id = _create_request(tmp_path, monkeypatch, dates=["2026-06-14"])
    set_guard_package_status(request_id, "submitted", user="admin")

    mark_guard_package_done(request_id, user="admin")
    mark_guard_package_done(request_id, user="admin")

    task = read_sheet("Guard_Tasks").iloc[0]
    audit = read_sheet("Audit_Log")
    assert task["status"] == "done"
    assert len(audit[audit["action"] == "mark_done"]) == 1


def test_cancel_request_is_idempotent(tmp_path, monkeypatch):
    request_id = _create_request(tmp_path, monkeypatch, dates=["2026-06-14"])

    cancel_request(request_id, "test", user="admin")
    cancel_request(request_id, "test", user="admin")

    requests = read_sheet("Requests")
    audit = read_sheet("Audit_Log")
    assert requests.iloc[0]["status"] == "cancelled"
    assert len(audit[audit["action"] == "cancel_request"]) == 1


def test_cancel_requests_batches_and_is_idempotent(tmp_path, monkeypatch):
    first_request_id = _create_request(
        tmp_path,
        monkeypatch,
        book_no="QA-PROD-BATCH-1",
        dates=["2026-06-14"],
        plates=["TEST1"],
    )
    second_request_id = _create_request(
        tmp_path,
        monkeypatch,
        book_no="QA-PROD-BATCH-2",
        dates=["2026-06-15"],
        plates=["TEST2"],
    )

    cancelled = cancel_requests(
        [first_request_id, second_request_id],
        "qa cleanup",
        user="admin",
    )
    repeated = cancel_requests(
        [first_request_id, second_request_id],
        "qa cleanup",
        user="admin",
    )

    assert cancelled == 2
    assert repeated == 0

    request_statuses = read_sheet("Requests").set_index("request_id")["status"].to_dict()
    assert request_statuses[first_request_id] == "cancelled"
    assert request_statuses[second_request_id] == "cancelled"

    for worksheet in ["Request_Dates", "Guard_Tasks", "Vehicles"]:
        df = read_sheet(worksheet)
        statuses = set(df[df["request_id"].isin([first_request_id, second_request_id])]["status"])
        assert statuses == {"cancelled"}

    audit = read_sheet("Audit_Log")
    audit_rows = audit[
        (audit["action"] == "cancel_request")
        & (audit["target_id"].isin([first_request_id, second_request_id]))
    ]
    assert len(audit_rows) == 2


def test_cancel_one_date_keeps_one_package_active_when_other_dates_remain(tmp_path, monkeypatch):
    request_id = _create_request(
        tmp_path,
        monkeypatch,
        dates=["2026-06-14", "2026-06-15", "2026-06-16"],
    )
    dates = read_sheet("Request_Dates").sort_values("parking_date")

    cancel_request_date(dates.iloc[0]["request_date_id"], "test", user="admin")

    tasks = read_sheet("Guard_Tasks")
    task = tasks[tasks["request_id"] == request_id].iloc[0]
    assert task["status"] == "pending"
    assert task["start_date"] == "2026-06-15"
    assert task["end_date"] == "2026-06-16"
    assert task["date_count"] == "2"


def test_cancel_vehicle_is_idempotent(tmp_path, monkeypatch):
    _create_request(tmp_path, monkeypatch, dates=["2026-06-14"], plates=["TEST1"])
    vehicle_id = read_sheet("Vehicles").iloc[0]["vehicle_id"]

    cancel_vehicle(vehicle_id, "test", user="admin")
    cancel_vehicle(vehicle_id, "test", user="admin")

    vehicles = read_sheet("Vehicles")
    audit = read_sheet("Audit_Log")
    assert vehicles.iloc[0]["status"] == "cancelled"
    assert len(audit[audit["action"] == "cancel_vehicle"]) == 1
