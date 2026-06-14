from __future__ import annotations

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


FONT_NAME = "Helvetica"


def _register_font() -> str:
    candidates = [
        Path("assets/fonts/NotoSansThai-Regular.ttf"),
        Path("assets/fonts/Sarabun-Regular.ttf"),
        Path("assets/fonts/THSarabunNew.ttf"),
    ]
    for path in candidates:
        if path.exists():
            pdfmetrics.registerFont(TTFont("NACCThai", str(path)))
            return "NACCThai"
    return FONT_NAME


def _fit_font_size(text: str, font_name: str, max_width: float, start: int, minimum: int) -> int:
    size = start
    while size > minimum and pdfmetrics.stringWidth(text, font_name, size) > max_width:
        size -= 2
    return size


def _draw_page(
    pdf: canvas.Canvas,
    main_text: str,
    agency: str,
    parking_location: str,
    date_summary: str | None,
    parking_time: str | None,
    book_no: str | None,
    plates: list[str],
    font_name: str,
) -> None:
    width, height = landscape(A4)
    margin = 42
    pdf.setFillColor(colors.black)

    pdf.setFont(font_name, 18)
    pdf.drawCentredString(width / 2, height - 42, "ป้ายจอดรถ")

    agency_size = _fit_font_size(agency, font_name, width - margin * 2, 24, 13)
    pdf.setFont(font_name, agency_size)
    pdf.drawCentredString(width / 2, height - 76, agency)

    main_size = _fit_font_size(main_text, font_name, width - margin * 2, 88, 36)
    pdf.setFont(font_name, main_size)
    pdf.drawCentredString(width / 2, height / 2 + 58, main_text)

    y = height / 2 - 30
    if plates:
        pdf.setFont(font_name, 20)
        pdf.drawCentredString(width / 2, y + 42, "ทะเบียนรถ")
        cols = 3 if len(plates) > 4 else 2
        col_width = (width - margin * 2) / cols
        row_height = 34
        pdf.setFont(font_name, 22 if len(plates) <= 8 else 18)
        for index, plate in enumerate(plates[:24]):
            col = index % cols
            row = index // cols
            x = margin + col_width * col + col_width / 2
            pdf.drawCentredString(x, y - row * row_height, str(plate))

    footer_parts = [part for part in [parking_location, date_summary, parking_time, book_no] if part]
    if footer_parts:
        footer = " | ".join(footer_parts)
        pdf.setFont(font_name, _fit_font_size(footer, font_name, width - margin * 2, 18, 10))
        pdf.setFillColor(colors.HexColor("#333333"))
        pdf.drawCentredString(width / 2, 52, footer)

    pdf.showPage()


def build_parking_pdf(
    agency: str,
    car_count: int,
    plates: list[str],
    parking_location: str,
    parking_date: str | None = None,
    parking_dates: list[str] | None = None,
    date_summary: str | None = None,
    parking_time: str | None = None,
    book_no: str | None = None,
) -> bytes:
    """Return printable parking sign PDF bytes."""
    buffer = BytesIO()
    font_name = _register_font()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    active_plates = [str(plate).strip() for plate in plates if str(plate).strip()]
    effective_date_summary = date_summary or (
        ", ".join([str(value) for value in parking_dates or [] if str(value).strip()])
        or parking_date
        or ""
    )

    main_text = f"จำนวน {int(car_count)} คัน"

    if not active_plates:
        _draw_page(
            pdf=pdf,
            main_text=main_text,
            agency=agency,
            parking_location=parking_location,
            date_summary=effective_date_summary,
            parking_time=parking_time,
            book_no=book_no,
            plates=[],
            font_name=font_name,
        )
    else:
        for start in range(0, len(active_plates), 24):
            page_plates = active_plates[start : start + 24]
            _draw_page(
                pdf=pdf,
                main_text=main_text,
                agency=agency,
                parking_location=parking_location,
                date_summary=effective_date_summary,
                parking_time=parking_time,
                book_no=book_no,
                plates=page_plates,
                font_name=font_name,
            )

    pdf.save()
    return buffer.getvalue()
