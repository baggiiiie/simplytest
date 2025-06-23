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


class CaseRunner:
    def __init__(self, function_pool: Optional[FunctionPool] = None):
        self.function_pool = function_pool or FunctionPool()
        self.test_results = []
        self.variables = {}
        self.ctx = None
        self.current_step = {}
        # self._load_env_var()

    def _load_env_var(self):
        # self.ctx["env_var"] = os.environ
        return None

    def execute_test_case(self, test_case: TestCase) -> Dict[str, Any]:
        self.ctx = test_case
        print(f"\n--- Executing Test Case: {test_case.description} ---")
        self.variables = test_case.variables.copy() if test_case.variables else {}

        result = {
            const.STATUS: "PASSED",
            const.ERROR: None,
            const.EXECUTION_TIME: 0,
        }

        try:
            for step in test_case.steps:
                start_time = time.time()
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

        # try:
        #     # Execute setup steps
        #     if test_case.setup_steps:
        #         print("Executing setup steps...")
        #         for step in test_case.setup_steps:
        #             step.result = self._execute_step(step)
        #             if not step.result["passed"]:
        #                 result[const.STATUS] = "FAILED"
        #                 result[const.ERROR] = (
        #                     f"Setup step failed: {step.result[const.ERROR]}"
        #                 )
        #                 return result
        #
        #     # Execute main test steps
        #     for step in test_case.steps:
        #         step.result = self._execute_step(step)
        #         result["steps"].append(step.result)
        #
        #         if not step.result["passed"]:
        #             result[const.STATUS] = "FAILED"
        #             result["error"] = step.result["error"]
        #             break
        #
        #     # Execute teardown steps (always run, even if test failed)
        #     if test_case.teardown_steps:
        #         print("Executing teardown steps...")
        #         for step in test_case.teardown_steps:
        #             teardown_result = self._execute_step(step)
        #             if not teardown_result["passed"]:
        #                 print(
        #                     f"Warning: Teardown step failed: {teardown_result['error']}"
        #                 )
        #
        # except Exception as e:
        #     result[const.STATUS] = "ERROR"
        #     result["error"] = str(e)
        #
        # finally:
        #     result["execution_time"] = time.time() - start_time
        #     print("test finished")
        #     print(self.ctx)

        return result

    def execute_test_step(self, step: TestStep) -> Dict[str, Any]:
        self.current_step = step
        print(f"Executing step: {step.description}")

        func_to_call = self.function_pool.get_function(step.function)
        resolved_args = self._resolve_variables(step.input_args)
        resolved_kwargs = self._resolve_variables(step.input_kwargs)

        @allure_step(f"{step.description}: Calling function {step.function}")
        def step_func_call():
            allure.attach(
                name="Function Input",
                body=json.dumps(
                    {"args": resolved_args, "kwargs": resolved_kwargs},
                    default=str,
                    indent=2,
                ),
                attachment_type=allure.attachment_type.JSON,
            )
            actual_result = func_to_call(*resolved_args, **resolved_kwargs)
            allure.attach(
                name="Function Output",
                body=json.dumps(
                    {"result": actual_result, "type": str(type(actual_result))},
                    indent=2,
                ),
                attachment_type=allure.attachment_type.JSON,
            )
            allure_attach = {
                "actual": actual_result,
                "expected": step.expected_result,
                "assertion_type": step.assertion_type,
            }
            allure.attach(
                name="Assertion",
                body=json.dumps(allure_attach, indent=2),
                attachment_type=allure.attachment_type.JSON,
            )
            self._perform_assertion(
                actual_result, step.expected_result, step.assertion_type
            )
            return actual_result

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
            for var_name, value in self.variables.items():
                obj = obj.replace(f"${{{var_name}}}", str(value))
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
