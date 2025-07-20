from .capitalization_formatter import CapitalizationFormatter, CAPITALIZATION_STRATEGY_TITLECASE, CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_ALL_CAPS
from .separator_formatter import SeparatorFormatter
from .surround_separator_formatter import SurroundSeparatorFormatter
from .dictation_formatter import DICTATION_FORMATTERS

FORMATTERS_LIST = {
    'SNAKE_CASE': CapitalizationFormatter("snakecase", "_", CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_LOWERCASE),
    'PASCAL_CASE': CapitalizationFormatter("pascalcase", "", CAPITALIZATION_STRATEGY_TITLECASE, CAPITALIZATION_STRATEGY_TITLECASE),
    'CAMEL_CASE': CapitalizationFormatter("camelcase", "", CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_TITLECASE),
    'KEBAB_CASE': SeparatorFormatter("kebabcase", "-"),
    'CONSTANT': CapitalizationFormatter("constant", "_", CAPITALIZATION_STRATEGY_ALL_CAPS, CAPITALIZATION_STRATEGY_ALL_CAPS),
    'NOOP': SeparatorFormatter("", " "),
    'NO_SPACES': CapitalizationFormatter("nospaces", " ", "", ""),
    'DOUBLE_UNDERSCORE': SeparatorFormatter("double_underscore", "__"),
    'DOUBLE_QUOTED_STRING': SurroundSeparatorFormatter("double_quoted_string", " ", '"', '"'),
    'DOUBLE_UNDERSCORE': SurroundSeparatorFormatter("double_underscore", "__", "__", "__"),
    'COMMA_SEPARATED': SeparatorFormatter("comma_separated", ','),
    'DOT_SEPARATED': SeparatorFormatter("dot_separated", '.'),
    'ALL_CAPS': CapitalizationFormatter("all_caps", " ", CAPITALIZATION_STRATEGY_ALL_CAPS, CAPITALIZATION_STRATEGY_ALL_CAPS),
    'ALL_LOWERCASE': CapitalizationFormatter("all_lowercase", " ", CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_LOWERCASE),
    'TITLE': CapitalizationFormatter("title", " ", CAPITALIZATION_STRATEGY_TITLECASE, CAPITALIZATION_STRATEGY_TITLECASE),    
    'ALL_SLASHES': SurroundSeparatorFormatter("double_underscore", "/", "/", "/"),
    'SLASH_SEPARATED': SeparatorFormatter("slash_separated", "/"),
    'DOUBLE_COLON_SEPARATED': SeparatorFormatter("double_colon_separated", "::"),
    'COMBINED_WORDS': SeparatorFormatter("combined_words", ""),
    'SINGLE_QUOTED_STRING': SurroundSeparatorFormatter("single_quoted_string", " ", "'", "'"),
    'SPACE_AFTER_WORD': SurroundSeparatorFormatter("space_after_word", " ", "", " "),
    'CAPITALIZE_FIRST_WORD': CapitalizationFormatter("capitalize_first_word", " ", CAPITALIZATION_STRATEGY_TITLECASE, CAPITALIZATION_STRATEGY_LOWERCASE),
    'CAPITALIZE_FIRST_WORD_TRAILING_SPACE': CapitalizationFormatter("capitalize_first_word", " ", CAPITALIZATION_STRATEGY_TITLECASE, CAPITALIZATION_STRATEGY_LOWERCASE, "", " "),
}

for dictation_key in DICTATION_FORMATTERS:
    FORMATTERS_LIST["DICTATION_" + dictation_key] = DICTATION_FORMATTERS[dictation_key]