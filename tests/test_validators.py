from modules.validators import (
    validate_book_no,
    validate_car_count,
    validate_guard_submission,
    validate_location,
    validate_parking_dates,
    validate_plates,
)


def test_validate_book_no_requires_non_empty_value():
    assert validate_book_no(" ปช 0001/1234 ") == (True, None)
    ok, message = validate_book_no(" ")
    assert ok is False
    assert "เลขหนังสือ" in message


def test_validate_car_count_requires_at_least_one_car():
    assert validate_car_count(1) == (True, None)
    ok, message = validate_car_count(0)
    assert ok is False
    assert "จำนวนรถ" in message


def test_validate_parking_dates_requires_at_least_one_date():
    assert validate_parking_dates(["2026-06-13"]) == (True, None)
    ok, message = validate_parking_dates([])
    assert ok is False
    assert "วันที่จอด" in message


def test_validate_location_requires_other_location_text():
    assert validate_location("หน้าอาคาร 3", "") == (True, None)
    ok, message = validate_location("อื่นๆ (ระบุเพิ่มเติม)", " ")
    assert ok is False
    assert "จุดจอด" in message


def test_validate_plates_normalizes_and_blocks_duplicates():
    assert validate_plates(["กข 1234", "ขค 5555"], car_count=2) == (True, None)
    ok, message = validate_plates(["กข 1234", " กข 1234 "], car_count=2)
    assert ok is False
    assert "ซ้ำ" in message


def test_validate_plates_requires_at_least_one_plate_when_enabled():
    ok, message = validate_plates(["", "  "], car_count=2)
    assert ok is False
    assert "ทะเบียน" in message


def test_validate_guard_submission_requires_near_and_far_photos():
    assert validate_guard_submission(object(), object()) == (True, None)
    ok, message = validate_guard_submission(None, object())
    assert ok is False
    assert "รูปใกล้" in message
