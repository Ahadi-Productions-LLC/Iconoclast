from typing import Any
from enum import Enum, StrEnum

def is_primitive_or_primitive_collection(value: Any) -> bool:
    primitive_types = (int, float, str, bool)
    collection_types = (tuple, list, dict, set)
    enum_types = (Enum, StrEnum)
    if value is None:
        return True
    if any(isinstance(value, enum_type) for enum_type in enum_types):
        return True
    if any(isinstance(value, primitive) for primitive in primitive_types):
        return True
    if any(isinstance(value, collection) for collection in collection_types):
        if isinstance(value, dict):
            return is_primitive_or_primitive_collection(list(value.keys())) and is_primitive_or_primitive_collection(list(value.values()))
        else:
            return all(is_primitive_or_primitive_collection(v) for v in value)
    return False
