from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Type

from app.events.event_prefab import EventCatalog, get_event_version
from app.events.event_version import EventVersion
from app.events.python_eventing.compiler import VERSION_MAP, Compiler
from app.events.python_eventing.errors import CannotUseYieldError, InvalidCommandError, InvalidPythonError, MalformedTriggerScriptCall, NestedEventError, NoSaveInLoopError, EventError
from app.events.python_eventing.postcomp.analyzer_postcomp import AnalyzerPostComp
from app.events.python_eventing.swscomp.comp_utils import COMMAND_SENTINEL
from app.events.python_eventing.utils import EVENT_CALL_COMMAND_NIDS, EVENT_INSTANCE, SAVE_COMMAND_NIDS
from app.utilities.typing import NID

from .. import event_commands

def check_valid_event_function_call(node: ast.stmt):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
        isinstance(node.func.value, ast.Name) and node.func.value.id == EVENT_INSTANCE:
        event_command_nid = node.func.attr
        if not event_command_nid in event_commands.get_all_event_commands(EventVersion.PYEV1):
            return False
    return True

def check_safe_event_function_call(node: ast.stmt, parents: List[ast.stmt]):
    """Expectations: if 'node' is an EventFunction call, e.g. 'speak(*args)'
      and the parents are the ast nodes above it. We assert that the immediate
      parent must be an solitary Expr, and that this cannot be nested in a function.

    Rationale:
      The core concept of this event engine is this: that we can yield
      EventCommand objects, thus allowing us to cede control
      to the actual Event object and execute the yielded EventCommand.
      Once the EventCommand is executed, we then return control
      to the Processor, which can resume the execution of the script,
      until the next EventCommand is hit, which is then yielded, control ceded,
      etc.

      Therefore, the most important rule is that every single event function
      *can* be yielded one-by-one. This fails, for example, for the line,
      `speak(args...) and speak(args2...)`. This line tries to
      execute both speak commands at once, which is not how the EventEngine
      works. Therefore, it is invalid. Likewise, creating a function definition
      with multiple EventCommands and then calling them would also be problematic.

      Therefore, we must be sure to uphold that EventCommand are *always* yieldable, i.e.
      either top-level Exprs, or equivalent (in the bodies of for and while-loops, which can be yielded)
      and not args to a Function call, not values in e.g. a BinOp, and not part of the for loop's iterator
      or while loop's test.
    """
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
      isinstance(node.func.value, ast.Name) and node.func.value.id == EVENT_INSTANCE:
        if parents[-1].__class__ != ast.Expr and not (isinstance(parents[-1], ast.Attribute) and parents[-1].attr == 'set_flags'):
            return False
        elif any([parent.__class__ == ast.FunctionDef for parent in parents]):
            return False
    return True

def is_save_call(node: ast.stmt):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
        isinstance(node.func.value, ast.Name) and node.func.value.id == EVENT_INSTANCE and \
            node.func.attr in SAVE_COMMAND_NIDS:
        return True
    return False

def is_trigger_script_call(node: ast.stmt):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
        isinstance(node.func.value, ast.Name) and node.func.value.id == EVENT_INSTANCE and \
            node.func.attr in EVENT_CALL_COMMAND_NIDS:
        return True
    return False

def check_valid_trigger_script_call(node: ast.stmt):
    if is_trigger_script_call(node):
        if len(node.args) > 0 and isinstance(node.args[0], ast.Str):
            return True
        return False
    return True

def get_script_from_trigger_script_call(node: ast.Call) -> str:
    try:
        if is_trigger_script_call(node):
            return node.args[0].s
    except:
        raise ValueError("Not a valid TriggerScript call")

@dataclass
class EventContext():
    event_name: NID
    source_as_lines: List[str]
    source_as_ast: ast.Module

    @classmethod
    def from_event(cls: Type[EventContext], event_name: str, source: str):
        as_lines = source.split('\n')
        as_ast = ast.parse(Compiler.compile_analyzer(source))
        return cls(event_name, as_lines, as_ast)

class PyEventAnalyzer():
    def __init__(self, event_db: EventCatalog = None) -> None:
        self._catalog: EventCatalog = event_db
        self._parsed_events: Dict[NID, EventContext] = {}

    def get_event_info(self, event_name: str) -> Optional[EventContext]:
        try:
            if event_name not in self._parsed_events and self._catalog and event_name in self._catalog:
                self._parsed_events[event_name] = EventContext.from_event(event_name, self._catalog.get_from_nid(event_name).source)
            return self._parsed_events.get(event_name)
        except:
            return None

    def verify_event(self, event_name: str, source: str = None) -> List[EventError]:
        self._parsed_events.clear() # no reason to load all events simultaneously in memory
        event_info = None
        if not source:
            source = self._catalog.get_from_nid(event_name).source
        python_version_errors = self._verify_python_version_is_correct(event_name, source)
        if python_version_errors:
            return [python_version_errors]
        forbidden_symbols_errors = self._verify_no_forbidden_symbols(event_name, source)
        if forbidden_symbols_errors:
            return forbidden_symbols_errors
        compiled = Compiler.compile_analyzer(source)
        is_invalid_python_error = self._verify_valid_python(event_name, compiled, source)
        if is_invalid_python_error:
            return [is_invalid_python_error]

        event_info = EventContext.from_event(event_name, compiled)
        self._parsed_events[event_name] = event_info

        event_command_call_errors = self._verify_event_calls(event_info)
        loop_save_errors = self._verify_no_loop_save(event_info)
        yield_errors = self._verify_no_yields(event_info)
        return event_command_call_errors + loop_save_errors + yield_errors

    def _verify_python_version_is_correct(self, event_name: str, source: str) -> Optional[InvalidPythonError]:
        version = get_event_version(source)
        if not version or version not in VERSION_MAP:
            err = InvalidPythonError(event_name, 1, source.split('\n')[0])
            err.what = "In event %s: Unknown python event version: %s" %(event_name, version)
            return err

    def _verify_no_forbidden_symbols(self, event_name: str, source: str) -> Optional[List[InvalidPythonError]]:
        as_lines = source.split('\n')
        errors = []
        for idx, line in enumerate(as_lines):
            if COMMAND_SENTINEL in line:
                error = InvalidPythonError(event_name, idx + 1, line)
                error.what = f"{COMMAND_SENTINEL} invalid symbol. Do not use this string in events."
                errors.append(error)
        return errors

    def _verify_valid_python(self, event_name: str, compiled: str, source: str) -> Optional[InvalidPythonError]:
        try:
            ast.parse(compiled)
            return None
        except Exception as e:
            as_lines = source.split('\n')
            source_as_lines = compiled.split('\n')
            message = "%s => %s" % (as_lines[e.lineno - 1], source_as_lines[e.lineno - 1])
            error = InvalidPythonError(event_name, e.lineno, message)
            error.what = e.msg
            return error

    def _verify_no_yields(self, event: EventContext) -> List[CannotUseYieldError]:
        """Since the event engine uses yields as its primary mode of extracting EventCommands,
        yields should not be used in the script."""
        yield_errors: List[CannotUseYieldError] = []
        for cnode in ast.walk(event.source_as_ast):
            if isinstance(cnode, ast.Yield):
                yield_errors.append(CannotUseYieldError(event.event_name, cnode.lineno, event.source_as_lines[cnode.lineno - 1]))
        return yield_errors

    def _verify_event_calls(self, event: EventContext) -> List[EventError]:
        """see `check_safe_event_function_call` above for details on what this function verifies.
        It also verifies that all event calls are valid commands, via `check_valid_event_function_call`.
        """
        def recursive_tree_verify(node: ast.stmt, parents: List[ast.stmt] = None):
            if parents is None:
                curr_parents = []
            else:
                curr_parents = parents[:]
            unsafe_event_function_calls: List[EventError] = []
            # base case
            if not check_safe_event_function_call(node, curr_parents):
                unsafe_event_function_calls.append(NestedEventError(event.event_name, node.lineno, event.source_as_lines[node.lineno - 1]))
            if not check_valid_event_function_call(node):
                unsafe_event_function_calls.append(InvalidCommandError(event.event_name, node.lineno, event.source_as_lines[node.lineno - 1]))
            curr_parents.append(node)
            for cnode in ast.iter_child_nodes(node):
                unsafe_event_function_calls += recursive_tree_verify(cnode, curr_parents)
            return unsafe_event_function_calls
        return recursive_tree_verify(event.source_as_ast)

    def _verify_no_loop_save(self, event: EventContext, from_event_names: List[str] = None, from_event_lines: List[int] = None) -> List[NoSaveInLoopError | MalformedTriggerScriptCall]:
        """Events cannot be resumed in the middle of a for loop. Therefore, any save commands
        cannot be run inside a for loop. Because for loops can call other events, we
        must also verify the other scripts."""
        from_event_names = from_event_names[:] if from_event_names else []
        from_event_lines = from_event_lines[:] if from_event_lines else []
        # if this is the first level of event, we don't care about direct mid-event saves
        # but if this is a nested event, any save is suspect
        is_top_level_event = True if (not from_event_lines and not from_event_names) else False
        current_event = event.event_name

        def generate_error_info(node: ast.stmt) -> Tuple[list, list, list]:
            previous_event_list = [self.get_event_info(event_name).source_as_lines[event_line - 1] for event_name, event_line in zip(from_event_names, from_event_lines)]
            error_info = (from_event_names + [current_event], from_event_lines + [node.lineno], previous_event_list + [event.source_as_lines[node.lineno - 1]])
            return error_info

        def recursive_tree_verify(snode: ast.stmt, parents: List[Type[ast.stmt]] = None):
            unsafe_save_calls: List[NoSaveInLoopError] = []
            if parents is None:
                curr_parents = []
            else:
                curr_parents = parents[:]
            for cnode in ast.iter_child_nodes(snode):
                if is_save_call(cnode):                                 # if there's any save call, fail in two conditions
                    if not is_top_level_event or ast.For in curr_parents:   # if we are already in a nested script, or we're in a for loop
                        unsafe_save_calls.append(NoSaveInLoopError(*generate_error_info(cnode)))
                elif is_trigger_script_call(cnode):                     # likewise, if we're triggering another script
                    if not is_top_level_event or ast.For in curr_parents:   # in a nested script, or under a for loop
                        if not check_valid_trigger_script_call(cnode):  # enforce that all trigger scripts go to a specified other event
                            unsafe_save_calls.append(MalformedTriggerScriptCall(*generate_error_info(cnode)))
                        else:                                           # if it does, now we recurse into the other event
                            nested_event_nid = get_script_from_trigger_script_call(cnode)
                            nested_event_info = self.get_event_info(nested_event_nid)
                            if not nested_event_info:
                                unsafe_save_calls.append(MalformedTriggerScriptCall(*generate_error_info(cnode)))
                            else:
                                error_info = generate_error_info(cnode)
                                triggered_script_unsafe_save_calls = self._verify_no_loop_save(nested_event_info, error_info[0], error_info[1])
                                unsafe_save_calls += triggered_script_unsafe_save_calls
                else: # command is neither trigger script nor save; continue walking
                    unsafe_save_calls += recursive_tree_verify(cnode, curr_parents + [snode.__class__])
            return unsafe_save_calls
        return recursive_tree_verify(event.source_as_ast)