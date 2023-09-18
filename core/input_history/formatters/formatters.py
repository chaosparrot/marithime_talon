from .capitalization_formatter import CapitalizationFormatter, CAPITALIZATION_STRATEGY_TITLECASE, CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_ALL_CAPS
from .separator_formatter import SeparatorFormatter
from .dictation_formatter import DICTATION_FORMATTERS

FORMATTERS_LIST = {
    'SNAKECASE': CapitalizationFormatter("snakecase", "_"),
    'PASCALCASE': CapitalizationFormatter("pascalcase", "", CAPITALIZATION_STRATEGY_TITLECASE, CAPITALIZATION_STRATEGY_TITLECASE),
    'CAMELCASE': CapitalizationFormatter("camelcase", "", CAPITALIZATION_STRATEGY_LOWERCASE, CAPITALIZATION_STRATEGY_TITLECASE),
    'KEBABCASE': CapitalizationFormatter("kebabcase", "-"),
    'MACROCASE': CapitalizationFormatter("macrocase", "_", CAPITALIZATION_STRATEGY_ALL_CAPS, CAPITALIZATION_STRATEGY_ALL_CAPS),
    'NOOP': CapitalizationFormatter("", " ", "", ""),
    'NO_SPACES': CapitalizationFormatter("nospaces", " ", "", "")    
}

for dictation_key in DICTATION_FORMATTERS:
    FORMATTERS_LIST["DICTATE_" + dictation_key] = DICTATION_FORMATTERS[dictation_key]