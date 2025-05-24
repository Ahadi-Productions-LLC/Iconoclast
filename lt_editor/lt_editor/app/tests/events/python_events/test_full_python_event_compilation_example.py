from io import StringIO
import logging
from pathlib import Path
import unittest
from app.events.event_structs import EventCommandTokens
from app.events.python_eventing.postcomp.analyzer_postcomp import AnalyzerPostComp
from app.events.python_eventing.postcomp.engine_postcomp import PostComp

from app.events.python_eventing.swscomp.swscompv1 import SWSCompilerV1

class FullPythonEventCompilationExample(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_full_event_example(self):
        output = StringIO()
        def _printHeader(header):
            print("=" * (len(header) + 4), file=output)
            print("= " + header + " =", file=output)
            print("=" * (len(header) + 4), file=output)
        def _printMinorDivider():
            print('~' * 10, file=output)
        def _printScriptWithSentinel(parsed: EventCommandTokens):
            s = ""
            s += 'source=%s\n' % parsed.source
            s += 'start_idx=%d\n' % parsed.start_idx
            for tok, idx in zip(parsed.tokens, parsed.token_idx):
                s += '\ttoken=\'%s\' at idx=\'%d\'\n' % (tok, idx)
            print(s, file=output)

        # This test will illustrate the full compilation pipeline

        # First we have a user-provided script. This forms the input one may expect from an event.
        # You can view the source by following the below path.
        script_path = Path(__file__).parent / 'data' / 'compilation_example.pyevent'
        script_source = script_path.read_text()
        _printHeader("Source File")
        print(script_source, file=output)


        # ===================
        # = SWS Compilation =
        # ===================
        # We convert the script above to a ScriptWithSentinel object.
        # A ScriptWithSentinel is a copy of the original script
        # with all special lines removed. "Special Lines" in this
        # case indicate lines that are written in our own Event Language.
        # These special lines are replaced with a sentinel value.
        # Meanwhile, these special lines are parsed into a struct
        # that contains each line broken into tokens.
        sws = SWSCompilerV1(script_source).compile_sws()
        _printHeader("SWS Compiled Source")
        print(sws.source, file=output)
        _printHeader("Parsed token information")
        for parsed in sws.commands:
            _printScriptWithSentinel(parsed)
            _printMinorDivider()

        # ============
        # = Analysis =
        # ============
        # Now that we have the SWS representation of a script, it becomes very simple
        # to do any number of analyses and substitutions on the script.
        # The next step is just that: we will analyze the script for any common failures.
        # For example, if the script doesn't have a correct python version tag at the top,
        # or if the script contains forbidden symbols.
        #
        # In order to run this analysis, we compile a *simplified* version of the final script.
        # The reason for this is because the final script contains a lot of boilerplate
        # that we don't need while we're doing an initial static analysis.
        script_analyze = AnalyzerPostComp.postcomp(sws)
        _printHeader("Static Analyzer Code")
        print(script_analyze, file=output)

        # The analysis cannot be represented very gracefully in text form, so I'll write a summary:
        # The Static Analyzer Source above is (should be) valid python. Therefore, we can parse it
        # as an AST and check that for all issues. Given the code is the documentation, you
        # should look at `analyzer.py` for what issues these are. A brief list includes:
        # - all Event Commands should correspond to existing event commands.
        # - each line only contains a single event command.
        # - you cannot save inside a for loop (because iterator state cannot be persisted through save data).
        # The list goes on.

        # =====================
        # = (Post)Compilation =
        # =====================
        # Because we have the SWS representation of a script,
        # We can now create the actual python code that we will exec() to form a runnable event script.
        # N.B. This is called "post-compilation" - a poor choice of name, since it is itself a second round of compilation.
        # The key concept of postcompilation - indeed, of Python Eventing - is generators.
        # The existing Event Engine is like a generator: it parses a line of Event Script, turns it into an object,
        # executes some code based on that object, and then parses the next line.
        # Therefore, it's only natural that for Python Eventing, the script itself
        # should be turned into a generator that produces Event Commands.
        #
        # The product of postcompilation is therefore wrapping the user-provided script in a generator
        # and `yield`-ing all Event Functions that are included in the script.
        # There are a number of additional things that post-compilation does that, while appearing complex, are quite simple.
        # Almost all of these - the DO_NOT_EXECUTE_SENTINELs, the _PTRs, the RESUME_CHECKs - have to do with
        # restoring after a load. (Since we saved in the middle of an event, we necessarily have to skip all event calls
        # until the save call).
        postcomp_script = PostComp.postcompile(sws)
        _printHeader("Final Compilation Output")
        print(postcomp_script, file=output)

        output_path = Path(__file__).parent / 'data' / 'compilation_docs.txt'
        self.assertEqual(output.getvalue(), output_path.read_text())

        # uncomment the following to see the above printed live
        # print(output.getvalue())

if __name__ == '__main__':
      unittest.main()