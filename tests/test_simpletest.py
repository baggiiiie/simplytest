import pytest
import allure
from src.case_runner import case_runner as runner
from src.utils.case_utils import load_test_cases


test_suites = load_test_cases("tests/simpletest.json")


@allure.feature(test_suites.description)
class TestSimpleTestOne:
    @pytest.mark.parametrize("test_case", test_suites.test_cases)
    def test_my_func(self, test_case):
        # print("runing test case:", test_case.description)
        runner.execute_test_case(test_case)
