from .buffer import VirtualBuffer
import time

# Class keeping track of the context of the inserted text
class InputContext:

    app_name: str = ""
    title: str = ""
    role: str = ""
    pid = -1
    modified_at: float = 0
    accessible_api_available = False
    buffer: VirtualBuffer = None

    def __init__(self, app_name: str = "", title: str = "", pid: int = -1):
        self.app_name = app_name
        self.title = title
        self.pid = pid
        self.buffer = VirtualBuffer()
        self.update_modified_at()

    def set_accessible_api_available(self, role:str, availability: bool):
        self.role = role
        self.accessible_api_available = availability

    def update_modified_at(self):
        self.modified_at = time.perf_counter()

    def update_pattern(self, app_name: str = "", title: str = "", pid: int = -1):
        #print( self.app_name, app_name, self.title, title, self.pid, pid)
        if app_name != "":
            self.app_name = app_name
        if title != "":
            self.title = title
        if pid != -1:
            self.pid = pid

    def match_pattern(self, app_name: str, title: str, pid: int) -> bool:
        return self.coarse_match_pattern(app_name, title, pid) and title.lower() == self.title
    
    def coarse_match_pattern(self, app_name: str, title: str, pid: int) -> bool:
        return self.app_name.lower() == app_name.lower() or self.pid == pid

    # A context is stale if it has had no changes in 5 minutes
    def is_stale(self, inactive_threshold: int = 300):
        return time.perf_counter() - self.modified_at > inactive_threshold
    
    def apply_key(self, key: str):
        self.buffer.apply_key(key)

    def clear_context(self):
        self.update_modified_at()
        self.buffer.clear_tokens()

    def destroy(self):
        self.clear_context()
        self.pid = -1
        self.key_matching = ""
        self.modified_at = 0
        self.buffer = None

    