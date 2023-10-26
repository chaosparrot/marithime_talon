from .managed_list import ManagedList
import re

# Manages all the user-managed lists dynamically
class ManagedHomophones(ManagedList):
    name = "homophones"

    # Whether or not the value can possible be used as a value to keep in this list
    def matches(self, value: str, name: str) -> bool:
        return False
    
    def is_valid_value(self, value: str) -> bool:
        return True    