from typing import List
from ..sentence_formatter import SentenceFormatter
from .language import Language
from ...converters.english_I import IConverter

class EnglishLanguage(Language):
    sentence_formatter = SentenceFormatter("sentence")

    converters = [
        IConverter()
    ]

    def dictation_format(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        new_words = []
        for index, word in enumerate(words):
            previous_word = previous if index == 0 else words[index - 1]
            next_word = next if index == len(words) - 1 else words[index + 1]

            converted_word = word.lower()
            for converter in self.converters:
                if converter.match_text(word, previous_word, next_word):
                    converted_word = converter.convert(word)
            new_words.append(converted_word)

        return self.sentence_formatter.words_to_format([word for word in new_words], previous, next)

englishLanguage = EnglishLanguage()