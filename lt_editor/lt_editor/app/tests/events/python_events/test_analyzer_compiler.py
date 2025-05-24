import logging
import unittest
from app.events.python_eventing.postcomp.analyzer_postcomp import AnalyzerPostComp

from app.events.python_eventing.swscomp.swscompv1 import SWSCompilerV1

class AnalyzerPostCompTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_analyzer_postcomp(self):
        script = """
$speak eirika "Hello", no_block
for i in range(5):
    $speak "Seth" "Goodbye", yes_block"""

        expected_comp = """
EC.speak(eirika,"Hello").set_flags("no_block")
for i in range(5):
    EC.speak("Seth","Goodbye").set_flags("yes_block")"""

        sws = SWSCompilerV1(script).compile_sws()
        res = AnalyzerPostComp.postcomp(sws)
        self.assertEqual(res, expected_comp)