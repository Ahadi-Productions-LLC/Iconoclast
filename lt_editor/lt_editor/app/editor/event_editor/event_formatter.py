from typing import List

from app.events.event_commands import parse_text_to_command

def format_tabs(script: List[str]) -> List[str]:
    num_tabs = 0
    formatted = []
    for line in script:
        command, _ = parse_text_to_command(line)
        if command and command.nid in ('else', 'elif', 'end', 'endf'):
            num_tabs -= 1
        formatted.append('    ' * num_tabs + line.lstrip())
        if command and command.nid in ('if', 'elif', 'else', 'for'):
            num_tabs += 1
    return formatted

def format_event_script(script: str) -> str:
    as_lines = script.split('\n')
    as_lines = format_tabs(as_lines)
    return '\n'.join(as_lines)

if __name__ == "__main__":
    script = """
if;a = b
speak;Eirika;hi
elif;a = c
speak;Eirika;hello
if;True
speak;Eirika;two nest
end
end
"""
    print(format_event_script(script))
