import allure
from functools import wraps
import logging
import json


def allure_step(message):
    def wrapper(func):
        @allure.step(message)
        @wraps(func)
        def _wrapper(*args, **kwargs):
            print(f"Executing step: {message}")
            return func(*args, **kwargs)

        return _wrapper

    return wrapper


def allure_func(func, message):
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
            func_description = doc.format(**context)
            with allure.step(f"{message}: {func_description}"):
                logging.info(f"STEP: {func_description}")
                print(f"STEP: {func_description}")
                allure.attach(
                    body=json.dumps(context, indent=2),
                    name="func_input",
                    attachment_type="application/json",
                )
                res = func(*args, **kwargs)
                allure.attach(
                    body=json.dumps(res, indent=2),
                    name="func_input",
                    attachment_type="application/json",
                )
                return res

        except Exception as e:
            raise ValueError(
                f"Error formatting docstring: {e}\nDocstring: {doc}\nContext: {context}"
            ) from e

    return wrapper
