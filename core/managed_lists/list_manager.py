
from .managed_list import ManagedList
from typing import List

# Manages all the user-managed lists dynamically
class ListManager:
    managed_lists = None

    def __init__(self, managed_lists: List[ManagedList]):
        self.managed_lists = managed_lists

    def update(self, value: str, name: str, append: bool = False) -> bool:
        managed_list = self.determine_managed_list_to_use(value)

        if managed_list:
            return managed_list.update(value, name, append)
        else:
            return False
        
    def remove(self, value: str, name: str) -> bool:
        managed_list = self.determine_managed_list_to_use(value)

        if managed_list:
            return managed_list.remove(value, name)
        else:
            return False
    
    def determine_managed_list_to_use(self, value: str) -> ManagedList:
        managed_list_to_use = None
        for managed_list in self.managed_lists:
            if managed_list.matches(value):
                managed_list_to_use = managed_list
                break
        
        return managed_list_to_use
