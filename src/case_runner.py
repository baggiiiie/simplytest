import json
import time
import os
from typing import Dict, List, Any, Optional
from src.functions.function_pool import FunctionPool
from src.case_helpers import TestCase, TestStep
import src.constants as const
from retry.api import retry_call
import importlib
from hamcrest import assert_that
from src.utils.allure_utils import allure_step, allure_func
from src.utils.logger import logger
import allure


class CaseRunner:
    def __init__(self, function_pool: Optional[FunctionPool] = None):
        self.function_pool = function_pool or FunctionPool()
        self.test_results = []
        self.variables = {}
        self.ctx = {}
        self._load_env_var()

    def _load_env_var(self):
        # self.ctx["env_var"] = os.environ
        return None

    def load_test_cases_from_json(self, json_path: str) -> List[TestCase]:
        with open(json_path, "r") as f:
            json_data = json.load(f)

        test_cases = json_data.get(const.TEST_CASES, [])
        if not test_cases:
            raise ValueError(f"no test cases found in {json_path}")
        parsed_tests = [self._parse_test_case(case_data) for case_data in test_cases]
        return parsed_tests

    def _parse_test_case(self, test_case: Dict) -> TestCase:
        steps = test_case.get(const.STEPS, [])
        if not steps:
            raise ValueError("no test steps found")
        parsed_steps = [self._parse_step(step) for step in steps]

        parsed_setup = [
            self._parse_step(step) for step in test_case.get(const.SETUP_STEPS, [])
        ]

        parsed_teardown = [
            self._parse_step(step) for step in test_case.get(const.TEARDOWN_STEPS, [])
        ]

        return TestCase(
            description=test_case.get(const.DESCRIPTION),
            steps=parsed_steps,
            setup_steps=parsed_setup,
            teardown_steps=parsed_teardown,
            variables=test_case.get(const.VARIABLES, {}),
        )

    def _parse_step(self, step_data: Dict) -> TestStep:
        return TestStep(
            function=step_data[const.FUNCTION],
            input_args=step_data.get(const.INPUT_ARGS, []),
            input_kwargs=step_data.get(const.INPUT_KWARGS, {}),
            expected_result=step_data.get(const.EXPECTED_RESULT),
            assertion_type=step_data.get(const.ASSERTION_TYPE, "equal_to"),
            retry_count=step_data.get(const.RETRY_COUNT, 3),
            retry_delay=step_data.get(const.RETRY_DELAY, 1),
            description=step_data.get(
                const.DESCRIPTION, "No step description provided"
            ),
        )

    def execute_test_case(self, test_case: TestCase) -> Dict[str, Any]:
        print(f"\n--- Executing Test Case: {test_case.description} ---")
        self.variables = test_case.variables.copy() if test_case.variables else {}

        result = {
            const.NAME: test_case.description,
            const.STATUS: "PASSED",
            const.STEPS: [],
            const.ERROR: None,
            const.EXECUTION_TIME: 0,
        }

        start_time = time.time()

        try:
            for step in test_case.steps:
                step_result = self.execute_step(step)
                result["steps"].append(step_result)

                if not step_result["passed"]:
                    result[const.STATUS] = "FAILED"
                    result["error"] = step_result["error"]
                    break
        except Exception as e:
            raise e
        finally:
            # teardown
            print("Executing teardown steps...")
            print("test done")
            allure.attach(
                body=json.dumps(self.ctx, indent=2),
                attachment_type=allure.attachment_type.JSON,
                name="context",
            )

        # try:
        #     # Execute setup steps
        #     if test_case.setup_steps:
        #         print("Executing setup steps...")
        #         for step in test_case.setup_steps:
        #             step_result = self._execute_step(step)
        #             if not step_result["passed"]:
        #                 result[const.STATUS] = "FAILED"
        #                 result[const.ERROR] = (
        #                     f"Setup step failed: {step_result[const.ERROR]}"
        #                 )
        #                 return result
        #
        #     # Execute main test steps
        #     for step in test_case.steps:
        #         step_result = self._execute_step(step)
        #         result["steps"].append(step_result)
        #
        #         if not step_result["passed"]:
        #             result[const.STATUS] = "FAILED"
        #             result["error"] = step_result["error"]
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

    def execute_step(self, step: TestStep) -> Dict[str, Any]:
        print(f"Executing step: {step.description}")

        func_to_call = self.function_pool.get_function(step.function)
        resolved_args = self._resolve_variables(step.input_args)
        resolved_kwargs = self._resolve_variables(step.input_kwargs)

        @allure_step(step.description)
        def step_func_call():
            print(f"Calling function: {step.function}")
            actual_result = func_to_call(*resolved_args, **resolved_kwargs)
            # if step.name.startswith("var_"):
            #     var_name = step.name[4:]  # Remove 'var_' prefix
            #     self.variables[var_name] = actual_result
            allure_attach = {
                "actual": actual_result,
                "expected": step.expected_result,
                "assertion_type": step.assertion_type,
            }
            allure.attach(
                name="assertion_result",
                body=json.dumps(allure_attach, indent=2),
                attachment_type=allure.attachment_type.JSON,
            )
            self._perform_assertion(
                actual_result, step.expected_result, step.assertion_type
            )
            return actual_result

        actual_result = retry_call(
            step_func_call,
            tries=step.retry_count + 1,
            delay=step.retry_delay,
            backoff=1,
            max_delay=None,
            exceptions=(AssertionError,),
            logger=logger,
        )
        print("Step passed")
        return {
            "name": step.description,
            "passed": True,
            "actual_result": actual_result,
            "expected_result": step.expected_result,
            "attempt": step.retry_count + 1,
            "error": None,
        }

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
