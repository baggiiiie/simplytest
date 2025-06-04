"""
Function pool containing all available functions for test execution
"""

import time
from typing import List, Callable


class FunctionPool:
    """Central registry for all functions available to test steps"""

    def __init__(self):
        self._functions = {}
        self._register_default_functions()

    def register(self, name: str, func: Callable):
        """Register a function with a given name"""
        self._functions[name] = func

    def get_function(self, name: str) -> Callable:
        """Get a function by name"""
        if name not in self._functions:
            raise ValueError(f"Function '{name}' not found in function pool")
        return self._functions[name]

    def list_functions(self) -> List[str]:
        """List all available function names"""
        return list(self._functions.keys())

    def _register_default_functions(self):
        """Register default utility functions"""
        self.register("add", lambda x, y: x + y)
        self.register("subtract", lambda x, y: x - y)
        self.register("multiply", lambda x, y: x * y)
        self.register("divide", lambda x, y: x / y if y != 0 else None)
        self.register("sleep", time.sleep)
