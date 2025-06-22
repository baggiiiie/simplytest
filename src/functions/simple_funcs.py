from src.utils.allure_utils import allure_func


@allure_func
def ping():
    """
    This is simple function ping
    """
    return "pong"


@allure_func
def int_add(*args):
    """
    Adding integers: {args}
    """
    sum = 0
    for arg in args:
        if not isinstance(arg, int):
            raise ValueError(f"{arg} is not integer!")
        sum += arg
    return sum
