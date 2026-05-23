def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    if b == 0:
        raise ValueError("ZeroDivisionError")
    return a / b


def calculator():
    print("Simple Calculator")
    print("Addition:")
    print("Subtraction:")
    print("Multiplication:")
    print("Division:")
    while True:
        operator = input("Choose operator (+, -, *, /): ")
        if operator in ['+', '-', '*', '/']:
            break
