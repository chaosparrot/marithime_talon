# Class that is used to transform the content of text to another text
class PunctuationConverter:

    punctuation = {
        "point": ".",
        "comma": ",",
        "coma": ",",
        "space": " ",
        "period": ".",
        "question mark": "?",
        "exclamation mark": "!"
    }

    def match_text(self, text: str, previous: str = "", next = "") -> bool:
        return text in self.punctuation or text in self.punctuation.values()
    
    def convert(self, text: str) -> str:
        return self.punctuation[text]