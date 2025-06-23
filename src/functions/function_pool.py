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
        self.register("add", lambda x, y: x + y)
        self.register("subtract", lambda x, y: x - y)
        self.register("multiply", lambda x, y: x * y)
        self.register("divide", lambda x, y: x / y if y != 0 else None)
        self.register("sleep", time.sleep)
        self.register("echo", my_client.echo)
        self.register("edgeos_health", my_client.health_check)
        for name, func in inspect.getmembers(funcs, inspect.isfunction):
            self.register(name, func)


function_pool = FunctionPool()
