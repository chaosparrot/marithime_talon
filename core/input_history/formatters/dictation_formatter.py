from typing import List
from .text_formatter import TextFormatter
from .languages.english import englishLanguage
from .languages.language import Language

class DictationFormatter(TextFormatter):
    language: Language

    def __init__(self, name: str, language: Language):
        super().__init__(name)
        self.language = language

    # Transform formatted text into separate words
    def format_to_words(self, text: str) -> List[str]:
        return text.split()

    # Transform words into the given format
    def words_to_format(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        return self.language.dictation_format(words, previous, next)
    
    # Determine whether or not we need to type correction keys ( backspaces etc. ) when inserting this text
    def determine_correction_keys(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        return self.language.determine_correction_keys(words, previous, next)

DICTATION_FORMATTERS = {
    'EN': DictationFormatter('english', englishLanguage)
}