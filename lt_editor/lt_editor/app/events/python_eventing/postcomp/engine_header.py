from app.events.python_eventing.utils import EVENT_INSTANCE

HEADER_IMPORT = f"""
import app.events.python_eventing.python_event_command_wrappers as {EVENT_INSTANCE}
from app.events.python_eventing.utils import DO_NOT_EXECUTE_SENTINEL, ResumeCheck
from app.events.speak_style import SpeakStyle
from app.constants import WINHEIGHT, WINWIDTH
from app.engine import (action, background, dialog, engine, evaluate,
                        image_mods, item_funcs)
from app.engine.movement import movement_funcs
from app.utilities import str_utils, utils, static_random
"""