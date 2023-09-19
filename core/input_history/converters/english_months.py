# Class that is used to transform the content of text to another text
class MonthConverter:

    context_months = [
        "March",
        "May"
    ]

    months = [
        "January",
        "February",
        "April",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December"
    ]

    def match_text(self, text: str, previous: str = "", next = "") -> bool:
        if text.capitalize() in self.months:
            return True
        elif text.capitalize() in self.context_months:
            return previous.lower().endswith("on") or previous.lower().endswith("in")
        return False
    
    def convert(self, text: str) -> str:
        return text.capitalize()