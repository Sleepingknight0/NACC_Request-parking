from datetime import date, datetime

import pytest

from modules.dates import (
    expand_date_range,
    parse_multiline_dates,
    to_iso_date,
    to_month_key,
)


def test_to_iso_date_normalizes_supported_values():
    assert to_iso_date(date(2026, 6, 13)) == "2026-06-13"
    assert to_iso_date(datetime(2026, 6, 13, 8, 30)) == "2026-06-13"
    assert to_iso_date("13/06/2026") == "2026-06-13"
    assert to_iso_date("2026-06-13") == "2026-06-13"


def test_to_month_key_returns_year_month():
    assert to_month_key("2026-07-02") == "2026-07"


def test_expand_date_range_handles_cross_month_dates():
    assert expand_date_range("2026-06-30", "2026-07-02") == [
        "2026-06-30",
        "2026-07-01",
        "2026-07-02",
    ]


def test_expand_date_range_can_exclude_weekends():
    assert expand_date_range("2026-06-12", "2026-06-15", include_weekends=False) == [
        "2026-06-12",
        "2026-06-15",
    ]


def test_expand_date_range_rejects_reversed_range():
    with pytest.raises(ValueError, match="end_date"):
        expand_date_range("2026-07-02", "2026-06-30")


def test_parse_multiline_dates_returns_unique_sorted_iso_dates():
    assert parse_multiline_dates(
        """
        2026-07-02
        30/06/2026
        2026-07-01
        2026-07-01
        """
    ) == ["2026-06-30", "2026-07-01", "2026-07-02"]
