from talon import actions
from .managed_list import ManagedList
from typing import Dict
import re

# Manages all the user-managed lists dynamically
class ManagedHomophones(ManagedList):
    name = "homophones"

    def __init__(self):
        super().__init__("", "")

    # Append an item to the list, never overwriting known names
    def append_to_list(self, value: str, name: str):
        if actions.user.phonetic_similarity_score(value, name) >= 1:
            actions.user.homophones_add(value, name)
        else:
            actions.user.phonetic_similarities_add(value, name)

    # Remove an item from the list
    def remove_from_list(self, value: str, name: str):
        pass

    # Add a value to the list
    # If the value already exists, overwrite its name
    # If the value exists multiple times, remove all but one instance and overwrite it
    def add_to_list(self, value: str, name: str):
        self.append_to_list(value, name)

    # Whether or not the value can possible be used as a value to keep in this list
    def matches(self, value: str, name: str) -> bool:
        return actions.user.phonetic_similarity_score(value, name) == 0.8
    
    def is_valid_value(self, value: str) -> bool:
        return True
    
    # Turn the list contents into raw text
    def list_to_text(self) -> str:
        return ""

    # Turn the file contents into a list
    def text_to_choices(self) -> Dict[str, str]:
        return {}

    def persist(self) -> bool:
        return True
    
    def update_context_list(self, choices: Dict[str, str] = None) -> bool:
        # HOMOPHONES AND PHONETIC SIMILARITIES ARE HANDLED IN THE PHONETICS DIRECTORY INSTEAD
        return True 