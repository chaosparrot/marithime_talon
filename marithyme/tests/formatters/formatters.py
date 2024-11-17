from ...formatters.separator_formatter import SeparatorFormatter
from ...formatters.capitalization_formatter import CapitalizationFormatter, CAPITALIZATION_STRATEGY_ALL_CAPS, CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_TITLECASE
from ..test import create_test_suite

def test_dot_separator(assertion):
    dot_separator = SeparatorFormatter("dots", ".")
    assertion( "Separator formatters" )
    assertion( "    should not add the separator to single words", dot_separator.words_to_format(["This"]) == ["This"])
    assertion( "    should add the separator after the first word", dot_separator.words_to_format(["This", "Thing"]) == ["This.", "Thing"])
    assertion( "    should add the separator separately if the previous word lacks it", dot_separator.words_to_format(["This", "Thing"], "After") == [".", "This.", "Thing"])
    assertion( "    should not add the separator if only one word is given", dot_separator.words_to_format(["This"], "After") == [".", "This"])
    assertion( "    should not add the separators between digits", dot_separator.words_to_format(["86"], "9") == ["86"])
    assertion( "    should not add the separators between special characters", dot_separator.words_to_format([" this", "thing"], ".") == [" this.", "thing"])

def test_large_separator_formatter(assertion):
    large_separator = SeparatorFormatter("large", "-=-")
    assertion( "Multiple character separator formatters" )
    assertion( "    should not add the separator to single words", large_separator.words_to_format(["This"]) == ["This"])
    assertion( "    should add the separator after the first word", large_separator.words_to_format(["This", "Thing"]) == ["This-=-", "Thing"])
    assertion( "    should add the separator separately if the previous word lacks it", large_separator.words_to_format(["This", "Thing"], "After") == ["-=-", "This-=-", "Thing"])
    assertion( "    should not add the separator if only one word is given", large_separator.words_to_format(["This"], "After") == ["-=-", "This"])

def test_lowercase_formatter(assertion):
    lowercase_formatter = CapitalizationFormatter("lower", " ")
    assertion( "Lower case formatter with separators" )
    assertion( "    should keep lower case words the same", lowercase_formatter.words_to_format(["this"]) == ["this"])
    assertion( "    should make capitalized words lowercase", lowercase_formatter.words_to_format(["This"]) == ["this"])
    assertion( "    should make uppercase words lowercase", lowercase_formatter.words_to_format(["THIS"]) == ["this"])
    assertion( "    should join multiple lowercase words with a separator", lowercase_formatter.words_to_format(["this", "thing"]) == ["this ", "thing"])
    assertion( "    should join multiple different cased words with a separator", lowercase_formatter.words_to_format(["this", "thing"]) == ["this ", "thing"])
    assertion( "    should add a separator to previous if they are lacking", lowercase_formatter.words_to_format(["thiS", "THing"], "after") == [" ", "this ", "thing"])
    assertion( "    should handle utf-8 characters by keeping all letters lowercase", lowercase_formatter.words_to_format(["über"]) == ["über"])
    assertion( "    should handle utf-8 characters by making all letters lowercase", lowercase_formatter.words_to_format(["Über"]) == ["über"])
    assertion( "    should handle utf-8 characters by keeping all letters lowercase", lowercase_formatter.words_to_format(["ÜBER"]) == ["über"])

def test_uppercase_formatter(assertion):
    uppercase_formatter = CapitalizationFormatter("upper", " ", CAPITALIZATION_STRATEGY_ALL_CAPS, CAPITALIZATION_STRATEGY_ALL_CAPS)
    assertion( "Upper case formatter with separators" )
    assertion( "    should keep lowercase words uppercase", uppercase_formatter.words_to_format(["this"]) == ["THIS"])
    assertion( "    should make capitalized words uppercase", uppercase_formatter.words_to_format(["This"]) == ["THIS"])
    assertion( "    should keep uppercase words the same", uppercase_formatter.words_to_format(["THIS"]) == ["THIS"])
    assertion( "    should join multiple uppercase words with a separator", uppercase_formatter.words_to_format(["THIS", "THING"]) == ["THIS ", "THING"])
    assertion( "    should join multiple different cased words with a separator", uppercase_formatter.words_to_format(["this", "THING"]) == ["THIS ", "THING"])
    assertion( "    should add a separator to previous if they are lacking", uppercase_formatter.words_to_format(["thiS", "THing"], "after") == [" ", "THIS ", "THING"])
    assertion( "    should handle utf-8 characters by making all letters uppercase", uppercase_formatter.words_to_format(["über"]) == ["ÜBER"])
    assertion( "    should handle utf-8 characters by making all letters uppercase", uppercase_formatter.words_to_format(["Über"]) == ["ÜBER"])
    assertion( "    should handle utf-8 characters by keeping all letters uppercase", uppercase_formatter.words_to_format(["ÜBER"]) == ["ÜBER"])

def test_titlecase_formatters(assertion):
    titlecase_formatters = CapitalizationFormatter("title", " ", CAPITALIZATION_STRATEGY_TITLECASE, CAPITALIZATION_STRATEGY_TITLECASE)
    assertion( "Title case formatter with separators" )
    assertion( "    should keep lower case words capitalized", titlecase_formatters.words_to_format(["this"]) == ["This"])
    assertion( "    should keep capitalized words the same", titlecase_formatters.words_to_format(["This"]) == ["This"])
    assertion( "    should make uppercase words capitalized", titlecase_formatters.words_to_format(["THIS"]) == ["This"])
    assertion( "    should join multiple lowercase words with a separator", titlecase_formatters.words_to_format(["This", "Thing"]) == ["This ", "Thing"])
    assertion( "    should join multiple different cased words with a separator", titlecase_formatters.words_to_format(["this", "THING"]) == ["This ", "Thing"])
    assertion( "    should add a separator to previous if they are lacking", titlecase_formatters.words_to_format(["thiS", "THing"], "after") == [" ", "This ", "Thing"])
    assertion( "    should handle utf-8 characters by making the first letter uppercase", titlecase_formatters.words_to_format(["über"]) == ["Über"])
    assertion( "    should handle utf-8 characters by making the first letter uppercase", titlecase_formatters.words_to_format(["ÜBER"]) == ["Über"])
    assertion( "    should handle utf-8 characters by keeping the first letter uppercase", titlecase_formatters.words_to_format(["ÜBER"]) == ["Über"])

def test_mixed_case_formatters(assertion):
    mixed_case_formatting = CapitalizationFormatter("title", "_", CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_TITLECASE)
    assertion( "Mixed case formatting with separators" )
    assertion( "    should keep the first lowercase word the same", mixed_case_formatting.words_to_format(["this"]) == ["this"])
    assertion( "    should make capitalized words lowercase", mixed_case_formatting.words_to_format(["This"]) == ["this"])
    assertion( "    should make uppercase words lowercase", mixed_case_formatting.words_to_format(["THIS"]) == ["this"])
    assertion( "    should make the next lowercase word title case", mixed_case_formatting.words_to_format(["this", "thing"]) == ["this_", "Thing"])
    assertion( "    should keep the next titlecase word title case", mixed_case_formatting.words_to_format(["this", "Thing"]) == ["this_", "Thing"])
    assertion( "    should make the next uppercase word title case", mixed_case_formatting.words_to_format(["this", "THING"]) == ["this_", "Thing"])
    assertion( "    should make the first lowercase word title case if it had a lowercase word before it", mixed_case_formatting.words_to_format(["this", "thing"], "after_") == ["This_", "Thing"])
    assertion( "    should make the first uppercase word title case if it had a lowercase word before it", mixed_case_formatting.words_to_format(["THIS", "thing"], "after_") == ["This_", "Thing"])
    assertion( "    should keep the first titlecase word title case if it had a lowercase word before it", mixed_case_formatting.words_to_format(["This", "thing"], "after_") == ["This_", "Thing"])
    assertion( "    should keep the first lowercase word if it had a non-alphanumeric character before it", mixed_case_formatting.words_to_format(["this", "thing"], "after ") == ["this_", "Thing"])
    assertion( "    should make the first lowercase word title case if it had a non-alphanumeric character before it", mixed_case_formatting.words_to_format(["this", "thing"], "after") == ["_", "This_", "Thing"])

def test_capitalization_formatter(assertion):
    mixed_case_formatting = CapitalizationFormatter("title", "", CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_TITLECASE)
    assertion( "Mixed case formatting without separators" )
    assertion( "    should keep the first lowercase word the same", mixed_case_formatting.words_to_format(["this"]) == ["this"])
    assertion( "    should make capitalized words lowercase", mixed_case_formatting.words_to_format(["This"]) == ["this"])
    assertion( "    should make uppercase words lowercase", mixed_case_formatting.words_to_format(["THIS"]) == ["this"])
    assertion( "    should make the next lowercase word title case", mixed_case_formatting.words_to_format(["this", "thing"]) == ["this", "Thing"])
    assertion( "    should keep the next titlecase word title case", mixed_case_formatting.words_to_format(["this", "Thing"]) == ["this", "Thing"])
    assertion( "    should make the next uppercase word title case", mixed_case_formatting.words_to_format(["this", "THING"]) == ["this", "Thing"])
    assertion( "    should make the first lowercase word title case if it had a lowercase word before it", mixed_case_formatting.words_to_format(["this", "thing"], "after") == ["This", "Thing"])
    assertion( "    should make the first uppercase word title case if it had a lowercase word before it", mixed_case_formatting.words_to_format(["THIS", "thing"], "after") == ["This", "Thing"])
    assertion( "    should keep the first titlecase word title case if it had a lowercase word before it", mixed_case_formatting.words_to_format(["This", "thing"], "after") == ["This", "Thing"])
    assertion( "    should keep the first lowercase word if it had a non-alphanumeric character before it", mixed_case_formatting.words_to_format(["this", "thing"], "after ") == ["this", "Thing"])

suite = create_test_suite("Text formatters")
suite.add_test(test_dot_separator)
suite.add_test(test_large_separator_formatter)
suite.add_test(test_lowercase_formatter)
suite.add_test(test_uppercase_formatter)
suite.add_test(test_titlecase_formatters)
suite.add_test(test_mixed_case_formatters)
suite.add_test(test_capitalization_formatter)