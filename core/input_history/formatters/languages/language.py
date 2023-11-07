from typing import List

class Language:

    def dictation_format(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        return words
    
    def format_to_words(self, text: str) -> List[str]:
        return text.split()
    
    def determine_correction_keys(self, words: List[str], previous: str = "", next: str = "") -> List[str]:
        return []