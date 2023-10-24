from .managed_list import ManagedList
import re
from typing import Dict

# Regex taken from validator_collection package
URL_REGEX = re.compile(
    r"^"
    # protocol identifier
    r"(?:(?:https?|ftp)://)"
    # user:pass authentication
    r"(?:\S+(?::\S*)?@)?"
    r"(?:"
    # IP address exclusion
    # private & local networks
    r"(?!(?:10|127)(?:\.\d{1,3}){3})"
    r"(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})"
    r"(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})"
    # IP address dotted notation octets
    # excludes loopback network 0.0.0.0
    # excludes reserved space >= 224.0.0.0
    # excludes network & broadcast addresses
    # (first & last IP address of each class)
    r"(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])"
    r"(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}"
    r"(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))"
    r"|"
    r"(?:"
    r"(?:localhost|invalid|test|example)|("
    # host name
    r"(?:(?:[A-z\u00a1-\uffff0-9]-*_*)*[A-z\u00a1-\uffff0-9]+)"
    # domain name
    r"(?:\.(?:[A-z\u00a1-\uffff0-9]-*)*[A-z\u00a1-\uffff0-9]+)*"
    # TLD identifier
    r"(?:\.(?:[A-z\u00a1-\uffff]{2,}))"
    r")))"
    # port number
    r"(?::\d{2,5})?"
    # resource path
    r"(?:/\S*)?"
    r"$"
    , re.UNICODE)

# Manages all the user-managed lists dynamically
class ManagedList(ManagedList):
    websites = None

    # Append an item to the list, never overwriting known names
    def append_to_list(self, value: str, name: str):
        if self.websites:
            self.websites[name] = value

    # Add a value to the list
    # If the value already exists, overwrite its name
    # If the value exists multiple times, remove all but one instance and overwrite it
    def add_to_list(self, value: str, name: str):
        if self.websites:
            self.remove_from_list(value, name)
            self.websites[name] = value

    # Remove an item from the list
    def remove_from_list(self, value: str, name: str):
        if self.websites:
            names_to_remove = []
            for known_name in self.websites:
                if self.websites[known_name] == value:
                    names_to_remove.append(known_name)
            
            for known_name in names_to_remove:
                del self.websites[known_name]

            if name in self.websites:
                del self.websites[name]

    # Check if the value exists in the list
    def value_exists(self, value: str, name: str) -> bool:
        if self.websites:
            for known_name in self.websites:
                if self.websites[known_name] == value or known_name == name:
                    return True

        return False

    # Whether or not the value can possible be used as a value to keep in this list
    def matches(self, value: str) -> bool:
        return URL_REGEX.match(value.lower())
    
    # Turn the list contents into raw text
    def list_to_text(self) -> str:
        return ""

    # Turn the file contents into a list
    def text_to_choices(self) -> Dict[str, str]:
        return {}
