# Class that is used to transform the content of text to another text
class TextConverter:

    def match_text(self, text: str, previous: str = "", next = "") -> bool:
        return False
    
    def convert(self, text: str) -> str:
        return text