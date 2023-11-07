from typing import List
import re
from .text_formatter import TextFormatter

class SeparatorFormatter(TextFormatter):

    def __init__(self, name:str, separator = " "):
        super().__init__(name)
        self.separator = separator

    # Transform formatted text into separate words
    def format_to_words(self, text: str) -> List[str]:
        separated_words = [word for word in text.split(self.separator) if word] if self.separator else [text]
        total_words = []
        for separated_word in separated_words:
            if separated_word.isalnum():
                total_words.append(separated_word)
            else:
                # Split non-alphanumeric characters in separate buckets
                new_word = ""
                new_words = []
                for char in separated_word:
                    if char.isalnum():
                        new_word += char
                    else:
                        if new_word:
                            new_words.append(new_word)
                            new_word = ""
                        new_words.append(char)
                if new_word:
                    new_words.append(new_word)
                
                total_words.extend(new_words)

        return total_words
    
    # Transform words into the given format
    def words_to_format(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        append_character = ""
        if not (previous == "" or previous.endswith(self.separator) or not previous[-1].isalnum()):
            if len(words) == 0 or words[0][0].isalpha():
                append_character = self.separator

        # Add a character to the last word if it was the final one
        formatted = []
        if append_character:
            formatted.append(append_character)

        # Otherwise, just append the words with the separators together
        for index, word in enumerate(words):
            if index < len(words) - 1:
                formatted.append(word + self.separator)
            else:
                formatted.append(word)

        # Add the separator if the next, connected word does not have a separator
        if next and next[0].isalnum():
            formatted[-1] = formatted[-1] + self.separator

        return formatted