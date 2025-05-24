from collections import Counter
from typing import Any

from app.utilities.type_checking import is_primitive_or_primitive_collection

class PrimitiveCounter(Counter):
    """A Counter which has type-checking on what types can be saved (namely, primitives and builtin containers of primitives)"""
    def __setitem__(self, key: str, val: Any):
        if not is_primitive_or_primitive_collection(val):
            raise ValueError("Cannot put object of type %s in game or level vars: %s" % (str(type(val)), str(val)))
        super().__setitem__(key, val)