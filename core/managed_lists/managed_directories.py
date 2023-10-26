from .managed_list import ManagedList
import os

class ManagedDirectories(ManagedList):
    name = "directories"

    # Whether or not the value can possible be used as a value to keep in this list
    def matches(self, value: str, name: str) -> bool:
        return os.path.exists(value) and os.path.isdir(value)
