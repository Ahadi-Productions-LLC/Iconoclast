import logging
import unittest

from app.events.python_eventing.swscomp.comp_utils import EventCommandTokens, ScriptWithSentinel
from app.events.python_eventing.postcomp.engine_postcomp import PostComp

class SecondPassCompilationUnitTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_assemble_yields_command_pointer(self):
        script = """
__COMMAND_SENTINEL
for i in range(5):
__COMMAND_SENTINEL"""

        commands = [
            EventCommandTokens(['speak', 'eirika', '"Hello"' ,'no_block'], None, None, 0),
            EventCommandTokens(['speak', '"Seth"', '"Goodbye"', 'yes_block'], None, None, 4),
        ]
        commands[0]._flag_idx = 3
        commands[1]._flag_idx = 3

        expected = """
yield (DO_NOT_EXECUTE_SENTINEL if (_PTR >= 1 and RESUME_CHECK.check_set_caught_up(1)) else 1, EC.speak(eirika,"Hello").set_flags("no_block"))
for i in range(5):
    yield (DO_NOT_EXECUTE_SENTINEL if (_PTR >= 2 and RESUME_CHECK.check_set_caught_up(2)) else 2, EC.speak("Seth","Goodbye").set_flags("yes_block"))"""

        res = PostComp._assemble_script_with_yields_and_command_pointer(ScriptWithSentinel(script, commands))
        self.assertEqual(res, expected)