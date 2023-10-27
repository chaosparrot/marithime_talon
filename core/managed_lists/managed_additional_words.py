from .managed_list import ManagedList
import re

# Manages the vocabulary ( like additional words does )
class ManagedVocabulary(ManagedList):
    name = "vocabulary"

    def matches(self, value: str, name: str) -> bool:
        return False
    
    def is_valid_value(self, value: str) -> bool:
        return True