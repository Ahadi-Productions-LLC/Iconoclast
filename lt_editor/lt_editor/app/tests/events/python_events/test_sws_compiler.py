import logging
import unittest
from app.events.event_structs import EOL
from app.events.python_eventing.swscomp.swscompv1 import SWSCompilerV1

class SWSCompilationTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_swscompilerv1(self):
        script = """
$speak eirika "Hello", no_block
for i in range(5):
    $speak "Seth" "Goodbye", yes_block
    $half_finished_comman
    $finished_command ('not_done_with_arg',
    $comment "Comment arg" # begin comment
"""
        expected_commands_and_indices = [
            (['speak', 'eirika', '"Hello"', 'no_block'], [1, 7, 14, 23], 3),
            (['speak', '"Seth"', '"Goodbye"', 'yes_block'], [5, 11, 18, 29], 3),
            (['half_finished_comman'], [5], 99),
            (['finished_command', "('not_done_with_arg',"], [5, 22], 99),
            (['comment', '"Comment arg"', EOL], [5, 13, 27], 99),
        ]
        # we should maintain whitespace (for indentation)
        # and newline count (for error logging)
        expected_source = """
__COMMAND_SENTINEL
for i in range(5):
__COMMAND_SENTINEL
__COMMAND_SENTINEL
__COMMAND_SENTINEL
__COMMAND_SENTINEL
"""

        res = SWSCompilerV1(script).compile_sws()
        self.assertEqual(res.source, expected_source)
        self.assertEqual(len(res.commands), len(expected_commands_and_indices))
        for i in range(len(res.commands)):
            r = res.commands[i]
            exp = expected_commands_and_indices[i]
            self.assertEqual(r.tokens, exp[0])
            self.assertEqual(r.token_idx, exp[1])
            self.assertEqual(r._flag_idx, exp[2])