from __future__ import annotations


OTHER_LABEL = "อื่นๆ (ระบุเพิ่มเติม)"


def _clean_values(values: list[str]) -> list[str]:
    return [str(value).strip() for value in values if str(value).strip()]


def validate_book_no(book_no: str) -> tuple[bool, str | None]:
    if not str(book_no or "").strip():
        return False, "กรุณาระบุเลขหนังสือ"
    return True, None


def validate_car_count(count: int) -> tuple[bool, str | None]:
    try:
        value = int(count)
    except (TypeError, ValueError):
        return False, "จำนวนรถต้องเป็นตัวเลข"
    if value < 1:
        return False, "จำนวนรถต้องไม่น้อยกว่า 1 คัน"
    return True, None


def validate_parking_dates(dates: list[str]) -> tuple[bool, str | None]:
    if not dates:
        return False, "กรุณาระบุวันที่จอดอย่างน้อย 1 วัน"
    return True, None


def validate_location(selected_loc: str, other_loc: str | None) -> tuple[bool, str | None]:
    selected = str(selected_loc or "").strip()
    if not selected:
        return False, "กรุณาระบุจุดจอด"
    if selected == OTHER_LABEL and not str(other_loc or "").strip():
        return False, "กรุณาระบุรายละเอียดจุดจอดอื่นๆ"
    return True, None


def validate_plates(plates: list[str], car_count: int) -> tuple[bool, str | None]:
    cleaned = _clean_values(plates)
    if not cleaned:
        return False, "กรุณาระบุทะเบียนรถอย่างน้อย 1 รายการ"
    normalized = [plate.replace(" ", "").upper() for plate in cleaned]
    if len(set(normalized)) != len(normalized):
        return False, "พบเลขทะเบียนซ้ำในคำขอเดียวกัน"
    try:
        count = int(car_count)
    except (TypeError, ValueError):
        count = 0
    if count > 0 and len(cleaned) > count:
        return False, "จำนวนทะเบียนมากกว่าจำนวนรถที่ขอ"
    return True, None


def validate_guard_submission(near_photo, far_photo) -> tuple[bool, str | None]:
    if near_photo is None:
        return False, "กรุณาอัปโหลดรูปใกล้"
    if far_photo is None:
        return False, "กรุณาอัปโหลดรูปไกล"
    return True, None
