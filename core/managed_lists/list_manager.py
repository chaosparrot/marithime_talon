
from talon import Module, Context, resource
from .managed_list import ManagedList
from typing import List
from ..user_settings import track_csv_list

mod = Module()
mod.list("managed_lists", desc="A list of managed lists available to be changed through voice commands")

ctx = Context()

# Manages all the user-managed lists dynamically
class ListManager:
    base_managed_lists = None
    language_aware_managed_lists = None
    managed_lists = None
    current_lang = "en"
    current_engine = ""

    def __init__(self, lists: List[ManagedList], language_aware_lists: List[ManagedList] = []):
        self.base_managed_lists = lists
        self.language_aware_managed_lists = language_aware_lists
        self.load_language("en", True)

    def load_language(self, language = "en", forced_reload = False):
        replace_suffix = "_" + self.current_lang + ".csv" if self.current_lang != "en" else ".csv"
        suffix = "_" + language + ".csv" if language != "en" else ".csv"

        self.managed_lists = [managed_list for managed_list in self.base_managed_lists]
        for managed_list in self.language_aware_managed_lists:
            managed_list.filename = managed_list.filename.replace(replace_suffix, suffix)
            self.managed_lists.append(managed_list)
        
        # TODO THIS ADDS RESOURCE TRACKERS EVERY TIME THE LANGUAGE SWITCHES
        # DO NOT CURRENTLY KNOW HOW TO UN-WATCH THIS LIST
        for managed_list in self.managed_lists:
            if managed_list.filename:
                track_csv_list(managed_list.filename, managed_list.reload_list)

        ctx.lists["user.managed_lists"] = [managed_list.name for managed_list in self.managed_lists]

    def update(self, value: str, name: str, append: bool = False, list_name: str = None) -> bool:
        managed_list = self.determine_managed_list_to_use(value, name, list_name)

        if managed_list:
            return managed_list.update(value, name, append)
        else:
            return False
        
    def remove(self, value: str, name: str, list_name: str = None) -> bool:
        managed_list = self.determine_managed_list_to_use(value, name, list_name)

        if managed_list:
            return managed_list.remove(value, name)
        else:
            return False
    
    def determine_managed_list_to_use(self, value: str, name: str, list_name: str) -> ManagedList:
        managed_list_to_use = None
        for managed_list in self.managed_lists:
            if managed_list.is_valid_value(value):
                if list_name != None:
                    if managed_list.match_by_list_name(list_name):
                        managed_list_to_use = managed_list
                else:
                    if managed_list.matches(value, name):
                        managed_list_to_use = managed_list
                        break
        
        return managed_list_to_use
