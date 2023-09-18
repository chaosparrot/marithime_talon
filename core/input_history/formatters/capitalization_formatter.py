from typing import List
from .separator_formatter import SeparatorFormatter

CAPITALIZATION_STRATEGY_ALL_CAPS = 'ALLCAPS'
CAPITALIZATION_STRATEGY_LOWERCASE = 'LOWERCASE'
CAPITALIZATION_STRATEGY_TITLECASE = 'TITLE'

class CapitalizationFormatter(SeparatorFormatter):
    def __init__(self, name: str, separator = " ", first: str = CAPITALIZATION_STRATEGY_LOWERCASE, after: str = CAPITALIZATION_STRATEGY_LOWERCASE):
        super().__init__(name, separator)
        self.first_word = first
        self.after_first = after

    # Transform formatted text into separate words
    def format_to_words(self, text: str) -> List[str]:
        return [word.lower() for word in text.split(self.separator) if word]
    
    def matches_strategy(self, word: str, strategy: str) -> bool:
        if strategy == CAPITALIZATION_STRATEGY_ALL_CAPS:
            return word == word.upper()
        elif strategy == CAPITALIZATION_STRATEGY_LOWERCASE:
            return word == word.lower()
        elif strategy == CAPITALIZATION_STRATEGY_TITLECASE:
            return word == word.capitalize()
        else:
            return True

    # Transform words into the given format
    def words_to_format(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        capitalized_words = []
        is_first_word = previous == "" or (not previous.endswith(self.separator) or not previous[-1].isalnum())
        if not is_first_word:
            is_first_word = not self.matches_strategy(previous, self.first_word)

        first_strategy = self.first_word if is_first_word else self.after_first

        # Do capitalization first before doing separation connection
        for index, word in enumerate(words):
            strategy = first_strategy if index == 0 else self.after_first
            formatted_word = word
            if strategy == CAPITALIZATION_STRATEGY_LOWERCASE:
                formatted_word = formatted_word.lower()
            elif strategy == CAPITALIZATION_STRATEGY_ALL_CAPS:
                formatted_word = formatted_word.upper()
            elif strategy == CAPITALIZATION_STRATEGY_TITLECASE:
                formatted_word = formatted_word.capitalize()
            
            capitalized_words.append(formatted_word)

        return super().words_to_format(capitalized_words, previous, next)