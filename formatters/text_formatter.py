from typing import List
import re

def normalize_text(text: str) -> str:
    return re.sub(r"[^\w\s]|[_]", ' ', text).replace("\n", " ")

class TextFormatter:
    name: str

    def __init__(self, name: str):
        self.name = name

    # Transform formatted text into separate words
    def format_to_words(self, text: str) -> List[str]:
        return [text]
    
    # Transform words into the given format
    def words_to_format(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        return words
    
    # Split the text up into tokens known by the formatter without losing characters
    def split_format(self, text: str) -> List[str]:
        return self.words_to_format(self.format_to_words(text))
    
    # Detect if we can merge this text together into a single token
    def can_merge_text(self, first_text: str, last_text: str) -> bool:
        normalized_first_text = normalize_text(first_text)
        normalized_last_text = normalize_text(last_text)

        return normalized_last_text == "" or \
            ( not normalized_first_text.endswith(" ") and not normalized_last_text.startswith(" ") ) or \
            first_text == "\n" or last_text == "\n"
    
    # Determine whether or not we need to type correction keys ( backspaces etc. ) when inserting this text
    def determine_correction_keys(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        return []