import allure
from functools import wraps
import logging
import json


def allure_step(func):
    """
    Decorator that wraps a function in an Allure step using its docstring
    as the step description. Supports formatting with args/kwargs.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Build a formatting context
        arg_names = func.__code__.co_varnames[: func.__code__.co_argcount]
        named_args = dict(zip(arg_names, args))
        context = {**named_args, "args": args, "kwargs": kwargs}

        doc = func.__doc__ or "No description"
        try:
            description = doc.format(**context)
            logging.info(f"STEP: {description}")
            print(f"STEP: {description}")
            with allure.step(description):
                allure.attach(
                    body=json.dumps(context),
                    name="func_input",
                    attachment_type="application/json",
                )
                res = func(*args, **kwargs)
                allure.attach(
                    body=json.dumps(res),
                    name="func_input",
                    attachment_type="application/json",
                )
                return res

        except Exception as e:
            raise ValueError(
                f"Error formatting docstring: {e}\nDocstring: {doc}\nContext: {context}"
            ) from e

    return wrapper
