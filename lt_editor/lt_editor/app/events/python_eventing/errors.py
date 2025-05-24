from __future__ import annotations
from dataclasses import dataclass
import traceback
from typing import List, Optional

ERROR_TEMPLATE = \
"""
    Event "{event_name}", Line {lnum}:
        {line}
    {error_name}: {what}"""

STACK_ERROR_TEMPLATE = \
"""
    From event "{event_name}", Line {lnum}:
        {line}"""

@dataclass
class EventError(Exception):
    event_name: str | List[str]
    line_num: int | List[int]
    line: str | List[str]
    what = "generic event error"
    original_exception: Optional[Exception] = None

    def __str__(self) -> str:
        if isinstance(self.event_name, list):
            # all three should be list
            msg = ''
            for i in range(len(self.event_name) - 1):
                msg += STACK_ERROR_TEMPLATE.format(event_name=self.event_name[i], lnum=self.line_num[i], line=self.line[i].strip())
            msg += ERROR_TEMPLATE.format(event_name=self.event_name[-1], lnum=self.line_num[-1], line=self.line[-1].strip(),
                                         error_name=self.__class__.__name__, what=self.what)
        else:
            msg = ERROR_TEMPLATE.format(event_name=self.event_name, lnum=self.line_num, line=self.line.strip(),
                                        error_name=self.__class__.__name__, what=self.what)
        if self.original_exception:
            msg += '\n\n' + ''.join(traceback.format_exception(None, self.original_exception, self.original_exception.__traceback__))
        return msg

class NestedEventError(EventError):
    what = "all event function calls must be alone and outside function def"

class InvalidCommandError(EventError):
    what = "unknown event command"

class NoSaveInLoopError(EventError):
    what = "cannot use save event commands in for loops"

class MalformedTriggerScriptCall(EventError):
    what = 'trigger script must have non-variable valid event target'

class CannotUseYieldError(EventError):
    what = 'cannot use yield in python event scripting'

class InvalidPythonError(EventError):
    what = None
