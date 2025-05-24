import logging
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from app.events import event_commands
from app.events.python_eventing.python_event_processor import PythonEventProcessor
from app.tests.mocks.mock_game import get_mock_game


class PythonEventProcessorUnitTests(unittest.TestCase):
    def setUp(self):
        self.mock_game = get_mock_game()
        mock_unit = MagicMock()
        mock_unit.name = "Erika" # deliberate spelling
        get_unit = lambda name: mock_unit
        self.mock_game.get_unit = get_unit
        self.mock_game.level_vars = {"TimesRescued": 10, "TimesToRepeat": 3}
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_event_processor(self):
        script_path = Path(__file__).parent / 'data' / 'test_event.pyevent'
        script_source = script_path.read_text()
        processor = PythonEventProcessor('test', script_source, self.mock_game)

        # normal command
        mu_speak = processor.fetch_next_command()
        self.assertTrue(isinstance(mu_speak, event_commands.Speak))
        self.assertEqual(mu_speak.parameters['SpeakerOrStyle'], 'MU')
        self.assertEqual(mu_speak.parameters['Text'], 'I am a custom named character.')

        # eval
        seth_speak = processor.fetch_next_command()
        self.assertTrue(isinstance(seth_speak, event_commands.Speak))
        self.assertEqual(seth_speak.parameters['SpeakerOrStyle'], 'Seth')
        self.assertEqual(seth_speak.parameters['Text'], 'Princess Erika!')

        # variable
        rescue_speak = processor.fetch_next_command()
        self.assertTrue(isinstance(rescue_speak, event_commands.Speak))
        self.assertEqual(rescue_speak.parameters['SpeakerOrStyle'], 'MU')
        self.assertEqual(rescue_speak.parameters['Text'], "You've rescued me 10 times")

        # if/else/processing
        iftrue_speak = processor.fetch_next_command()
        self.assertTrue(isinstance(iftrue_speak, event_commands.Speak))
        self.assertEqual(iftrue_speak.parameters['SpeakerOrStyle'], 'MU')
        self.assertEqual(iftrue_speak.parameters['Text'], "A bit ridiculous isn't it?")

        # for
        eirika_for = processor.fetch_next_command()
        seth_for = processor.fetch_next_command()
        self.assertTrue(isinstance(eirika_for, event_commands.Speak))
        self.assertEqual(eirika_for.parameters['SpeakerOrStyle'], 'Eirika')
        self.assertEqual(eirika_for.parameters['Text'], "My name is Eirika")
        self.assertTrue(isinstance(seth_for, event_commands.Speak))
        self.assertEqual(seth_for.parameters['SpeakerOrStyle'], 'Seth')
        self.assertEqual(seth_for.parameters['Text'], "My name is Seth")

        # while
        first = processor.fetch_next_command()
        first_dec = processor.fetch_next_command()
        self.mock_game.level_vars['TimesToRepeat'] -= 1
        second = processor.fetch_next_command()
        second_dec = processor.fetch_next_command()
        self.mock_game.level_vars['TimesToRepeat'] -= 1
        third = processor.fetch_next_command()
        third_dec = processor.fetch_next_command()
        self.mock_game.level_vars['TimesToRepeat'] -= 1
        for cmd in [first, second, third]:
            self.assertTrue(isinstance(cmd, event_commands.Speak))
            self.assertEqual(cmd.parameters['SpeakerOrStyle'], 'MU')
            self.assertEqual(cmd.parameters['Text'], 'I am speaking in a while loop')

        for cmd in [first_dec, second_dec, third_dec]:
            self.assertTrue(isinstance(cmd, event_commands.IncLevelVar))
            self.assertEqual(cmd.parameters['Nid'], 'TimesToRepeat')
            self.assertEqual(cmd.parameters['Expression'], -1)

        processor.fetch_next_command()
        self.assertTrue(processor.is_finished)

    def test_save_restore_processor_state(self):
        script_path = Path(__file__).parent / 'data' / 'test_save_event_state.pyevent'
        script_source = script_path.read_text()
        processor = PythonEventProcessor('test_save_event_state', script_source, self.mock_game)

        self.mock_game.level_vars['SomeState'] = True
        self.mock_game.level_vars['WhileState'] = True

        processor.fetch_next_command()
        # processor just returned "FirstCommand"
        # first SAVE_HERE

        processor2 = PythonEventProcessor.restore(processor.save(), self.mock_game)
        next_command = processor2.fetch_next_command()
        self.assertTrue(isinstance(next_command, event_commands.Alert))
        self.assertEqual(next_command.parameters['String'], 'SecondCommand')
        next_command = processor2.fetch_next_command()
        self.assertTrue(isinstance(next_command, event_commands.Alert))
        self.assertEqual(next_command.parameters['String'], 'SomeStateTrueCommand')
        next_command = processor2.fetch_next_command()
        self.assertTrue(isinstance(next_command, event_commands.LevelVar))
        self.assertEqual(next_command.parameters['Nid'], 'SomeState')
        self.assertEqual(next_command.parameters['Expression'], False)
        self.mock_game.level_vars['SomeState'] = False

        # second SAVE_HERE
        processor3 = PythonEventProcessor.restore(processor2.save(), self.mock_game)
        next_command = processor3.fetch_next_command()
        self.assertTrue(isinstance(next_command, event_commands.Alert))
        self.assertEqual(next_command.parameters['String'], 'ResumedAndStillSomeState')
        # sanity check to make sure that a fresh version would not take the conditional
        # under altered state
        processor1_second = PythonEventProcessor.restore(processor.save(), self.mock_game)
        processor1_second.fetch_next_command()
        next_command = processor1_second.fetch_next_command()
        self.assertTrue(isinstance(next_command, event_commands.Alert))
        self.assertEqual(next_command.parameters['String'], 'ShouldNeverHappen')

        next_command = processor3.fetch_next_command()
        self.assertTrue(isinstance(next_command, event_commands.Alert))
        self.assertEqual(next_command.parameters['String'], 'ExecutingWhile')
        next_command = processor3.fetch_next_command()
        self.assertTrue(isinstance(next_command, event_commands.LevelVar))
        self.assertEqual(next_command.parameters['Nid'], 'WhileState')
        self.assertEqual(next_command.parameters['Expression'], False)
        self.mock_game.level_vars['WhileState'] = False

        # third SAVE_HERE
        processor4 = PythonEventProcessor.restore(processor3.save(), self.mock_game)
        next_command = processor4.fetch_next_command()
        self.assertTrue(isinstance(next_command, event_commands.Alert))
        self.assertEqual(next_command.parameters['String'], 'ResumedWhile')
        next_command = processor4.fetch_next_command()
        self.assertTrue(isinstance(next_command, event_commands.Alert))
        self.assertEqual(next_command.parameters['String'], 'PreviousCommandsShouldOnlyBeCalledOnce')

        # another sanity check - if condition is off, it should never enter the loop
        processor3_second = PythonEventProcessor.restore(processor2.save(), self.mock_game)
        processor3_second.fetch_next_command()
        next_command = processor3_second.fetch_next_command()
        self.assertTrue(isinstance(next_command, event_commands.Alert))
        self.assertEqual(next_command.parameters['String'], 'PreviousCommandsShouldOnlyBeCalledOnce')

        # final sanity check - if condition is on, then a resume should still repeat the loop
        processor4_second = PythonEventProcessor.restore(processor3.save(), self.mock_game)
        self.mock_game.level_vars['WhileState'] = True
        next_command = processor4_second.fetch_next_command()
        self.assertTrue(isinstance(next_command, event_commands.Alert))
        self.assertEqual(next_command.parameters['String'], 'ResumedWhile')
        next_command = processor4_second.fetch_next_command()
        self.assertTrue(isinstance(next_command, event_commands.Alert))
        self.assertEqual(next_command.parameters['String'], 'ExecutingWhile')
