import allure
from functools import wraps


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
        except Exception as e:
            raise ValueError(
                f"Error formatting docstring: {e}\nDocstring: {doc}\nContext: {context}"
            ) from e

        print(f"STEP: {description}")
        with allure.step(description):
            return func(*args, **kwargs)

    return wrapper
