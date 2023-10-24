from talon import Context
from typing import Dict
import os
import re

# Manages all the user-managed lists dynamically
class ManagedList:
    ctx: Context = None
    list_name: str = "" # Context list name
    filename: str = "" # The filename to persist the list to

    def __init__(self, list_name: str, filename: str):
        self.list_name = list_name
        self.filename = filename
        self.ctx = Context()

    # Append an item to the list, never overwriting known names
    def append_to_list(self, value: str, name: str):
        pass

    # Add a value to the list
    # If the value already exists, overwrite its name
    # If the value exists multiple times, remove all but one instance and overwrite it
    def add_to_list(self, value: str, name: str):
        pass

    # Remove an item from the list
    def remove_from_list(self, value: str, name: str):
        pass
    
    # Check if the value exists in the list
    def value_exists(self, value: str, name: str) -> bool:
        return False

    # Remove the value if it exists in the list
    def remove(self, value: str, name: str) -> bool:
        if self.value_exists():
            self.remove_from_list()

            return self.persist()
        else:
            return False

    # Whether or not the value can possible be used as a value to keep in this list
    def matches(self, value: str) -> bool:
        return False
    
    # Turn the list contents into raw text
    def list_to_text(self) -> str:
        return ""

    # Turn the file contents into a list
    def text_to_choices(self) -> Dict[str, str]:
        return {}

    def update(self, value: str, name: str, append: bool = False) -> bool:
        if append:
            self.append(value, name)
        else:
            self.overwrite(value, name)

        return self.persist()

    def persist(self) -> bool:
        if os.path.exists(self.filename):
            text = self.choices_to_text()
            with open(self.filename, 'w') as file:
                file.write(text)
            
            return self.update_context_list()
        else:
            return False
    
    def update_context_list(self) -> bool:
        choices = self.text_to_choices()

        filtered_choices = {}
        for key, value in choices.items():
            filtered_choices[re.sub(r'[^\w\s]', '', key)] = value

        try:
            self.ctx.lists[self.list_name] = choices
            return True
        except:
            return False