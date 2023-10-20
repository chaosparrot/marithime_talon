import re
from .input_history import InputHistoryManager
import time

# Class keeping track of the context of the inserted text
class InputContext:

    key_matching: str = ""
    pid = -1
    modified_at: float = 0

    def __init__(self, key_matching: str = "", pid: int = -1):
        self.key_matching = key_matching
        self.pid = pid
        self.input_history_manager = InputHistoryManager()
        self.update_modified_at()

    def update_modified_at(self):
        self.modified_at = time.perf_counter()

    def update_pattern(self, key_matching: str = "", pid: int = -1):
        if key_matching != "":
            self.key_matching = key_matching
        if pid != -1:
            self.pid = pid

    def match_pattern(self, key_matching: str, pid: int) -> bool:
        return self.key_matching == key_matching or pid == self.pid

    # A context is stale if it has had no changes in 5 minutes
    def is_stale(self, inactive_threshold: int = 300):
        return time.perf_counter() - self.modified_at > inactive_threshold
    
    def apply_key(self, key: str):
        self.input_history_manager.apply_key(key)

    def clear_context(self):
        self.update_modified_at()
        self.input_history_manager.clear_input_history()

    def destroy(self):
        self.clear_context()
        self.pid = -1
        self.key_matching = ""
        self.modified_at = 0
        self.input_history_manager = None

    