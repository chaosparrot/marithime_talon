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
    return not text or no_space_before.search(text)
def omit_space_after(text: str) -> bool:
    return not text or no_space_after.search(text)
def needs_space_between(before: str, after: str) -> bool:
    return not (omit_space_after(before) or omit_space_before(after))

# This formatter capitalizes sentences and ensures proper spacing
class SentenceFormatter(TextFormatter):
    def __init__(self, name: str):
        super().__init__(name)

    # Transform formatted text into separate words
    def format_to_words(self, text: str) -> List[str]:
        return text.split()
    
    # Transform words into the given format
    def words_to_format(self, words: List[str], previous: str = "", next: str = "") -> str:        
        formatted_words = []

        # Add a leading space if the previous word had no leading space
        if previous and not previous.endswith(" ") and not omit_space_after(previous):
            formatted_words.append(" ")

        for index, word in enumerate(words):
            if index == 0 and self.detect_end_sentence(previous):
                formatted_words.append(word.capitalize())
            elif index > 0 and self.detect_end_sentence(words[index - 1]):
                formatted_words.append(word.capitalize())
            else:
                formatted_words.append(word)

            # Add spaces according to the previous word
            if index == 0 and needs_space_between(previous, word):
                formatted_words[-1] += " "
            elif index > 0 and needs_space_between(words[index - 1], word):
                formatted_words[-1] += " "
        
        # Remove the final space if it was added
        if formatted_words[-1].endswith(" "):
            formatted_words[-1] = formatted_words[-1][:-1]
        
        return formatted_words

    def detect_end_sentence(self, previous: str) -> bool:
        return previous == "" or "".join(previous.split()).endswith(("?", ".", "!"))