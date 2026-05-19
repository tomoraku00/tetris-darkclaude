"""calculator.add のテスト (5 ケース)"""
from calculator import add


def test_add_positive():
    assert add(2, 3) == 5


def test_add_negative():
    assert add(-1, -2) == -3


def test_add_zero():
    assert add(0, 0) == 0


def test_add_mixed():
    assert add(10, -3) == 7


def test_add_large():
    assert add(100, 200) == 300
