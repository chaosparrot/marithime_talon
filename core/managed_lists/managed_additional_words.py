from .managed_list import ManagedList
import re

# Manages all the user-managed lists dynamically
class ManagedAdditionalWords(ManagedList):
    name = "vocabulary"

    # Whether or not the value can possible be used as a value to keep in this list
    def matches(self, value: str, name: str) -> bool:
        return re.sub(r'[^\w\s]', '', value) == value
    
    def is_valid_value(self, value: str) -> bool:
        return True