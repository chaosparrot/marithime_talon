from .capitalization_formatter import CapitalizationFormatter, CAPITALIZATION_STRATEGY_TITLECASE, CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_ALL_CAPS
from .separator_formatter import SeparatorFormatter
from .dictation_formatter import DICTATION_FORMATTERS

FORMATTERS_LIST = {
    'SNAKE_CASE': CapitalizationFormatter("snakecase", "_"),
    'PASCAL_CASE': CapitalizationFormatter("pascalcase", "", CAPITALIZATION_STRATEGY_TITLECASE, CAPITALIZATION_STRATEGY_TITLECASE),
    'CAMEL_CASE': CapitalizationFormatter("camelcase", "", CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_TITLECASE),
    'KEBAB_CASE': CapitalizationFormatter("kebabcase", "-"),
    'CONSTANT': CapitalizationFormatter("constant", "_", CAPITALIZATION_STRATEGY_ALL_CAPS, CAPITALIZATION_STRATEGY_ALL_CAPS),
    'NOOP': CapitalizationFormatter("", " ", "", ""),
    'NO_SPACES': CapitalizationFormatter("nospaces", " ", "", ""),
    'DOUBLE_UNDERSCORE': CapitalizationFormatter("double_underscore", "__"),
    'DOUBLE_QUOTED_STRING': CapitalizationFormatter("double_quoted_string", '"'),
    'COMMA_SEPARATED': CapitalizationFormatter("comma_separated", ','),
    'DOT_SEPARATED': CapitalizationFormatter("dot_separated", '.'),
    'ALL_CAPS': CapitalizationFormatter("all_caps", " ", CAPITALIZATION_STRATEGY_ALL_CAPS, CAPITALIZATION_STRATEGY_ALL_CAPS),
    'ALL_LOWERCASE': CapitalizationFormatter("all_lowercase", " ", CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_LOWERCASE),
    'TITLE': CapitalizationFormatter("title", " ", CAPITALIZATION_STRATEGY_TITLECASE, CAPITALIZATION_STRATEGY_TITLECASE),    
    'SLASH_SEPARATED': CapitalizationFormatter("slash_separated", "/"),
    'DOUBLE_COLON_SEPARATED': CapitalizationFormatter("double_colon_separated", "::"),
    'COMBINED_WORDS': CapitalizationFormatter("combined_words", ""),
    'CAPITALIZE_FIRST_WORD': CapitalizationFormatter("capitalize_first_word", " ", CAPITALIZATION_STRATEGY_TITLECASE, CAPITALIZATION_STRATEGY_LOWERCASE),

}

for dictation_key in DICTATION_FORMATTERS:
    FORMATTERS_LIST["DICTATION_" + dictation_key] = DICTATION_FORMATTERS[dictation_key]