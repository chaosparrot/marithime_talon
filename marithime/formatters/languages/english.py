from typing import List
import re
from ..sentence_formatter import SentenceFormatter
from .language import Language
from ...converters.english_I import IConverter
from ...converters.english_commas import EnglishCommaPrependingConverter, EnglishCommaAppendingConverter
from ...converters.english_days import DayConverter
from ...converters.english_months import MonthConverter
from ...converters.english_punctuation import PunctuationConverter
from ...converters.text_converter import TextConverter

class EnglishLanguage(Language):
    sentence_formatter = SentenceFormatter("sentence")

    converters: List[TextConverter] = [
        PunctuationConverter(),
        IConverter(),
        DayConverter(),
        MonthConverter(),
        EnglishCommaPrependingConverter(),
        EnglishCommaAppendingConverter(),
    ]

    def format_to_words(self, text: str) -> List[str]:
        return self.split(text)

    def dictation_format(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        converted_words = words
        for converter in self.converters:
            if converter.match_words(converted_words, previous, next):
                converted_words = converter.convert_words(converted_words, previous, next)

        return self.sentence_formatter.words_to_format([word for word in converted_words], previous, next)

    def determine_correction_keys(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        return self.sentence_formatter.determine_correction_keys(words, previous, next)

    def split(self, text: str, lossless = False) -> List[str]:
        sentence_separated_words = self.sentence_formatter.split(text, lossless)
        total_words = []
        for separated_word in sentence_separated_words:
            if separated_word.isalnum():
                total_words.append(separated_word)
            else:
                # Split non-alphanumeric characters in separate buckets
                new_word = ""
                new_words = []
                for char in separated_word:
                    if char.isalnum() or char in ("'", "-"):
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

    def split_format(self, text: str) -> List[str]:
        return self.split(text, True)

englishLanguage = EnglishLanguage()