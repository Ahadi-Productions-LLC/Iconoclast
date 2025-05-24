import logging
import unittest
from pathlib import Path
from app.events.event_prefab import EventCatalog, EventPrefab

from app.events.python_eventing.errors import CannotUseYieldError, InvalidCommandError, InvalidPythonError, MalformedTriggerScriptCall, NestedEventError, NoSaveInLoopError
from app.events.python_eventing.analyzer import PyEventAnalyzer

class PyEventAnalyzerUnitTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_analyzer_checks_version(self):
        # version 00, which will likely never exist
        script = """#pyev00"""
        ppsr = PyEventAnalyzer()
        errors = ppsr.verify_event("analyzer_bad_version", script)
        error_lines = set([e.line_num for e in errors])
        self.assertEqual(len(error_lines), 1)
        self.assertIn(1, error_lines)
        self.assertEqual(errors[0].__class__, InvalidPythonError)

    def test_analyzer_catches_forbidden_symbols(self):
        script_path = Path(__file__).parent / 'data' / 'analyzer_forbidden_symbols.pyevent'
        script_source = script_path.read_text()
        ppsr = PyEventAnalyzer()

        errors = ppsr.verify_event('analyzer_forbidden_symbols', script_source)

        error_lines = set([e.line_num for e in errors])
        self.assertEqual(len(error_lines), 3)
        self.assertIn(4, error_lines)
        self.assertIn(5, error_lines)
        self.assertIn(6, error_lines)
        self.assertEqual(errors[0].__class__, InvalidPythonError)
        self.assertEqual(errors[1].__class__, InvalidPythonError)
        self.assertEqual(errors[2].__class__, InvalidPythonError)

    def test_analyzer_catches_errors(self):
        script_path = Path(__file__).parent / 'data' / 'analyzer.pyevent'
        script_source = script_path.read_text()
        ppsr = PyEventAnalyzer()

        errors = ppsr.verify_event('analyzer_test', script_source)
        error_lines = set([e.line_num for e in errors])
        self.assertIn(21, error_lines)
        self.assertIn(22, error_lines)
        self.assertEqual(len(error_lines), 2)
        self.assertEqual(errors[0].__class__, NestedEventError)
        self.assertEqual(errors[1].__class__, InvalidCommandError)

    def test_analyzer_catches_bad_saves(self):
        script_path = Path(__file__).parent / 'data' / 'analyzer_save_in_for_loop.pyevent'
        script_source = script_path.read_text()
        script_prefab = EventPrefab('analyzer_save_in_for_loop')
        script_prefab.source = script_source

        nested_script_path = Path(__file__).parent / 'data' / 'save_in_trigger_script_in_for_loop.pyevent'
        nested_script_source = nested_script_path.read_text()
        nested_prefab = EventPrefab('save_in_trigger_script_in_for_loop')
        nested_prefab.source = nested_script_source

        catalog = EventCatalog([script_prefab, nested_prefab])
        ppsr = PyEventAnalyzer(catalog)

        errors = ppsr.verify_event('analyzer_save_in_for_loop', script_source)
        self.assertEqual(errors[0].__class__, NoSaveInLoopError)
        self.assertEqual(errors[1].__class__, NoSaveInLoopError)
        self.assertEqual(errors[2].__class__, MalformedTriggerScriptCall)
        self.assertEqual(errors[3].__class__, MalformedTriggerScriptCall)

    def test_analyzer_forbids_yields(self):
        script_path = Path(__file__).parent / 'data' / 'analyzer_yields.pyevent'
        script_source = script_path.read_text()
        ppsr = PyEventAnalyzer()

        errors = ppsr.verify_event('analyzer_test', script_source)
        error_lines = set([e.line_num for e in errors])
        self.assertIn(4, error_lines)
        self.assertEqual(len(error_lines), 1)
        self.assertEqual(errors[0].__class__, CannotUseYieldError)