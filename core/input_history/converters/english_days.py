from .text_converter import TextConverter

# Class that is used to transform the content of text to another text
class DayConverter(TextConverter):

    days = [
        "Monday",
        "Mondays",
        "Tuesday",
        "Tuesdays",
        "Wednesday",
        "Wednesdays",
        "Thursday",
        "Thursdays",
        "Friday",
        "Fridays",
        "Saturday",
        "Saturdays",
        "Sunday",
        "Sundays"
    ]

    def match_text(self, text: str, previous: str = "", next = "") -> bool:
        return text.capitalize() in self.days
    
    def convert_text(self, text: str) -> str:
        return text.capitalize()