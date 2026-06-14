import re

from modules.pdf_generator import build_parking_pdf


def _page_count(pdf_bytes: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page\b", pdf_bytes))


def test_pdf_without_plates_has_one_page():
    pdf_bytes = build_parking_pdf(
        agency="สำนักบริหารงานกลาง",
        car_count=3,
        plates=[],
        parking_location="หน้าอาคาร 3",
        parking_date="2026-06-13",
        book_no="ปช 0001/1234",
    )

    assert pdf_bytes.startswith(b"%PDF")
    assert _page_count(pdf_bytes) == 1


def test_pdf_with_three_plates_stays_one_work_package_page():
    pdf_bytes = build_parking_pdf(
        agency="สำนักบริหารงานกลาง",
        car_count=3,
        plates=["TEST1", "TEST2", "TEST3"],
        parking_location="หน้าอาคาร 3",
        parking_dates=["2026-06-13", "2026-06-14"],
        parking_time="08:30-16:30",
        book_no="ปช 0001/1234",
    )

    assert _page_count(pdf_bytes) == 1
