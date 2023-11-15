from ..separator_formatter import SeparatorFormatter
from ..capitalization_formatter import CapitalizationFormatter, CAPITALIZATION_STRATEGY_ALL_CAPS, CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_TITLECASE
from ...utils.test import create_test_suite

def test_dot_separator(assertion):
    dot_separator = SeparatorFormatter("dots", ".")
    assertion( "Separator formatters" )
    assertion( "    should separate words by the separator 'THIS.is.A'", dot_separator.format_to_words('THIS.is.A') == ["THIS", "is", "A"])
    assertion( "    should have a single word if there is no separator", dot_separator.format_to_words('THIS') == ["THIS"])
    assertion( "    should have a non-alphanumerical separators if a character is not a separator", dot_separator.format_to_words('this_is(a test') == ["this", "_", "is", "(", "a", " ", "test"])
    assertion( "    should keep digits as well", dot_separator.format_to_words('this101.is.a') == ["this101", "is", "a"])

def test_large_separator_formatter(assertion):
    large_separator = SeparatorFormatter("large", "-=-")
    assertion( "Multiple character separator formatters" )
    assertion( "    should separate words by the separator 'THIS-=-is-=-A'", large_separator.format_to_words('THIS-=-is-=-A') == ["THIS", "is", "A"])
    assertion( "    should have a single word if there is no separator", large_separator.format_to_words('THIS') == ["THIS"])
    assertion( "    should have a non-alphanumerical separators if a character is not a separator", large_separator.format_to_words('this_is(a test') == ["this", "_", "is", "(", "a", " ", "test"])
    assertion( "    should keep digits as well", large_separator.format_to_words('this101-=-is-=-a') == ["this101", "is", "a"])

def test_lowercase_formatter(assertion):
    lowercase_formatter = CapitalizationFormatter("lower", "_")
    assertion( "Lower case formatter with separators" )
    assertion( "    should keep lower case words the same", lowercase_formatter.format_to_words("this_is_a") == ["this", "is", "a"])
    assertion( "    should keep other capitalization the same'", lowercase_formatter.format_to_words('THIS_is_A') == ["THIS", "is", "A"])
    assertion( "    should have a single word if there is no separator", lowercase_formatter.format_to_words('this') == ["this"])
    assertion( "    should have a non-alphanumerical separators if a character is not a separator", lowercase_formatter.format_to_words('this_is(a test') == ["this", "is", "(", "a", " ", "test"])
    assertion( "    should keep digits as well", lowercase_formatter.format_to_words('this101_is_a') == ["this101", "is", "a"])

def test_uppercase_formatter(assertion):
    uppercase_formatter = CapitalizationFormatter("upper", "_", CAPITALIZATION_STRATEGY_ALL_CAPS, CAPITALIZATION_STRATEGY_ALL_CAPS)
    assertion( "Lower case formatter with separators" )
    assertion( "    should change uppercase words to lowercase", uppercase_formatter.format_to_words("THIS_is_a") == ["this", "is", "a"])
    assertion( "    should keep other capitalization the same'", uppercase_formatter.format_to_words('THIS_is_A') == ["this", "is", "a"])
    assertion( "    should have a single word if there is no separator", uppercase_formatter.format_to_words('THIS') == ["this"])
    assertion( "    should have a non-alphanumerical separators if a character is not a separator", uppercase_formatter.format_to_words('THIS_IS(a test') == ["this", "is", "(", "a", " ", "test"])
    assertion( "    should keep digits as well", uppercase_formatter.format_to_words('THIS101_is_a') == ["this101", "is", "a"])

def test_titlecase_formatters(assertion):
    titlecase_formatters = CapitalizationFormatter("title", "_", CAPITALIZATION_STRATEGY_TITLECASE, CAPITALIZATION_STRATEGY_TITLECASE)
    assertion( "Title case formatter with separators" )
    assertion( "    should change titlecase words to lowercase", titlecase_formatters.format_to_words("THIS_Is_A") == ["THIS", "is", "a"])
    assertion( "    should keep other capitalization the same'", titlecase_formatters.format_to_words('This_IS_A') == ["this", "IS", "a"])
    assertion( "    should have a single word if there is no separator", titlecase_formatters.format_to_words('This') == ["this"])
    assertion( "    should have a non-alphanumerical separators if a character is not a separator", titlecase_formatters.format_to_words('This_Is(a test') == ["this", "is", "(", "a", " ", "test"])
    assertion( "    should keep digits as well", titlecase_formatters.format_to_words('This101_is_a') == ["this101", "is", "a"])

def test_mixed_case_formatters(assertion):
    mixed_case_formatting = CapitalizationFormatter("title", "_", CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_TITLECASE)
    assertion( "Mixed case formatting with separators" )
    assertion( "    should change after first titlecase words to lowercase", mixed_case_formatting.format_to_words("this_Thing_Is_Amazing") == ["this", "thing", "is", "amazing"])
    assertion( "    should change after first titlecase words to lowercase", mixed_case_formatting.format_to_words("This_Thing_Is_AMAZING") == ["This", "thing", "is", "AMAZING"])
    assertion( "    should have a single word if there is no separator", mixed_case_formatting.format_to_words('This') == ["This"])
    assertion( "    should have a non-alphanumerical separators if a character is not a separator", mixed_case_formatting.format_to_words('this_Is(a test') == ["this", "is", "(", "a", " ", "test"])
    assertion( "    should keep digits as well", mixed_case_formatting.format_to_words('this101_Is101_a') == ["this101", "is101", "a"])
    assertion( mixed_case_formatting.format_to_words("this_Thing_Is_Amazing") )

def test_capitalization_formatter(assertion):
    mixed_case_formatting = CapitalizationFormatter("title", "", CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_TITLECASE)
    assertion( "Mixed case formatting without separators" )
    assertion( "    should nicely split off capitalized words", mixed_case_formatting.format_to_words("thisThingIsAmazing") == ["this", "thing", "is", "amazing"])
    assertion( "    should change after first titlecase words to lowercase", mixed_case_formatting.format_to_words("ThisThingIsAMAZING") == ["This", "thing", "is", "AMAZING"])
    assertion( "    should have a single word if there is no separator", mixed_case_formatting.format_to_words('This') == ["This"])
    assertion( "    should have a non-alphanumerical separators if a character is not a separator", mixed_case_formatting.format_to_words('thisIs(a test') == ["this", "is", "(", "a", " ", "test"])
    assertion( "    should keep digits as well", mixed_case_formatting.format_to_words('this101Is101_a') == ["this101", "is101", "_", "a"])

suite = create_test_suite("Reverse formatters")
suite.add_test(test_dot_separator)
suite.add_test(test_large_separator_formatter)
suite.add_test(test_lowercase_formatter)
suite.add_test(test_uppercase_formatter)
suite.add_test(test_titlecase_formatters)
suite.add_test(test_mixed_case_formatters)
suite.add_test(test_capitalization_formatter)