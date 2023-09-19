from ..dictation_formatter import DICTATION_FORMATTERS

formatter = DICTATION_FORMATTERS['EN']
print( "English dictation" )
print( "    should capitalize the first letter of a sentence", formatter.words_to_format(["this"]) == ["This"])
print( "    should capitalize the first letter of a sentence and add proper spacing", formatter.words_to_format(["this", "is", "a", "test"]) == ["This ", "is ", "a ", "test"])
print( "    should capitalize the first letter if it was preceded by dots", formatter.words_to_format(["this"], "testing. ") == ["This"])
print( "    should capitalize the first letter if it was preceded by exclamation marks", formatter.words_to_format(["this"], "testing! ") == ["This"])
print( "    should capitalize the first letter if it was preceded by question marks", formatter.words_to_format(["this"], "testing? ") == ["This"])
print( "    should capitalize the first letter if it was preceded by question marks, and add a space if it was missing", formatter.words_to_format(["this"], "testing?") == [" ", "This"])
print( "    should not capitalize the first letter if it was preceded by commas", formatter.words_to_format(["this"], "testing, ") == ["this"])
print( "    should not capitalize the first letter if it was preceded by a word", formatter.words_to_format(["this"], "testing ") == ["this"])
print( "    should not capitalize the first letter if it was preceded by a number", formatter.words_to_format(["this"], "1123 ") == ["this"])
print( "    should add a separate space if the word preceding it had no space", formatter.words_to_format(["this"], "Testing") == [" ", "this"])
print( "    should add a separate space if the word preceding it had no space and keep all words lowercase", formatter.words_to_format(["this", "could", "have"], "Testing") == [" ", "this ", "could ", "have"])
print( "    should not add a space if we are adding punctuation", formatter.words_to_format(["."], "thing") == ["."])