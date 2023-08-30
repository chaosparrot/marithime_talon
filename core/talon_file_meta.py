from talon import Module
from typing import List

mod = Module()

@mod.action_class
class Actions:

    def list_to_str(list_of_strings: List[str]) -> str:
        """Turns into a single concatenated string for easy usage in .talon files"""
        return "".join(list_of_strings)