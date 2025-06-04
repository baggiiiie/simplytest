def ping():
    return "pong"


def int_add(*args):
    sum = 0
    for arg in args:
        if not isinstance(arg, int):
            raise ValueError(f"{arg} is not integer!")
        sum += arg
    return sum
