import pytest
from src.case_runner import case_runner as runner


test_cases = runner.load_test_cases_from_json("tests/simpletest.json")


class TestSimpleTestOne:
    @pytest.mark.parametrize("test_case", test_cases)
    def test_my_func(self, test_case):
        runner.execute_test_case(test_case)
