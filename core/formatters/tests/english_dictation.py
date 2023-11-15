from ..dictation_formatter import DICTATION_FORMATTERS
from ...utils.test import create_test_suite

def test_english_dictation(assertion):
    formatter = DICTATION_FORMATTERS['EN']
    assertion( "English dictation" )
    assertion( "    should capitalize the first letter of a sentence", formatter.words_to_format(["this"]) == ["This"])
    assertion( "    should capitalize the first letter of a sentence and add proper spacing", formatter.words_to_format(["this", "is", "a", "test"]) == ["This ", "is ", "a ", "test"])
    assertion( "    should capitalize the first letter if it was preceded by dots", formatter.words_to_format(["this"], "testing. ") == ["This"])
    assertion( "    should capitalize the first letter if it was preceded by exclamation marks", formatter.words_to_format(["this"], "testing! ") == ["This"])
    assertion( "    should capitalize the first letter if it was preceded by question marks", formatter.words_to_format(["this"], "testing? ") == ["This"])
    assertion( "    should capitalize the first letter if it was preceded by question marks, and add a space if it was missing", formatter.words_to_format(["this"], "testing?") == [" ", "This"])
    assertion( "    should not capitalize the first letter if it was preceded by commas", formatter.words_to_format(["this"], "testing, ") == ["this"])
    assertion( "    should not capitalize the first letter if it was preceded by a word", formatter.words_to_format(["this"], "testing ") == ["this"])
    assertion( "    should not capitalize the first letter if it was preceded by a number", formatter.words_to_format(["this"], "1123 ") == ["this"])
    assertion( "    should add a separate space if the word preceding it had no space", formatter.words_to_format(["this"], "Testing") == [" ", "this"])
    assertion( "    should add a separate space if the word preceding it had no space and keep all words lowercase", formatter.words_to_format(["this", "could", "have"], "Testing") == [" ", "this ", "could ", "have"])
    assertion( "    should not add a space if we are adding punctuation", formatter.words_to_format(["."], "thing") == ["."])

suite = create_test_suite("English dictation")
suite.add_test(test_english_dictation)