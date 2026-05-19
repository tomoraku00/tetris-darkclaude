"""shapes.py 機能テスト"""
from shapes import Circle, Rectangle, total_area, find_largest, make_shape


def test_circle_area():
    c = Circle(5)
    assert abs(c.area() - 78.5) < 0.01


def test_rectangle_area():
    r = Rectangle(3, 4)
    assert r.area() == 12


def test_total_area():
    shapes = [Circle(1), Rectangle(2, 3)]
    assert abs(total_area(shapes) - (3.14 + 6)) < 0.01


def test_find_largest():
    shapes = [Circle(1), Rectangle(10, 10)]
    largest = find_largest(shapes)
    assert isinstance(largest, Rectangle)


def test_find_largest_empty():
    assert find_largest([]) is None


def test_make_shape_circle():
    c = make_shape("circle", 5)
    assert isinstance(c, Circle)


def test_make_shape_rectangle():
    r = make_shape("rectangle", 3, 4)
    assert isinstance(r, Rectangle)


def test_make_shape_unknown():
    assert make_shape("triangle", 3) is None
