from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from dateutil import parser


def _normalize_buddhist_year(value: date) -> date:
    if value.year > 2400:
        return value.replace(year=value.year - 543)
    return value


def _parse_date(value) -> date:
    if value is None:
        raise ValueError("date value is required")
    if isinstance(value, datetime):
        return _normalize_buddhist_year(value.date())
    if isinstance(value, date):
        return _normalize_buddhist_year(value)

    text = str(value).strip()
    if not text:
        raise ValueError("date value is required")

    if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", text):
        return _normalize_buddhist_year(datetime.strptime(text, "%Y-%m-%d").date())

    parsed = parser.parse(text, dayfirst=True, fuzzy=False).date()
    return _normalize_buddhist_year(parsed)


def to_iso_date(value) -> str:
    """Return YYYY-MM-DD."""
    return _parse_date(value).isoformat()


def to_month_key(date_value) -> str:
    """Return YYYY-MM."""
    return to_iso_date(date_value)[:7]


def expand_date_range(start_date, end_date, include_weekends=True) -> list[str]:
    """Return ISO dates in an inclusive date range."""
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if end < start:
        raise ValueError("end_date must be on or after start_date")

    values: list[str] = []
    current = start
    while current <= end:
        if include_weekends or current.weekday() < 5:
            values.append(current.isoformat())
        current += timedelta(days=1)
    return values


def parse_multiline_dates(text: str) -> list[str]:
    """Parse one date per line and return unique sorted ISO dates."""
    dates = {
        to_iso_date(line)
        for line in str(text or "").splitlines()
        if line.strip()
    }
    return sorted(dates)
