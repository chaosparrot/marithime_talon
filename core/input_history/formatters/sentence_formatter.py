from typing import List
from .text_formatter import TextFormatter
import re

no_space_after = re.compile(r"""
  (?:
    [\s\-_/#@([{‘“]     # characters that never need space after them
  | (?<!\w)[$£€¥₩₽₹]    # currency symbols not preceded by a word character
  # quotes preceded by beginning of string, space, opening braces, dash, or other quotes
  | (?: ^ | [\s([{\-'"] ) ['"]
  )$""", re.VERBOSE)
no_space_before = re.compile(r"""
  ^(?:
    [\s\-_.,!?;:/%)\]}’”]   # characters that never need space before them
  | [$£€¥₩₽₹](?!\w)         # currency symbols not followed by a word character
  # quotes followed by end of string, space, closing braces, dash, other quotes, or some punctuation.
  | ['"] (?: $ | [\s)\]}\-'".,!?;:/] )
  )""", re.VERBOSE)

def omit_space_before(text: str) -> bool:
    return not text or no_space_before.search(text) is not None

def omit_space_after(text: str) -> bool:
    return not text or no_space_after.search(text) is not None

def needs_space_between(before: str, after: str) -> bool:
    return not (omit_space_after(before) or omit_space_before(after))

# This formatter capitalizes sentences and ensures proper spacing
class SentenceFormatter(TextFormatter):

    def __init__(self, name: str):
        super().__init__(name)

    # Transform formatted text into separate words
    def format_to_words(self, text: str) -> List[str]:
        new_words = []
        for word in text.split():
            if word:
                new_words.append(word.lower())
        
        return new_words
    
    # Transform words into the given format
    def words_to_format(self, words: List[str], previous: str = "", next: str = "") -> str:        
        formatted_words = []

        # Add a leading space if the previous word had no leading space
        if previous and not previous.endswith(" ") and needs_space_between(previous, words[0]):
            formatted_words.append(" ")

        for index, word in enumerate(words):
            if word.islower():
                if index == 0 and self.detect_end_sentence(previous):
                    formatted_words.append(word.capitalize())
                elif index > 0 and self.detect_end_sentence(words[index - 1]):
                    formatted_words.append(word.capitalize())
                else:
                    formatted_words.append(word)
            else:
                formatted_words.append(word)

            # Add spaces according to the next word
            if index == len(words) - 1:
                if needs_space_between(word, next):
                    formatted_words[-1] += " "
            elif needs_space_between(word, words[index + 1]):
                formatted_words[-1] += " "
        
        return formatted_words

    def detect_end_sentence(self, previous: str) -> bool:
        return previous == "" or "".join(previous.split()).endswith(("?", ".", "!"))
    
    def determine_correction_keys(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        # Remove a space if we are adding punctiation
        # Add a leading space if the previous word had no leading space
        if previous and previous.endswith(" ") and omit_space_before(words[0]):
            return ["backspace"]
        return []

