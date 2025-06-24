import time
from typing import List, Callable
import src.functions.simple_funcs as funcs
import inspect
from src.api_clients.simple_client import my_client


class FunctionPool:
    """Central registry for all functions available to test steps"""

    def __init__(self):
        self._functions = {}
        self._register_default_functions()

    def register(self, name: str, func: Callable):
        self._functions[name] = func

    def get_function(self, name: str) -> Callable:
        if name not in self._functions:
            raise ValueError(f"Function '{name}' not found in function pool")
        return self._functions[name]

    def list_functions(self) -> List[str]:
        return list(self._functions.keys())

    def _register_default_functions(self):
        for name, func in inspect.getmembers(funcs, inspect.isfunction):
            self.register(name, func)


function_pool = FunctionPool()
