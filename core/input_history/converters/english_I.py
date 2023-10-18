# Class that is used to transform the content of text to another text
class IConverter:

    tokens = {
        "i've": "I've",
        "i'll": "I'll",
        "i'm": "I'm",
        "i": "I",
        "i'd": "I'd",
    }

    def match_text(self, text: str, previous: str = "", next = "") -> bool:
        return text in self.tokens
    
    def convert(self, text: str) -> str:
        return self.tokens[text]