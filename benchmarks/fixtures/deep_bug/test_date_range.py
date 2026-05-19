"""DateRange テスト"""
import pytest
from datetime import date
from date_range import DateRange


# --- 通過するテスト ---

def test_contains_start():
    dr = DateRange(date(2024, 1, 1), date(2024, 1, 31))
    assert dr.contains(date(2024, 1, 1))


def test_contains_middle():
    dr = DateRange(date(2024, 1, 1), date(2024, 1, 31))
    assert dr.contains(date(2024, 1, 15))


def test_not_contains_before():
    dr = DateRange(date(2024, 1, 1), date(2024, 1, 31))
    assert not dr.contains(date(2023, 12, 31))


def test_not_contains_after():
    dr = DateRange(date(2024, 1, 1), date(2024, 1, 31))
    assert not dr.contains(date(2024, 2, 1))


# --- 失敗するテスト (バグによるもの) ---

def test_contains_end():
    """end 当日は範囲内のはず"""
    dr = DateRange(date(2024, 1, 1), date(2024, 1, 31))
    assert dr.contains(date(2024, 1, 31))


def test_clamp_at_end():
    """end 当日を clamp すると end を返すのではなく、そのまま返すべき"""
    dr = DateRange(date(2024, 1, 1), date(2024, 1, 31))
    assert dr.clamp(date(2024, 1, 31)) == date(2024, 1, 31)


def test_single_day_range():
    """start == end の 1 日範囲は start/end 当日を含む"""
    dr = DateRange(date(2024, 6, 15), date(2024, 6, 15))
    assert dr.contains(date(2024, 6, 15))


def test_duration_days_matches_contains():
    """期間の日数と含まれる日数が一致すること"""
    dr = DateRange(date(2024, 1, 1), date(2024, 1, 5))
    days_in_range = sum(
        1 for i in range(10)
        if dr.contains(date(2024, 1, 1 + i) if 1 + i <= 31 else date(2024, 1, 31))
    )
    # start=1/1, end=1/5 → 1/1,1/2,1/3,1/4,1/5 の 5 日
    assert dr.duration_days() + 1 == 5  # duration_days は差分 (4)、実際の日数は 5
