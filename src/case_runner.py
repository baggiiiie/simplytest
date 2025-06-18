"""
Test runner for executing JSON-defined test cases
"""

import json
import time
import os
import allure
from typing import Dict, List, Any, Optional
from src.functions.function_pool import FunctionPool
from src.case_helpers import TestCase, TestStep
import src.constants as const


class CaseRunner:
    """Main test runner for executing JSON-defined test cases"""

    def __init__(self, function_pool: Optional[FunctionPool] = None):
        self.function_pool = function_pool or FunctionPool()
        self.test_results = []
        self.variables = {}
        self.ctx = {}
        self._load_env_var()

    def _load_env_var(self):
        self.ctx["env_var"] = os.environ

    def load_test_cases_from_json(self, json_path: str) -> List[TestCase]:
        """Load test cases from JSON file"""
        with open(json_path, "r") as f:
            data = json.load(f)

        test_cases = []
        for case_data in data.get("test_cases", []):
            test_case = self._parse_test_case(case_data)
            test_cases.append(test_case)

        return test_cases

    def _parse_test_case(self, case_data: Dict) -> TestCase:
        """Parse a single test case from JSON data"""
        steps = []
        for step_data in case_data.get(const.STEPS, []):
            step = TestStep(
                name=step_data[const.NAME],
                function=step_data[const.FUNCTION],
                input_args=step_data.get(const.INPUT_ARGS, []),
                input_kwargs=step_data.get(const.INPUT_KWARGS, {}),
                expected_result=step_data.get(const.EXPECTED),
                assertion_type=step_data.get(const.ASSERTION, "equals"),
                retry_count=step_data.get(const.RETRY_COUNT, 0),
                retry_delay=step_data.get(const.RETRY_DELAY, 1.0),
                description=step_data.get(const.DESCRIPTION),
            )
            steps.append(step)

        # Parse setup and teardown steps if they exist
        setup_steps = None
        if "setup_steps" in case_data:
            setup_steps = [self._parse_step(step) for step in case_data["setup_steps"]]

        teardown_steps = None
        if "teardown_steps" in case_data:
            teardown_steps = [
                self._parse_step(step) for step in case_data["teardown_steps"]
            ]

        return TestCase(
            name=case_data["name"],
            description=case_data.get("description"),
            steps=steps,
            setup_steps=setup_steps,
            teardown_steps=teardown_steps,
            variables=case_data.get("variables", {}),
        )

    def _parse_step(self, step_data: Dict) -> TestStep:
        """Parse a single test step from JSON data"""
        return TestStep(
            name=step_data[const.NAME],
            function=step_data[const.FUNCTION],
            input_args=step_data.get(const.INPUT_ARGS, []),
            input_kwargs=step_data.get(const.INPUT_KWARGS, {}),
            expected_result=step_data.get(const.EXPECTED),
            assertion_type=step_data.get(const.ASSERTION, "equals"),
            retry_count=step_data.get(const.RETRY_COUNT, 0),
            retry_delay=step_data.get(const.RETRY_DELAY, 1.0),
            description=step_data.get(const.DESCRIPTION, ""),
        )

    def execute_test_case(self, test_case: TestCase) -> Dict[str, Any]:
        """Execute a single test case"""
        print(f"\n--- Executing Test Case: {test_case.name} ---")
        if test_case.description:
            print(f"Description: {test_case.description}")

        # Initialize variables for this test case
        self.variables = test_case.variables.copy() if test_case.variables else {}

        result = {
            const.NAME: test_case.name,
            const.STATUS: "PASSED",
            const.STEPS: [],
            const.ERROR: None,
            const.EXECUTION_TIME: 0,
        }

        start_time = time.time()

        try:
            # Execute setup steps
            if test_case.setup_steps:
                print("Executing setup steps...")
                for step in test_case.setup_steps:
                    with allure.step(step.description):
                        step_result = self._execute_step(step)
                        if not step_result["passed"]:
                            result[const.STATUS] = "FAILED"
                            result[const.ERROR] = (
                                f"Setup step failed: {step_result[const.ERROR]}"
                            )
                            return result

            # Execute main test steps
            for step in test_case.steps:
                step_result = self._execute_step(step)
                result["steps"].append(step_result)

                if not step_result["passed"]:
                    result[const.STATUS] = "FAILED"
                    result["error"] = step_result["error"]
                    break

            # Execute teardown steps (always run, even if test failed)
            if test_case.teardown_steps:
                print("Executing teardown steps...")
                for step in test_case.teardown_steps:
                    teardown_result = self._execute_step(step)
                    if not teardown_result["passed"]:
                        print(
                            f"Warning: Teardown step failed: {teardown_result['error']}"
                        )

        except Exception as e:
            result[const.STATUS] = "ERROR"
            result["error"] = str(e)

        finally:
            result["execution_time"] = time.time() - start_time

        return result

    def _execute_step(self, step: TestStep) -> Dict[str, Any]:
        """Execute a single test step with retry logic"""
        print(f"  Executing step: {step.name}")
        if step.description:
            print(f"    Description: {step.description}")

        for attempt in range(step.retry_count + 1):
            try:
                if attempt > 0:
                    print(f"    Retry attempt {attempt}/{step.retry_count}")
                    time.sleep(step.retry_delay)

                # Get the function to execute
                func = self.function_pool.get_function(step.function)

                # Resolve variables in input arguments
                resolved_args = self._resolve_variables(step.input_args)
                resolved_kwargs = self._resolve_variables(step.input_kwargs)

                # Execute the function
                actual_result = func(*resolved_args, **resolved_kwargs)

                # Store result in variables if step name starts with 'var_'
                if step.name.startswith("var_"):
                    var_name = step.name[4:]  # Remove 'var_' prefix
                    self.variables[var_name] = actual_result

                # Perform assertion
                assertion_passed = self._perform_assertion(
                    actual_result, step.expected_result, step.assertion_type
                )

                if assertion_passed:
                    print("Step passed")
                    return {
                        "name": step.name,
                        "passed": True,
                        "actual_result": actual_result,
                        "expected_result": step.expected_result,
                        "attempt": attempt + 1,
                        "error": None,
                    }
                else:
                    error_msg = f"Assertion failed: expected {step.expected_result}, got {actual_result}"
                    if attempt < step.retry_count:
                        print(f"    ✗ {error_msg} (will retry)")
                        continue
                    else:
                        print(f"    ✗ {error_msg}")
                        return {
                            "name": step.name,
                            "passed": False,
                            "actual_result": actual_result,
                            "expected_result": step.expected_result,
                            "attempt": attempt + 1,
                            "error": error_msg,
                        }

            except Exception as e:
                error_msg = f"Function execution failed: {str(e)}"
                if attempt < step.retry_count:
                    print(f"{error_msg} (will retry)")
                    continue
                else:
                    print(f"{error_msg}")
                    return {
                        "name": step.name,
                        "passed": False,
                        "actual_result": None,
                        "expected_result": step.expected_result,
                        "attempt": attempt + 1,
                        "error": error_msg,
                    }

        # This should never be reached, but just in case
        return {
            "name": step.name,
            "passed": False,
            "actual_result": None,
            "expected_result": step.expected_result,
            "attempt": step.retry_count + 1,
            "error": "Unknown error",
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

    def _perform_assertion(
        self, actual: Any, expected: Any, assertion_type: str
    ) -> bool:
        """Perform assertion based on type"""
        if assertion_type == "equals":
            return actual == expected
        elif assertion_type == "not_equals":
            return actual != expected
        elif assertion_type == "contains":
            return expected in actual
        elif assertion_type == "not_contains":
            return expected not in actual
        elif assertion_type == "greater":
            return actual > expected
        elif assertion_type == "less":
            return actual < expected
        elif assertion_type == "greater_equal":
            return actual >= expected
        elif assertion_type == "less_equal":
            return actual <= expected
        elif assertion_type == "is_none":
            return actual is None
        elif assertion_type == "is_not_none":
            return actual is not None
        else:
            raise ValueError(f"Unknown assertion type: {assertion_type}")


case_runner = CaseRunner()
