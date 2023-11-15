from typing import List
from ..sentence_formatter import SentenceFormatter
from .language import Language
from ...converters.dutch_punctuation import PunctuationConverter
from ...converters.text_converter import TextConverter

class DutchLanguage(Language):
    sentence_formatter = SentenceFormatter("sentence")

    converters: List[TextConverter] = [
        PunctuationConverter(),
    ]

    def dictation_format(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        converted_words = words
        for converter in self.converters:
            if converter.match_words(converted_words, previous, next):
                converted_words = converter.convert_words(converted_words, previous, next)

        return self.sentence_formatter.words_to_format([word for word in converted_words], previous, next)

    def determine_correction_keys(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        return self.sentence_formatter.determine_correction_keys(words, previous, next)

dutchLanguage = DutchLanguage()