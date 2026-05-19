"""finder.py 正確性テスト"""
import pytest
from finder import find_duplicates, find_common_elements, count_unique


def test_find_duplicates_basic():
    assert find_duplicates([1, 2, 3, 2, 4, 3]) == [2, 3]


def test_find_duplicates_no_dup():
    assert find_duplicates([1, 2, 3]) == []


def test_find_duplicates_all_same():
    assert find_duplicates([5, 5, 5]) == [5]


def test_find_common_basic():
    assert find_common_elements([1, 2, 3], [2, 3, 4]) == [2, 3]


def test_find_common_no_overlap():
    assert find_common_elements([1, 2], [3, 4]) == []


def test_count_unique():
    assert count_unique([1, 1, 2, 3, 3]) == 3


def test_count_unique_empty():
    assert count_unique([]) == 0
