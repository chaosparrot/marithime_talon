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
            return previous.lower().replace(" ", "").endswith(("on", "at", "this", "next", "of")) or next.lower().replace(" ", "").startswith(("1", "2", "3", "4", "5", "6", "7", "8", "9"))
        return False
    
    def convert(self, text: str) -> str:
        return text.capitalize()