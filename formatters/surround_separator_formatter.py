from typing import List
import re
from .separator_formatter import SeparatorFormatter

class SurroundSeparatorFormatter(SeparatorFormatter):

    def __init__(self, name:str, separator = " ", start_separator = "", end_separator = ""):
        super().__init__(name, separator)
        self.start_separator = start_separator
        self.end_separator = end_separator
    
    # Transform words into the given format
    def words_to_format(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        append_character = ""
        if previous == "" and self.start_separator:
            append_character = self.start_separator
        elif previous != "" and previous[-1].isalpha() and len(words) > 0 and words[0][0].isalpha():
            append_character = self.start_separator if self.start_separator else self.separator

        formatted = super().words_to_format(words)

        # Add a character to the first word if it was the first one
        if append_character:
            if previous != "" and previous[-1].isalpha():
                formatted.insert(0, append_character)
            else:
                formatted[0] = append_character + formatted[0]

        if not formatted[-1].endswith(self.end_separator) and formatted[-1][-1].isalpha():
            formatted[-1] = formatted[-1] + self.end_separator

        return formatted
    
    def split(self, text: str, with_separator: bool = False) -> List[str]:

        # Remove starting and ending separators
        has_starting_separator = len(text) > 0 and self.start_separator != "" and self.start_separator == text[0]
        has_ending_separator = len(text) > 0 and self.end_separator != "" and self.end_separator == text[-1]
        text = text[1:] if has_starting_separator else text
        text = text[:-1] if has_ending_separator else text

        words = super().split(text, with_separator)

        # Add the separators back if need be
        if with_separator:
            if has_starting_separator:
                words[0] = self.start_separator + words[0]
            if has_ending_separator:
                words[-1] = words[-1] + self.end_separator

        return words
    
    def split_format(self, text: str) -> List[str]:
        return self.split(text, True)