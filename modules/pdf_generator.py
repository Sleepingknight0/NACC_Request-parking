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
    parking_date: str | None,
    book_no: str | None,
    font_name: str,
) -> None:
    width, height = landscape(A4)
    margin = 42
    pdf.setFillColor(colors.black)

    agency_size = _fit_font_size(agency, font_name, width - margin * 2, 26, 14)
    pdf.setFont(font_name, agency_size)
    pdf.drawCentredString(width / 2, height - 78, agency)

    main_size = _fit_font_size(main_text, font_name, width - margin * 2, 112, 42)
    pdf.setFont(font_name, main_size)
    pdf.drawCentredString(width / 2, height / 2 - main_size / 3, main_text)

    footer_parts = [part for part in [parking_location, parking_date, book_no] if part]
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
    book_no: str | None = None,
) -> bytes:
    """Return printable parking sign PDF bytes."""
    buffer = BytesIO()
    font_name = _register_font()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    active_plates = [str(plate).strip() for plate in plates if str(plate).strip()]

    if active_plates:
        page_texts = active_plates
    else:
        page_texts = [f"จำนวน {int(car_count)} คัน"]

    for page_text in page_texts:
        _draw_page(
            pdf=pdf,
            main_text=page_text,
            agency=agency,
            parking_location=parking_location,
            parking_date=parking_date,
            book_no=book_no,
            font_name=font_name,
        )

    pdf.save()
    return buffer.getvalue()
