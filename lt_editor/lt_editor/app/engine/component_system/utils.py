from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List
from functools import reduce
import operator

ARG_TYPE_MAP: Dict[str, str] = {
    'unit': "UnitObject",
    'item': "ItemObject",
    'target': "UnitObject",
    'item2': "ItemObject"
}

class ResolvePolicy(Enum):
    LIST = 'list'
    UNIQUE = 'unique'
    UNION = 'union'

    ALL_DEFAULT_FALSE = 'all_false_priority'
    ALL_DEFAULT_TRUE = 'all_true_priority'
    ANY_DEFAULT_FALSE = 'any_false_priority'

    NUMERIC_ACCUM = 'numeric_accumulate'
    NUMERIC_MULTIPLY = 'numeric_multiply'
    MAXIMUM = 'maximum'
    MINIMUM = 'minimum'

    NO_RETURN = 'no_return'

@dataclass
class HookInfo():
    args: List[str] = field(default_factory=list)
    policy: ResolvePolicy = ResolvePolicy.UNIQUE
    has_default_value: bool = False
    has_unconditional: bool = False
    inherits_parent: bool = False
    is_cached: bool = False


"""
Resolution policies go here
"""

def unique(vals: List[Any]):
    if not vals:
        return None
    return vals[-1]

def all_false_priority(vals: List[bool]) -> bool:
    if not vals:
        return False
    return all(vals)

def all_true_priority(vals: List[bool]) -> bool:
    if not vals:
        return True
    return all(vals)

def any_false_priority(vals: List[bool]) -> bool:
    if not vals:
        return False
    return any(vals)

def list(vals: List[Any]):
    return vals or []

def union(vals: List[Any]):
    return set(filter(lambda val: val is not None, vals))

def numeric_accumulate(vals: List[int | float]):
    return sum(vals)

def numeric_multiply(vals: List[int | float]):
    return reduce(operator.mul, vals, 1)

def no_return(_):
    return None

def maximum(vals: List[int | float]):
    return max(vals, default=0)

def minimum(vals: List[int | float]):
    return min(vals, default=0)