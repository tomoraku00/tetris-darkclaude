"""図形ライブラリ (mypy --strict で 30+ エラー)"""
from abc import abstractmethod


class Shape:
    name = None  # 型注釈なし

    @abstractmethod
    def area(self):  # 戻り値型なし
        pass

    def describe(self):  # 戻り値型なし
        return f"Shape: {self.name}"


class Circle(Shape):
    def __init__(self, radius):  # 引数型なし
        self.radius = radius
        self.name = "circle"

    def area(self):
        return 3.14 * self.radius ** 2


class Rectangle(Shape):
    def __init__(self, width, height):  # 引数型なし
        self.width = width
        self.height = height
        self.name = "rectangle"

    def area(self):
        return self.width * self.height


def total_area(shapes):  # list[Shape] 型注釈なし、戻り値型なし
    return sum(s.area() for s in shapes)


def find_largest(shapes):  # 戻り値が Shape | None なのに注釈なし
    if not shapes:
        return None
    largest = shapes[0]
    for s in shapes[1:]:
        if s.area() > largest.area():
            largest = s
    return largest


def make_shape(shape_type, *args):  # Union 型必要、注釈なし
    if shape_type == "circle":
        return Circle(*args)
    elif shape_type == "rectangle":
        return Rectangle(*args)
    else:
        return None
