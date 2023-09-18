from typing import List
from .text_formatter import TextFormatter

class SeparatorFormatter(TextFormatter):

    def __init__(self, name:str, separator = " "):
        super().__init__(name)
        self.separator = separator

    # Transform formatted text into separate words
    def format_to_words(self, text: str) -> List[str]:
        return [word for word in text.split(self.separator) if word]
    
    # Transform words into the given format
    def words_to_format(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        append_character = ""
        if not (previous == "" or previous.endswith(self.separator) or not previous[-1].isalnum()):
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