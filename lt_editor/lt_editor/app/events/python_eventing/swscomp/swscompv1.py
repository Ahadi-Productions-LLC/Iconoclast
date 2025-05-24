from __future__ import annotations
import re
from app.events.event_structs import EOL, EventCommandTokens, ParseMode
from app.events.python_eventing.swscomp.comp_utils import COMMAND_SENTINEL, ScriptWithSentinel
from app.utilities.str_utils import RAW_NEWLINE, mirror_bracket

EOF = "EOF"

class SWSCompilerV1():
    def __init__(self, event_script: str) -> None:
        self.source = event_script.replace(RAW_NEWLINE, '\n')

    @staticmethod
    def parse_line(line: str) -> EventCommandTokens:
        # should be of format:
        # $speak eirika "Hello" "This is a second line" (1, 2, 3), flag_1 flag_2
        # should correctly separate the above by spaces, respecting quotes and parens, and partitions the last pieces into flags

        if not line.lstrip().startswith('$'):
            return None
        start_idx = line.index('$') + 1

        tokens = ['']
        token_idxs = [start_idx]
        tok_idx = start_idx
        c_idx = start_idx
        flag_idx = 99

        def advance():
            nonlocal c_idx
            c_idx = min(c_idx + 1, len(line))

        def fin_tok():
            nonlocal tok_idx
            if tokens[-1]:
                tokens.append('')
                token_idxs.append(tok_idx)

        def cadd(c: str):
            if not tokens[-1]:
                token_idxs[-1] = c_idx
            tokens[-1] += c

        def cchar() -> str:
            if c_idx < len(line):
                return line[c_idx]
            return EOF

        def peek():
            if c_idx + 1 < len(line):
                return line[c_idx + 1]
            return EOF

        while c_idx < len(line):
            c = cchar()
            if c in ("'", '"'):
                cadd(c)
                advance()
                while cchar() != c and cchar() != EOF:
                    nc = cchar()
                    cadd(nc)
                    advance()
                cadd(c)
            elif c == '#':
                fin_tok()
                tokens[-1] = EOL
                token_idxs[-1] = c_idx
                break
            elif c in '([{':
                level = 1
                cc = mirror_bracket(c)
                cadd(c)
                in_str = False
                while level != 0 and peek() != EOF:
                    advance()
                    nc = cchar()
                    cadd(nc)
                    if nc in ("'", '"'):
                        in_str = not in_str
                    if not in_str:
                        if nc == cc: # found close
                            level -= 1
                        elif nc == c: # found another open
                            level += 1
            elif c == ' ':
                fin_tok()
                tok_idx = c_idx + 1
            elif c == ',':
                fin_tok()
                flag_idx = len(tokens) - 1
            else:
                cadd(c)
            advance()
        if not tokens:
            tokens = ['']
        parsed = EventCommandTokens(tokens, line, token_idxs, start_idx - 1)
        parsed._flag_idx = flag_idx
        return parsed

    def compile_sws(self) -> ScriptWithSentinel:
        # takes in a python event script
        # removes all event commands, and replaces them with COMMAND_SENTINEL
        # stores the parsed event commands as data
        as_lines = self.source.split("\n")
        found_commands = []
        for idx, line in enumerate(as_lines):
            if line.strip().startswith('$'):
                # insert command sentinel
                as_lines[idx] = COMMAND_SENTINEL
                found_commands.append(SWSCompilerV1.parse_line(line))
        return ScriptWithSentinel('\n'.join(as_lines), found_commands)