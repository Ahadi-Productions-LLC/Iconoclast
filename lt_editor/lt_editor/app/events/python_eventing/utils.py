from typing import Any, Dict, Generator, List, Optional, Set, Tuple, Type

from app.events.event_structs import EventCommandTokens
from app.utilities.str_utils import SHIFT_NEWLINE

from .. import event_commands

EVENT_INSTANCE = "EC"
EVENT_GEN_NAME = "_lt_event_gen"

SAVE_COMMANDS: List[event_commands.EventCommand] = [event_commands.BattleSave, event_commands.Prep, event_commands.Base]
SAVE_COMMAND_NIDS: Set[str] = set([cmd.nid for cmd in SAVE_COMMANDS] + [cmd.nickname for cmd in SAVE_COMMANDS])
EVENT_CALL_COMMANDS: List[event_commands.EventCommand] = [event_commands.TriggerScript, event_commands.TriggerScriptWithArgs]
EVENT_CALL_COMMAND_NIDS: Set[str] = set([cmd.nid for cmd in EVENT_CALL_COMMANDS] + [cmd.nickname for cmd in EVENT_CALL_COMMANDS])

DO_NOT_EXECUTE_SENTINEL = -1

class ResumeCheck():
    def __init__(self, line_no_to_catch: int) -> None:
        self.catching_up = True
        self.line_no = line_no_to_catch

    def check_set_caught_up(self, line_no):
        is_catching_up = self.catching_up
        if line_no == self.line_no:
            self.catching_up = False
        return is_catching_up

def to_py_event_command(tokens: EventCommandTokens) -> Tuple[str, int]:
    """returns command text, and indent"""
    command = tokens.command()
    args = ','.join(tokens.args()).replace(SHIFT_NEWLINE, ' ')
    # flags are always strings
    flags = ','.join([f'"{flag}"' for flag in tokens.flags()])
    return "%s(%s).set_flags(%s)" % (command, args, flags), tokens.start_idx

def create_null_event() -> Generator:
    yield DO_NOT_EXECUTE_SENTINEL, None
