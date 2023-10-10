from typing import List

# Class that is used to transform the content of text to another text
class EnglishCommaPrependingConverter:
    conjunctions = ["however", "although", "therefore", "thus", "accordingly"]
    question_words = ["what", "where", "when", "who", "why", "how"]
    location_adverbs = ["there", "here"]
    prepositions = ["in", "inside", "at", "on", "since", "until", "by", "with", "within", "over",
        "from", "to", "towards", "through", "between", "about", "into", "during", "above", "below", "beside", "beneath", "underneath",
        "under", "near", "among", "toward", "along", "across", "around"
    ]
    possible_conjunctions = ["and", "so", "as"]

    pronouns = ["i", "you", "he", "she", "they", "we"]
    articles = ["the", "a", "an"]

    but_postfixes = []
    yet_postfixes = []
    so_postfixes = []

    def __init__(self):
        self.but_postfixes = self.flatten([self.question_words, self.pronouns, self.articles, self.location_adverbs, self.prepositions, self.possible_conjunctions])
        self.so_postfixes = self.but_postfixes
        self.yet_postfixes = self.yet_postfixes

    def match_text(self, text: str, previous: str = "", next = "") -> bool:
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
    
    def convert(self, text: str) -> str:
        return ", " + text
    
    def flatten(self, lists) -> List[str]:
        list_of_items = []
        for word_list in lists:
            list_of_items.extend(word_list)
        return list_of_items