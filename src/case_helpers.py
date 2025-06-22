from dataclasses import dataclass
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


@dataclass
class TestCase:
    description: Optional[str]
    steps: List[TestStep]
    setup_steps: Optional[List[TestStep]] = None
    teardown_steps: Optional[List[TestStep]] = None
    variables: Optional[Dict[str, Any]] = None
