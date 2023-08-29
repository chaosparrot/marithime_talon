from talon import Module, Context, actions, settings, clip
from .input_history_typing import InputHistoryEvent
from typing import List
from .cursor_position_tracker import CursorPositionTracker
mod = Module()
ctx = Context()

input_history: List[InputHistoryEvent] = []

mod.list("input_history_words", desc="A list of words that correspond to inserted text and their cursor positions for quick navigation in text")
ctx.lists["user.input_history_words"] = []

# Class to manage the cursor position within inserted text
class InputHistoryManager:
    input_history: List[InputHistoryEvent]
    cursor_position_tracker: CursorPositionTracker = None

    def __init__(self):
        self.cursor_position_tracker = CursorPositionTracker()
        self.clear_input_history()

    def clear_input_history(self):
        self.cursor_position_tracker.clear()        
        self.input_history = []
        self.index_input_history()
    
    def index_input_history(self):
        items = []
        for event in input_history:
            items[event.phrase] = str(event.start_index) + ":" + str(event.end_index) + ":" + event.text
        ctx.lists["user.input_history_words"] = items