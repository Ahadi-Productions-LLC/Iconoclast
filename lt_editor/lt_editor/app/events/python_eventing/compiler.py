from typing import Dict, Type
from app.events.event_prefab import get_event_version
from app.events.event_version import EventVersion
from app.events.python_eventing.postcomp.compiled_event import CompiledEvent
from app.events.python_eventing.postcomp.engine_postcomp import PostComp
from app.events.python_eventing.postcomp.analyzer_postcomp import AnalyzerPostComp
from app.events.python_eventing.swscomp.swscompv1 import SWSCompilerV1

VERSION_MAP: Dict[EventVersion, Type[SWSCompilerV1]] = {
    EventVersion.PYEV1: SWSCompilerV1
}

class Compiler():
    @staticmethod
    def compile(event_name: str, script: str, command_pointer: int = 0) -> CompiledEvent:
        version = get_event_version(script)
        if not version in VERSION_MAP:
            raise ValueError("In event %s: Unknown python event version: '%s'" %(event_name, version))
        sws_compiler = VERSION_MAP[version]
        original_script = script
        sentinel_script = sws_compiler(script).compile_sws()
        compiled_script = PostComp.postcompile(sentinel_script, command_pointer)
        return CompiledEvent(event_name, original_script, compiled_script)

    @staticmethod
    def compile_analyzer(script: str) -> str:
        version = get_event_version(script)
        if not version in VERSION_MAP:
            raise ValueError("Unknown python event version: '%s'" %(version))
        sws_compiler = VERSION_MAP[version]
        sentinel_script = sws_compiler(script).compile_sws()
        return AnalyzerPostComp.postcomp(sentinel_script)
