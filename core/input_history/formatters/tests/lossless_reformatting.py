from ..separator_formatter import SeparatorFormatter
from ..capitalization_formatter import CapitalizationFormatter, CAPITALIZATION_STRATEGY_ALL_CAPS, CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_TITLECASE
from ....utils.test import create_test_suite

def test_transition_between_separators(assertion):
    assertion( "Reformatting from a dot separator to an underscore separator...")
    dot_separator = SeparatorFormatter("dots", ".")
    score_separator = SeparatorFormatter("underscore", "_")
    words = score_separator.words_to_format(dot_separator.format_to_words("this.is.a.test"), "", "")
    assertion( "    'this.is.a.test' should become 'this_is_a_test'", "".join(words) == "this_is_a_test")
    words = score_separator.words_to_format(dot_separator.format_to_words("this.is a.test"), "", "")
    assertion( "    'this.is a.test' should become 'this_is a_test'", "".join(words) == "this_is a_test")
    words = score_separator.words_to_format(dot_separator.format_to_words("this.123 a.test"), "", "")
    assertion( "    'this.123 a.test' should become 'this_123 a_test'", "".join(words) == "this_123 a_test")
    words = score_separator.words_to_format(dot_separator.format_to_words("this..IS..big"), "", "")
    assertion( "    'this..IS..big' should become 'this__IS__big'", "".join(words) == "this__IS__big")

    assertion( "Reformatting from an underscore separator to a dot separator...")
    dot_separator = SeparatorFormatter("dots", ".")
    score_separator = SeparatorFormatter("underscore", "_")
    words = dot_separator.words_to_format(score_separator.format_to_words("this_is_a_test"), "", "")
    assertion( "    'this_is_a_test' should become 'this.is.a.test'", "".join(words) == "this.is.a.test")
    words = dot_separator.words_to_format(score_separator.format_to_words("this_is a_test"), "", "")
    assertion( "    'this_is a_test' should become 'this.is a.test'", "".join(words) == "this.is a.test")
    words = dot_separator.words_to_format(score_separator.format_to_words("this_123 a_test"), "", "")
    assertion( "    'this_123 a_test' should become 'this.123 a.test'", "".join(words) == "this.123 a.test")
    words = dot_separator.words_to_format(score_separator.format_to_words("this__IS__big"), "", "")
    assertion( "    'this__IS__big' should become 'this..IS..big'", "".join(words) == "this..IS..big")

def test_transition_between_capitalization_separators(assertion):
    assertion( "Reformatting from a dot separator to an uppercase underscore separator...")
    dot_separator = SeparatorFormatter("dots", ".")
    score_separator = CapitalizationFormatter("underscore", "_", CAPITALIZATION_STRATEGY_ALL_CAPS, CAPITALIZATION_STRATEGY_ALL_CAPS)
    words = score_separator.words_to_format(dot_separator.format_to_words("this.is.a.test"), "", "")
    assertion( "    'this.is.a.test' should become 'THIS_IS_A_TEST'", "".join(words) == "THIS_IS_A_TEST")
    words = score_separator.words_to_format(dot_separator.format_to_words("this.is a.test"), "", "")
    assertion( "    'this.is a.test' should become 'THIS_IS A_TEST'", "".join(words) == "THIS_IS A_TEST")
    words = score_separator.words_to_format(dot_separator.format_to_words("THIS.123 A.TEST"), "", "")
    assertion( "    'this.123 a.test' should become 'THIS_123 A_TEST'", "".join(words) == "THIS_123 A_TEST")
    words = score_separator.words_to_format(dot_separator.format_to_words("this..IS..big"), "", "")
    assertion( "    'this..IS..big' should become 'THIS__IS__BIG'", "".join(words) == "THIS__IS__BIG")

    assertion( "Reformatting from an uppercase underscore separator to a dot separator...")
    words = dot_separator.words_to_format(score_separator.format_to_words("THIS_IS_A_TEST"), "", "")
    assertion( "    'THIS_IS_A_TEST' should become 'this.is.a.test'", "".join(words) == "this.is.a.test")
    words = dot_separator.words_to_format(score_separator.format_to_words("THIS_IS a_Test"), "", "")
    assertion( "    'THIS_IS a_Test' should become 'this.is a.Test'", "".join(words) == "this.is a.Test")
    words = dot_separator.words_to_format(score_separator.format_to_words("THIS_123 A_TEST"), "", "")
    assertion( "    'THIS_123 A_TEST' should become 'this.123 a.test'", "".join(words) == "this.123 a.test")
    words = dot_separator.words_to_format(score_separator.format_to_words("this__IS__big"), "", "")
    assertion( "    'this__IS__big' should become 'this..is..big'", "".join(words) == "this..is..big")
    assertion(words)

def test_transition_between_pure_capitalization_separators(assertion):
    assertion( "Reformatting from a lower to titlecase separator to a titlecase uppercase separator...")
    lower_separator = CapitalizationFormatter("lower", "", CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_TITLECASE)
    upper_separator = CapitalizationFormatter("title", "", CAPITALIZATION_STRATEGY_TITLECASE, CAPITALIZATION_STRATEGY_TITLECASE)
    words = upper_separator.words_to_format(lower_separator.format_to_words("thisIsTheTest"), "", "")
    assertion( "    'thisIsTheTest' should become 'ThisIsTheTest'", "".join(words) == "ThisIsTheTest")
    words = upper_separator.words_to_format(lower_separator.format_to_words("THIS.isTheTest"), "", "")
    assertion( "    'THIS.isTheTest' should become 'This.IsTheTest'", "".join(words) == "This.IsTheTest")
    words = upper_separator.words_to_format(lower_separator.format_to_words("THIS IS TIRING"), "", "")
    assertion( "    'THIS IS TIRING' should become 'This Is Tiring'", "".join(words) == "This Is Tiring")


suite = create_test_suite("Lossless reformatting")
suite.add_test(test_transition_between_separators)
suite.add_test(test_transition_between_capitalization_separators)
suite.add_test(test_transition_between_pure_capitalization_separators)