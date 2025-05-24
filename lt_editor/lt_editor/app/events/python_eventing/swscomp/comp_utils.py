
from dataclasses import dataclass
from typing import List

from app.events.event_structs import EventCommandTokens

@dataclass
class ScriptWithSentinel():
    """
    A python event script, with all event commands
    replaced with the COMMAND_SENTINEL,
    and extracted into EventCommandTokens
    for use in second-pass compilation
    """
    source: str
    commands: List[EventCommandTokens]

COMMAND_SENTINEL = '__COMMAND_SENTINEL'