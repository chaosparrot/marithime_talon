from talon import Context
from typing import Dict
import os
import re
import csv
import io

# Manages all the user-managed lists dynamically
class ManagedList:
    name:str = ""
    ctx: Context = None
    list_name: str = "" # Context list name
    filename: str = "" # The filename to persist the list to
    rows = None

    def __init__(self, list_name: str, filename: str):
        self.list_name = list_name
        self.filename = str(filename)

        # Create the file if it does not exist yet
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as file:
                file.write("")


        self.rows = {}
        self.ctx = Context()
        self.update_context_list()

    # Append an item to the list, never overwriting known names
    def append_to_list(self, value: str, name: str):
        if self.rows is not None:
            self.rows[name] = value

    # Add a value to the list
    # If the value already exists, overwrite its name
    # If the value exists multiple times, remove all but one instance and overwrite it
    def add_to_list(self, value: str, name: str):
        if self.rows is not None``:
            self.remove_from_list(value, name)
            self.rows[name] = value

    # Remove an item from the list
    def remove_from_list(self, value: str, name: str):
        if self.rows is not None:
            names_to_remove = []
            for known_name in self.rows:
                if self.rows[known_name] == value:
                    names_to_remove.append(known_name)
            
            for known_name in names_to_remove:
                del self.rows[known_name]

            if name in self.rows:
                del self.rows[name]
    
    # Check if the value exists in the list
    def value_exists(self, value: str, name: str) -> bool:
        if self.rows is not None:
            for known_name in self.rows:
                if self.rows[known_name] == value or known_name == name:
                    return True

        return False

    # Remove the value if it exists in the list
    def remove(self, value: str, name: str) -> bool:
        if self.value_exists(value, name):
            self.remove_from_list(value, name)

            return self.persist()
        else:
            return False

    # Whether or not the value can possible be used as a value to keep in this list
    def matches(self, value: str, name: str) -> bool:
        return False
    
    # Whether or not this value can exist inside of this managed list
    def is_valid_value(self, value: str) -> bool:
        return self.matches(value, "")
    
    # Match by the list name
    def match_by_list_name(self, list_name: str):
        return self.name == list_name
    
    # Turn the list contents into raw text
    def list_to_text(self) -> str:
        rows = []
        output = io.StringIO()
        if self.rows is not None:
            for key in self.rows:
                rows.append({
                    "value": self.rows[key],
                    "spoken": key
                })

            csv_writer = csv.DictWriter(output, rows[0].keys(), delimiter=";", lineterminator="\n", quoting=csv.QUOTE_ALL)
            csv_writer.writeheader()
            csv_writer.writerows(rows)

        return output.getvalue()

    # Turn the file contents into a list
    def text_to_choices(self) -> Dict[str, str]:
        rows = {}
        if os.path.exists(self.filename):
            file = csv.DictReader(open(self.filename), delimiter=";", lineterminator="\n")

            for row in file:
                if "spoken" in row and "value" in row:
                    rows[row["spoken"]] = row["value"]

        return rows
    
    def update(self, value: str, name: str, append: bool = False) -> bool:
        if append:
            self.append_to_list(value, name)
        else:
            self.add_to_list(value, name)

        return self.persist()

    def persist(self) -> bool:
        if os.path.exists(self.filename):
            text = self.list_to_text()
            if text != "":
                with open(self.filename, 'w') as file:
                    file.write(text)
            
            return self.update_context_list()
        else:
            return False
        
    def reload_list(self, filename: str) -> Dict[str, str]:
        if filename == self.filename:
            choices = self.text_to_choices()
            self.update_context_list(choices)
            return choices
        return {}
    
    def update_context_list(self, choices: Dict[str, str] = None) -> bool:
        if choices is None:
            choices = self.text_to_choices()

        self.rows = choices

        filtered_choices = {}
        for key, value in choices.items():
            if key is not None:
                filtered_choices[re.sub(r'[^\w\s]', '', key)] = value

        try:
            self.ctx.lists[self.list_name] = choices
            return True
        except:
            return False