from typing import List
from ..sentence_formatter import SentenceFormatter
from .language import Language

class EnglishLanguage(Language):
    sentence_formatter = SentenceFormatter("sentence")

    def dictation_format(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        return self.sentence_formatter.words_to_format(words, previous, next)
    
englishLanguage = EnglishLanguage()