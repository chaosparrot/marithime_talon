# Class that is used to transform the content of text to another text
class DayConverter:

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
    
    def convert(self, text: str) -> str:
        return text.capitalize()