from typing import List
import re

# Class that is used to transform the content of text to another text
class TextConverter:

    def match_words(self, words: List[str], previous: str = "", next: str = "") -> bool:
        matches = False
        for index, word in enumerate(words):
            previous_word = words[index - 1] if index > 0 else "" if previous == "" else previous.strip().split()[-1]
            next_word = words[index + 1] if index + 1 < len(words) else "" if next == "" else next.strip().split()[0]
            if self.match_text(word, previous_word, next_word):
                matches = True
                break

        return matches

    def convert_words(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        converted_words = []
        for index, word in enumerate(words):
            previous_word = words[index - 1] if index > 0 else "" if previous == "" else previous.strip().split()[-1]
            next_word = words[index + 1] if index + 1 < len(words) else "" if next == "" else next.strip().split()[0]
            if self.match_text(word, previous_word, next_word):
                converted_words.append(self.convert_text(word, previous_word, next_word))
            else:
                converted_words.append(word)

        return converted_words

    def match_text(self, text: str, previous: str = "", next: str = "") -> bool:
        return False
    
    def convert_text(self, text: str) -> str:
        return text