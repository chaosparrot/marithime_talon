from typing import List
from ..sentence_formatter import SentenceFormatter
from .language import Language

class EnglishLanguage(Language):
    sentence_formatter = SentenceFormatter("sentence")

    digits = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    increments = ["teen", "hundred", "thousand", "million", "billion"]

    def dictation_format(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        return self.sentence_formatter.words_to_format(words, previous, next)

englishLanguage = EnglishLanguage()