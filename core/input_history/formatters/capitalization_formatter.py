from typing import List
from .separator_formatter import SeparatorFormatter
import re

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
        separated_words = super().format_to_words(text)
        unformatted_words = []
        previous_word = ""
        for index, word in enumerate(separated_words):
            split_out_words = []
            if index > 0:
                previous_word = separated_words[index - 1]
            
            if previous_word == "":
                is_first_word = True
            else:
                is_first_word = not previous_word[-1].isalnum()

            current_word = ""
            for index, char in enumerate(word):
                if char.isalpha():
                    alpha_current_word = re.sub('\d', '', re.sub('[^\w]', '', current_word))
                    previous_char = "" if alpha_current_word == "" else alpha_current_word[-1]
                    changing_casing = char.islower() != previous_char.islower() and previous_char != ""

                    # Title case - Just continue
                    start_of_title_case = changing_casing and char.islower() and previous_char.isupper() and len(current_word) == 1
                    if changing_casing and not start_of_title_case:
                        strategy = self.first_word if is_first_word and (self.separator != "" or len(split_out_words) == 0) else self.after_first
                        if current_word != "":
                            if self.matches_strategy(current_word, strategy):
                                split_out_words.append(current_word.lower())
                                current_word = ""
                            else:
                                split_out_words.append(current_word)
                                current_word = ""
                current_word += char

            # Add remnants left over by the loop
            if current_word:
                strategy = self.first_word if is_first_word and (self.separator != "" or len(split_out_words) == 0) else self.after_first
                if self.matches_strategy(current_word, strategy):
                    split_out_words.append(current_word.lower())                        
                else:
                    split_out_words.append(current_word)
            
            unformatted_words.extend(split_out_words)
                
        return unformatted_words
    
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
        is_first_word = previous == "" or not (previous.endswith(self.separator) or previous[-1].isalnum())
        if not is_first_word:
            if not self.separator:
                is_first_word = not (self.matches_strategy(previous, self.first_word) and previous[-1].isalnum())
            else:
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