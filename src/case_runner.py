import json
import time
import os
from typing import Dict, List, Any, Optional
from src.functions.function_pool import FunctionPool
import src.utils.constants as const
from src.utils.case_utils import TestCase, TestStep
from retry.api import retry_call
import importlib
from hamcrest import assert_that
from src.utils.allure_utils import allure_step, allure_func
from src.utils.logger import logger
import allure
from dataclasses import asdict
import jmespath


class CaseRunner:
    def __init__(self, function_pool: Optional[FunctionPool] = None):
        self.function_pool = function_pool or FunctionPool()
        self.test_results = []
        self.current_step = {}
        # self._load_env_var()

    def _load_env_var(self):
        # self.ctx.variables = os.environ
        return None

    def execute_test_case(self, test_case: TestCase) -> Dict[str, Any]:
        self.ctx = test_case
        self.ctx.variables = test_case.variables or {}
        print(f"\n--- Executing Test Case: {test_case.description} ---")

        result = {
            const.STATUS: "PASSED",
            const.ERROR: None,
            const.EXECUTION_TIME: 0,
        }

        try:
            for i, step in enumerate(test_case.steps):
                start_time = time.time()
                step.description = f"Step {i + 1}: {step.description}"
                func_return = self.execute_test_step(step)
                end_time = time.time()
                step.result = {
                    "func_return": func_return,
                    "exec_duration": f"{end_time - start_time:.2f} seconds",
                }
        except Exception as e:
            raise e
        finally:
            # teardown
            print("Executing teardown steps...")
            print("test done")
            allure.attach(
                body=json.dumps(asdict(self.ctx), indent=2),
                attachment_type=allure.attachment_type.JSON,
                name="context",
            )
        return result

    def execute_test_step(self, step: TestStep) -> Dict[str, Any]:
        self.current_step = step
        print(f"Executing step: {step.description}")

        func_to_call = self.function_pool.get_function(step.function)
        step.input_args = self._resolve_variables(step.input_args)
        step.input_kwargs = self._resolve_variables(step.input_kwargs)

        @allure_step(f"{step.description} - Calling function `{step.function}`")
        def step_func_call():
            allure.attach(
                name="Function Input",
                body=json.dumps(
                    {"args": step.input_args, "kwargs": step.input_kwargs},
                    default=str,
                    indent=2,
                ),
                attachment_type=allure.attachment_type.JSON,
            )
            func_res = func_to_call(*step.input_args, **step.input_kwargs)
            if step.save_result_to:
                self.ctx.variables[step.save_result_to] = func_res

            allure.attach(
                name="Function Output",
                body=json.dumps(
                    {"result": func_res, "type": str(type(func_res))},
                    indent=2,
                ),
                attachment_type=allure.attachment_type.JSON,
            )
            allure_attach = {
                "actual": func_res,
                "expected": step.expected_result,
                "assertion_type": step.assertion_type,
            }
            allure.attach(
                name="Assertion",
                body=json.dumps(allure_attach, indent=2),
                attachment_type=allure.attachment_type.JSON,
            )
            if step.expected_key:
                actual = jmespath.search(step.expected_key, func_res)
            else:
                actual = func_res
            self._perform_assertion(actual, step.expected_result, step.assertion_type)
            return func_res

        actual_result = retry_call(
            step_func_call,
            tries=step.retry_count,
            delay=step.retry_delay,
            backoff=1,
            max_delay=None,
            exceptions=(AssertionError,),
            logger=logger,
        )
        print("Step passed")
        return actual_result

    def _resolve_variables(self, obj: Any) -> Any:
        """Resolve variables in the format ${variable_name} within the object"""
        if isinstance(obj, str):
            # Simple variable substitution
            if obj.startswith("${") and obj.endswith("}"):
                var_name = obj[2:-1]
                var_value = self.ctx.variables.get(var_name, None)
                if not var_value:
                    raise ValueError(f"Variable {obj} not found in context")
                # TODO: this replacement is not enough
                obj = var_value
            return obj
        elif isinstance(obj, list):
            return [self._resolve_variables(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._resolve_variables(value) for key, value in obj.items()}
        else:
            return obj

    def _perform_assertion(self, actual: Any, expected: Any, assertion_type: str):
        def _get_matcher(matcher_name: str):
            matcher_modules = [
                "hamcrest.core.core",
                "hamcrest.library.collection",
                "hamcrest.library.number",
                "hamcrest.library.object",
                "hamcrest.library.text",
                "hamcrest.library.string",
            ]
            for module_name in matcher_modules:
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, matcher_name):
                        return getattr(module, matcher_name)
                except ImportError:
                    continue
            raise ValueError(f'"{assertion_type}" is not a valid matcher')

        matcher = _get_matcher(assertion_type.lower())
        assert_that(
            actual,
            matcher(expected),
            f"Assertion failed: {actual} does not match {expected}",
        )


case_runner = CaseRunner()
