
import re
from .formatters import FORMATTERS_LIST
from .text_formatter import TextFormatter
from .programming_detector import ProgrammingFormatterDetector
from .languages.dutch import dutchLanguage
from .languages.english import englishLanguage

remove_letters_regex = re.compile('[^a-zA-Z]')
class FormatterDetector:
    programming_detector: ProgrammingFormatterDetector = None

    def __init__(self):
        self.programming_detector = ProgrammingFormatterDetector()

    def detect_formatter(self, text: str, previous_token: str = "", next_token: str = "") -> TextFormatter:
        formatter = self.programming_detector.detect(text, previous_token, next_token)

        # Disable detecting title formatter for now since it conflicts with dictation
        if formatter and formatter.name == "title":
            formatter = None

        return formatter

    def detect_language_formatter(self, text: str) -> TextFormatter:
        language = FORMATTERS_LIST['DICTATION_EN']

        english_likeliness = englishLanguage.detect_likeliness(text)
        dutch_likeliness = dutchLanguage.detect_likeliness(text)
        if english_likeliness >= 0 and english_likeliness > dutch_likeliness:
            language = FORMATTERS_LIST['DICTATION_EN']
        else:
            language = FORMATTERS_LIST['DICTATION_NL']

        return language
