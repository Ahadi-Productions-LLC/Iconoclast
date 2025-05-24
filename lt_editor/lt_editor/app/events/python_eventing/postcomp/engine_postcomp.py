from __future__ import annotations

import ast
from app.events.python_eventing.postcomp.engine_header import HEADER_IMPORT
from app.events.python_eventing.swscomp.comp_utils import (COMMAND_SENTINEL,
                                                   ScriptWithSentinel)
from app.events.python_eventing.utils import EVENT_GEN_NAME, EVENT_INSTANCE, to_py_event_command

class PostComp():
    @staticmethod
    def postcompile(sentinel_script: ScriptWithSentinel, command_pointer: int = 0) -> str:
        script = PostComp._assemble_script_with_yields_and_command_pointer(sentinel_script)
        script = PostComp._insert_command_pointer_conditional_skips(script)
        script = PostComp._wrap_generator(script, command_pointer)
        script = PostComp._insert_header(script)
        return script

    @staticmethod
    def _assemble_script_with_yields_and_command_pointer(sentinel_script: ScriptWithSentinel):
        n_commands = sentinel_script.source.count(COMMAND_SENTINEL)
        script = sentinel_script.source
        if not n_commands == len(sentinel_script.commands):
            raise ValueError("Number of commands does not match number of sentinels.")
        for i in range(n_commands):
            command_data = sentinel_script.commands[i]
            command, indent = to_py_event_command(command_data)
            command = "%s.%s" % (EVENT_INSTANCE, command)
            resume_control = f"DO_NOT_EXECUTE_SENTINEL if (_PTR >= {i+1} and RESUME_CHECK.check_set_caught_up({i+1})) else {i+1}"
            compiled_command = "yield (%s, %s)" % (resume_control, command)
            compiled_command = ' ' * indent + compiled_command
            script = script.replace(COMMAND_SENTINEL, compiled_command, 1)
        return script

    @staticmethod
    def _get_yield_value(node: ast.Yield):
        return node.value.elts[0].orelse.n

    @staticmethod
    def _insert_command_pointer_conditional_skips(script_with_yields: str):
        parsed = ast.parse(script_with_yields)

        def fetch_pointers_under_conditional(cond_node: ast.If | ast.While):
            starting_nodes = cond_node.body
            def recursive_fetch_yields(node: ast.stmt):
                pointers_found = []
                for cnode in ast.iter_child_nodes(node):
                    if isinstance(cnode, ast.Yield):
                        pointers_found.append(PostComp._get_yield_value(cnode))
                    else:
                        pointers_found += recursive_fetch_yields(cnode)
                return pointers_found
            return [line_pointer for cnode in starting_nodes for line_pointer in recursive_fetch_yields(cnode)]

        as_lines = script_with_yields.split('\n')
        # inefficient algorithm with no memoization - i don't expect this to be a huge bottleneck, but could be improved
        for cnode in ast.walk(parsed):
            if isinstance(cnode, ast.If) or isinstance(cnode, ast.While):
                pointers_in_conditional = fetch_pointers_under_conditional(cnode)
                line = as_lines[cnode.lineno - 1]
                pointers_as_str = ', '.join([str(i) for i in pointers_in_conditional])
                if isinstance(cnode, ast.If):
                    # line starts with if or elif
                    line = line.replace('if', f'if _PTR in [{pointers_as_str}] or', 1)
                    as_lines[cnode.lineno - 1] = line
                else:
                    line = line.replace('while', f'while (_PTR in [{pointers_as_str}] and RESUME_CHECK.catching_up) or', 1)
                    as_lines[cnode.lineno - 1] = line

        return '\n'.join(as_lines)

    @staticmethod
    def _wrap_generator(script: str, resume_command_pointer = -1):
        # wraps the entire script in a generator
        as_lines = script.split("\n")
        as_lines = [f"\t{line}" for line in as_lines]
        as_lines = [f"_PTR = {resume_command_pointer}",
                    f"def {EVENT_GEN_NAME}():"] + as_lines
        if resume_command_pointer:
            as_lines = [f'RESUME_CHECK = ResumeCheck({resume_command_pointer})'] + as_lines
        return '\n'.join(as_lines)


    @staticmethod
    def _insert_header(script: str):
        """Insert necessary imports for the environment"""
        script = HEADER_IMPORT + '\n' + script
        return script

