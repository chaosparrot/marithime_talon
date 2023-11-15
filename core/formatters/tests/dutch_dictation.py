from ..dictation_formatter import DICTATION_FORMATTERS
from ...utils.test import create_test_suite

def test_dutch_dictation(assertion):
    formatter = DICTATION_FORMATTERS['NL']
    assertion( "    should capitalize the first letter of a sentence", formatter.words_to_format(["dit"]) == ["Dit"])
    assertion( "    should capitalize the first letter of a sentence and add proper spacing", formatter.words_to_format(["dit", "is", "een", "test"]) == ["Dit ", "is ", "een ", "test"])
    assertion( "    should capitalize the first letter if it was preceded by dots", formatter.words_to_format(["dit"], "test. ") == ["Dit"])
    assertion( "    should capitalize the first letter if it was preceded by exclamation marks", formatter.words_to_format(["dit"], "test! ") == ["Dit"])
    assertion( "    should capitalize the first letter if it was preceded by question marks", formatter.words_to_format(["dit"], "test? ") == ["Dit"])
    assertion( "    should capitalize the first letter if it was preceded by question marks, and add a space if it was missing", formatter.words_to_format(["dit"], "test?") == [" ", "Dit"])
    assertion( "    should not capitalize the first letter if it was preceded by commas", formatter.words_to_format(["waarvan"], "test, ") == ["waarvan"])
    assertion( "    should not capitalize the first letter if it was preceded by a word", formatter.words_to_format(["die"], "test ") == ["die"])
    assertion( "    should not capitalize the first letter if it was preceded by a number", formatter.words_to_format(["punten"], "1123 ") == ["punten"])
    assertion( "    should add a separate space if the word preceding it had no space", formatter.words_to_format(["is"], "Dit") == [" ", "is"])
    assertion( "    should add a separate space if the word preceding it had no space and keep all words lowercase", formatter.words_to_format(["had", "een", "probleem"], "Dit") == [" ", "had ", "een ", "probleem"])
    assertion( "    should not add a space if we are adding punctuation", formatter.words_to_format(["."], "thing") == ["."])

suite = create_test_suite("Dutch dictation")
suite.add_test(test_dutch_dictation)