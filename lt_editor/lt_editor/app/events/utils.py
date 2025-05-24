from typing import Any, Callable, List


# Type hint for table row args. Could be:
# - A function that returns a list of strings (lambda: ["Row1", "Row2", "Row3"])
# - A string ("Row1, Row2, Row3")
# - A list of strings (["Row1", "Row2", "Row3"])
# - A string that contains a evaluable function ("lambda: ['Row1', 'Row2', 'Row3']")
TableRows = Callable[[], List[str]] | str | List[Any]