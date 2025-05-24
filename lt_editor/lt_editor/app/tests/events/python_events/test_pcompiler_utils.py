import logging
import unittest

from app.events.event_structs import EventCommandTokens
from app.events.python_eventing.utils import to_py_event_command

class CompilerUtilsUnitTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def testEventCommandDataToString(self):
        ec = EventCommandTokens(["speak",'eirika_var', '"I am speaking in a string"', 'no_block'], None, None, 0)
        ec._flag_idx = 3
        expected = 'speak(eirika_var,"I am speaking in a string").set_flags("no_block")'
        self.assertEqual(to_py_event_command(ec)[0], expected)