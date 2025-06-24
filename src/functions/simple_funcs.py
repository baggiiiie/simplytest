# from src.utils.allure_utils import allure_func
from src.api_clients.simple_client import my_client
import time


# @allure_func
def ping():
    """
    This is simple function ping
    """
    return "pong"


# @allure_func
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


def sleep(seconds: int):
    time.sleep(seconds)


def echo(*args, **kwargs):
    return my_client.echo(*args, **kwargs)


def edgeos_health(*args, **kwargs):
    return my_client.health_check(*args, **kwargs)
