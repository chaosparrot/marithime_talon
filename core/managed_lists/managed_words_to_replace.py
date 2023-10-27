from talon import Context
from .managed_list import ManagedList
import re
from typing import Dict

ctx = Context()

# Manages all the user-managed lists dynamically
class ManagedWordsToReplace(ManagedList):
    name = "words to replace"

    def __init__(self, filename):
        super().__init__("", filename)

    # Whether or not the value can possible be used as a value to keep in this list
    def matches(self, value: str, name: str) -> bool:
        return False
    
    def is_valid_value(self, value: str) -> bool:
        return True

    # "dictate.word_map" is used by Talon's built-in default implementation of
    # `dictate.replace_words`, but supports only single-word replacements.
    # Multi-word phrases are ignored.
    def update_context_list(self, choices: Dict[str, str] = None) -> bool:        
        ctx.settings["dictate.word_map"] = choices    
    