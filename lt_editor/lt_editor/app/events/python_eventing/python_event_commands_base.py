from typing import Any, Callable, List, Tuple
from .. import event_commands, event_validators

def optional_value_filter(required_keywords: List[str]) -> Callable[[Tuple[str, Any]], bool]:
    # pair is a (key, value) pair
    return lambda pair: (pair[0] in required_keywords) or (pair[1] is not None)