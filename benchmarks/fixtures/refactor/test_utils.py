"""parse_date のテスト"""
import pytest
from utils import parse_date
from datetime import date


def test_iso_format():
    assert parse_date("2024-01-15") == date(2024, 1, 15)


def test_us_format():
    assert parse_date("01/15/2024") == date(2024, 1, 15)


def test_eu_format():
    assert parse_date("15.01.2024") == date(2024, 1, 15)


def test_with_whitespace():
    assert parse_date("  2024-01-15  ") == date(2024, 1, 15)


def test_invalid_format():
    with pytest.raises(ValueError):
        parse_date("not-a-date")
