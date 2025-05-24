import sys

def is_editor_engine_built_version():
    return hasattr(sys, 'frozen')