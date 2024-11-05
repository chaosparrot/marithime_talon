from typing import List
from .text_converter import TextConverter

def flatten(lists) -> List[str]:
    list_of_items = []
    for word_list in lists:
        list_of_items.extend(word_list)
    return list_of_items

question_words = ["what", "where", "when", "who", "why", "how"]
location_adverbs = ["there", "here"]
prepositions = ["in", "inside", "at", "on", "since", "until", "by", "with", "within", "over",
    "from", "to", "towards", "through", "between", "about", "into", "during", "above", "below", "beside", "beneath", "underneath",
    "under", "near", "among", "toward", "along", "across", "around"
]
possible_conjunctions = ["and", "so", "as"]
pronouns = ["i", "you", "he", "she", "they", "we"]
articles = ["the", "a", "an", "this", "that", "these", "those"]

# Class that is used to transform the content of text to another text
class EnglishCommaPrependingConverter(TextConverter):
    conjunctions = ["however", "although", "therefore", "thus", "accordingly"]

    but_postfixes = []
    yet_postfixes = []
    so_postfixes = []

    def __init__(self):
        self.but_postfixes = flatten([question_words, pronouns, articles, location_adverbs, prepositions, possible_conjunctions])
        self.so_postfixes = self.but_postfixes
        self.yet_postfixes = self.but_postfixes

    def match_text(self, text: str, previous: str = "", next = "") -> bool:
        return self.comma_prefixing(text, previous, next)
    
    def comma_prefixing(self, text: str, previous: str, next: str) -> bool:
        if previous and not previous.replace(" ", "").endswith((",", "!", ".", "?")):
            words = text.lower().split()

            previous_word = "" if len(previous.split()) == 0 else previous.split()[-1]
            starting_word = words[0]
            next_word = ("" if len(next.split()) == 0 else next.lower().split()[0]) if len(words) == 1 else words[1]
            if starting_word in self.conjunctions and not previous.replace(" ", "").endswith("and"):
                return True

            if starting_word == "but" and next_word in self.but_postfixes:
                return True

            if starting_word == "so" and next_word in self.so_postfixes:
                return True
            
            if starting_word in ["yet", "still"] and previous_word != ["not"] and next_word in self.yet_postfixes:
                return True

        return False

    def convert_text(self, text: str) -> str:
        return ", " + text

class EnglishCommaAppendingConverter(TextConverter):

    def match_text(self, text: str, previous: str = "", next = "") -> bool:
        return self.comma_appending(text, previous, next)
    
    def comma_appending(self, text: str, previous: str, next: str) -> bool:
        previous_word = "" if len(previous.lower().split()) == 0 else previous.lower().split()[-1]
        if next and not next.replace(" ", "").startswith((",", "!", ".", "?")):
            words = text.lower().split()
            starting_word = words[0] if len(words) > 0 else ""
            if starting_word.replace(" ", "").endswith((",", ".", "!", "?")):
                return False

            if previous_word == "for" and starting_word == "example":
                return True
            
            if previous_word == "in" and starting_word == "fact":
                return True
            
            if starting_word in ["however", "therefore", "furthermore", "meanwhile", "nevertheless"]:
                return True

        return False

    def convert_text(self, text: str) -> str:
        return text + ","