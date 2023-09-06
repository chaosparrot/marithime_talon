from talon import Module, Context, actions, settings, clip
from .input_history_typing import InputHistoryEvent
from typing import List
from .cursor_position_tracker import CursorPositionTracker
import re
mod = Module()
ctx = Context()

input_history: List[InputHistoryEvent] = []

mod.list("input_history_words", desc="A list of words that correspond to inserted text and their cursor positions for quick navigation in text")
ctx.lists["user.input_history_words"] = []

def text_to_phrase(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", ' ', text).lower().split()).strip()

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

    def determine_input_index(self) -> (int, int):
        line_index, character_index = self.cursor_position_tracker.get_cursor_index()
        if line_index > -1 and character_index > -1:
            for input_index, input_event in enumerate(self.input_history):
                if input_event.line_index == line_index and \
                    input_event.index_from_line_end <= character_index and input_event.index_from_line_end + len(input_event.text) >= character_index:
                    input_character_index = (len(input_event.text.replace("\n", "")) + input_event.index_from_line_end) - character_index
                    return input_index, input_character_index
            
            # Detect new lines properly
            if "\n" in self.input_history[-1].text:
                return len(self.input_history) - 1, len(self.input_history[-1].text)
        return -1, -1
    
    def insert_input_events(self, events: List[InputHistoryEvent]):
        for event in events:
            self.insert_input_event(event)

    def insert_input_event(self, event: InputHistoryEvent):
        line_index, character_index = self.cursor_position_tracker.get_cursor_index()
        if line_index > -1 and character_index > -1:
            input_index, input_character_index = self.determine_input_index()
            appended = False
            if input_index == len(self.input_history) - 1:
                if self.input_history[input_index].text != "" and input_character_index == len(self.input_history[input_index].text):

                    # Update the previous input events on this line to have accurate character count
                    for input_event in self.input_history:
                        if input_event.line_index == line_index:
                            input_event.index_from_line_end += len(event.text.replace("\n", ""))
                    event.line_index += line_index
                    self.input_history.append(event)
                    self.cursor_position_tracker.append_before_cursor(event.text)
                    appended = True
            # If empty events are inserted in the middle, just ignore them
            elif input_index < len(self.input_history) - 1 and event.text == "":
                return
            
            if appended == False:
                self.cursor_position_tracker.append_before_cursor(event.text)
                if input_character_index == len(self.input_history[input_index].text) and self.input_history[input_index].text != "":
                    self.append_event_after(input_index, event)
                
                # Just insert a event if we are at the exact start of an event
                elif input_character_index == 0 and self.input_history[input_index].text != "":
                    self.append_event_after(input_index - 1, event)
                # Merge input events if the appending happens in the middle of an event
                else:
                    self.merge_input_events(input_index, input_character_index, event)
        else:
            self.clear_input_history()
            self.input_history.append(event)
            self.cursor_position_tracker.append_before_cursor(event.text)

    def append_event_after(self, input_index: int, appended_event: InputHistoryEvent):
        appended_event.line_index = self.input_history[input_index].line_index
        if self.input_history[input_index].text.endswith("\n"):
            appended_event.line_index += 1
        reindex_text_lines = not appended_event.text.endswith("\n")

        self.input_history.insert(input_index + 1, appended_event)

        if reindex_text_lines:
            previous_length = 0
            for index, input_event in enumerate(reversed(self.input_history)):
                if input_event.line_index == appended_event.line_index:
                    true_index = len(self.input_history) - 1 - index
                    self.input_history[true_index].index_from_line_end = previous_length
                    previous_length += len(self.input_history[true_index].text.replace("\n", ""))

        # Fix the line index for the input events after this event
        if appended_event.text.endswith("\n"):
            for current_input_index, current_event in enumerate(self.input_history):
                if current_input_index > input_index + 1:
                    self.input_history[current_input_index].line_index += 1

    def merge_input_events(self, input_index: int, input_character_index: int, event: InputHistoryEvent):
        previous_input_event = self.input_history[input_index]

        # Line endings need to be counted separately as they aren't part of the input character index
        #if previous_input_event.text.endswith("\n"):
        #    input_character_index -= 2

        if "\n" in event.text:
            text_lines = event.text.splitlines()
            if event.text.endswith("\n"):
                text_lines.append("")
        else:
            text_lines = [event.text]
        
        total_text_lines = len(text_lines)
        events = []
        for line_index, text_line in enumerate(text_lines):
            text = ""
            if line_index == 0:
                text = previous_input_event.text[:input_character_index]
            text += text_line
            if total_text_lines > 1 and line_index != total_text_lines - 1:
                text += "\n"
            if line_index == total_text_lines - 1:
                text += previous_input_event.text[input_character_index:]
            
            new_event = InputHistoryEvent(text, text_to_phrase(text), "")
            new_event.line_index = previous_input_event.line_index + line_index
            events.append(new_event)

        for index, new_event in enumerate(events):
            if index == 0:
                self.input_history[input_index].text = new_event.text
                self.input_history[input_index].phrase = new_event.phrase
                if new_event.text.endswith("\n"):
                    self.input_history[input_index].index_from_line_end = 0
            else:
                self.append_event_after(input_index + index - 1, new_event)

    def text_to_input_history_events(self, text: str, phrase: str = None, format: str = None) -> InputHistoryEvent:
        lines = text.splitlines()
        if text.endswith("\n"):
            lines.append("")
        events = []
        if len(lines) == 1:
            event = InputHistoryEvent(text, "", "" if format is None else format)
            if phrase is not None:
                event.phrase = phrase
            else:
                event.phrase = " ".join(re.sub(r"[^\w\s]", ' ', text).lower().split()).strip()
            return [event]
            # If there are line endings, split them up properly
        else:
            for line_index, line in enumerate(lines):
                event = InputHistoryEvent(line + "\n" if line_index < len(lines) - 1 else line, "", "" if format is None else format)
                event.phrase = text_to_phrase(line)
                events.append(event)
            return events
        
    def remove_input_event(self, backspace_count = 0):
        line_index, character_index = self.cursor_position_tracker.get_cursor_index()
        if line_index > -1 and character_index > -1:
            input_index, input_character_index = self.determine_input_index()
