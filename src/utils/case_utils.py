from dataclasses import dataclass
import src.utils.constants as const
import json

from typing import Dict, List, Any, Optional


@dataclass
class TestStep:
    function: str
    input_args: List[Any]
    input_kwargs: Dict[str, Any]
    expected_result: Any = None
    assertion_type: str = "equal_to"
    retry_count: int = 3
    retry_delay: float = 1.0
    description: str = "No step description provided"
    result: Optional[Dict] = None


@dataclass
class TestCase:
    description: Optional[str]
    tag: Optional[str]
    steps: List[TestStep]
    setup_steps: Optional[List[TestStep]] = None
    teardown_steps: Optional[List[TestStep]] = None
    variables: Optional[Dict[str, Any]] = None


@dataclass
class TestSuites:
    description: Optional[str]
    tag: Optional[List[str]]
    test_cases: List[TestCase]


def _parse_step(step_data: Dict) -> TestStep:
    return TestStep(
        function=step_data[const.FUNCTION],
        input_args=step_data.get(const.INPUT_ARGS, []),
        input_kwargs=step_data.get(const.INPUT_KWARGS, {}),
        expected_result=step_data.get(const.EXPECTED_RESULT),
        assertion_type=step_data.get(const.ASSERTION_TYPE, "equal_to"),
        retry_count=step_data.get(const.RETRY_COUNT, 3),
        retry_delay=step_data.get(const.RETRY_DELAY, 1),
        description=step_data.get(const.DESCRIPTION, "No step description provided"),
    )


def _parse_test_case(test_case: Dict) -> TestCase:
    steps = test_case.get(const.STEPS, [])
    if not steps:
        raise ValueError("no test steps found")
    parsed_steps = [_parse_step(step) for step in steps]

    parsed_setup = [_parse_step(step) for step in test_case.get(const.SETUP_STEPS, [])]

    parsed_teardown = [
        _parse_step(step) for step in test_case.get(const.TEARDOWN_STEPS, [])
    ]

    return TestCase(
        description=test_case.get(const.DESCRIPTION),
        tag=test_case.get("tag", ""),
        steps=parsed_steps,
        setup_steps=parsed_setup,
        teardown_steps=parsed_teardown,
        variables=test_case.get(const.VARIABLES, {}),
    )


def load_test_cases(json_path: str) -> TestSuites:
    with open(json_path, "r") as f:
        json_data = json.load(f)

    test_cases = json_data.get(const.TEST_CASES, [])
    if not test_cases:
        raise ValueError(f"no test cases found in {json_path}")
    parsed_cases = [_parse_test_case(case) for case in test_cases]
    parsed_suites = TestSuites(
        description=json_data.get("description", "No description"),
        tag=json_data.get("tag", []),
        test_cases=parsed_cases,
    )
    return parsed_suites
