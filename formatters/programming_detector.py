
import re
from .formatters import FORMATTERS_LIST
from .text_formatter import TextFormatter

remove_letters_regex = re.compile('[^a-zA-Z]')
class ProgrammingFormatterDetector:

    def detect(self, text: str, previous_token: str = "", next_token: str = "") -> TextFormatter:

        # Empty string apart from numbers and non-ascii letters - Indeterminate
        if remove_letters_regex.sub('', text) == "":
            return None

        # All upper case formatters
        if text.isupper():
            if self.can_split_on_separator(text, "_"):
                return FORMATTERS_LIST["CONSTANT"]
            else:
                return FORMATTERS_LIST["ALL_CAPS"]

        # All lower case formatters
        elif text.islower():
            if self.can_split_on_separator(text, "_"):
                return FORMATTERS_LIST["SNAKE_CASE"]
            elif self.can_split_on_separator(text, "-"):
                return FORMATTERS_LIST["KEBAB_CASE"]
        # Mixed casing
        else:
            split_text = re.sub('([A-Z][a-z]+)', r' \1', re.sub('([A-Z]+)', r' \1', text)).split()
            if len(split_text) > 1:
                if split_text[0][0].islower():
                    return FORMATTERS_LIST["CAMEL_CASE"]
                elif split_text[0][0].isupper():
                    return FORMATTERS_LIST["PASCAL_CASE"]
            elif len(split_text) == 1 and split_text[0][0].isupper():
                return FORMATTERS_LIST["TITLE"]

        # Undetermined format
        return None
    
    def can_split_on_separator(self, text: str, separator: str) -> bool:
        return separator in text and '' not in text.split(separator)
