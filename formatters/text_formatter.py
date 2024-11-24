from typing import List

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

    # Determine whether or not we need to type correction keys ( backspaces etc. ) when inserting this text
    def determine_correction_keys(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        return []