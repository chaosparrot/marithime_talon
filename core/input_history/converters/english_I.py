from .text_converter import TextConverter

# Class that is used to transform the content of text to another text
class IConverter(TextConverter):

    tokens = {
        "i've": "I've",
        "i'll": "I'll",
        "i'm": "I'm",
        "i": "I",
        "i'd": "I'd",
    }

    def match_text(self, text: str, previous: str = "", next = "") -> bool:
        return text in self.tokens
    
    def convert_text(self, text: str) -> str:
        return self.tokens[text]