from .managed_list import ManagedList
from typing import Dict

# Manages all the user-managed lists dynamically
class ManagedAbbreviations(ManagedList):
    name = "abbreviations"

    # Whether or not the value can possible be used as a value to keep in this list
    def matches(self, value: str, name: str) -> bool:
        return False #len(name) > len(value) TODO FIGURE OUT AUTO-MATCHING ABBREVIATIONS

    def is_valid_value(self, value: str) -> bool:
        return True