from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class TestStep:
    """Represents a single test step"""

    name: str
    function: str
    input_args: List[Any]
    input_kwargs: Dict[str, Any]
    expected_result: Any
    assertion_type: str = (
        "equals"  # equals, not_equals, contains, not_contains, greater, less
    )
    retry_count: int = 0
    retry_delay: float = 1.0
    description: Optional[str] = None


@dataclass
class TestCase:
    """Represents a complete test case with multiple steps"""

    name: str
    description: Optional[str]
    steps: List[TestStep]
    setup_steps: Optional[List[TestStep]] = None
    teardown_steps: Optional[List[TestStep]] = None
    variables: Optional[Dict[str, Any]] = None
