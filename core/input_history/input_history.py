from talon import Module, Context, actions, settings, clip
from .input_history_typing import InputHistoryEvent, InputContext
from .input_matcher import InputMatcher
from typing import List, Dict
from .cursor_position_tracker import CursorPositionTracker
from ..phonetics.actions import phonetic_search
import re
mod = Module()
ctx = Context()

def text_to_phrase(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", ' ', text).lower().split()).strip()

def normalize_text(text: str) -> str:
    return re.sub(r"[^\w\s]", ' ', text).replace("\n", " ")

MERGE_STRATEGY_IGNORE = -1
MERGE_STRATEGY_APPEND_AFTER = 0
MERGE_STRATEGY_JOIN = 1
MERGE_STRATEGY_SPLIT_LEFT_JOIN_RIGHT = 2
MERGE_STRATEGY_JOIN_LEFT_SPLIT_RIGHT = 3
MERGE_STRATEGY_SPLIT = 4

# Class to manage the state of inserted text
class InputHistoryManager:
    input_history: List[InputHistoryEvent]
    cursor_position_tracker: CursorPositionTracker = None

    last_action_type = "insert"

    def __init__(self):
        self.cursor_position_tracker = CursorPositionTracker()
        self.input_matcher = InputMatcher(phonetic_search)
        self.clear_input_history()

    def is_selecting(self) -> bool:
        return self.cursor_position_tracker.is_selecting()
    
    def is_phrase_selected(self, phrase: str) -> bool:
        return self.input_matcher.has_matching_phrase(self, phrase)

    def clear_input_history(self):
        self.cursor_position_tracker.clear()
        self.input_history = []

    def determine_leftmost_input_index(self):
        return self.determine_input_index(self.cursor_position_tracker.get_leftmost_cursor_index())
    
    def determine_rightmost_input_index(self):
        return self.determine_input_index(self.cursor_position_tracker.get_rightmost_cursor_index())

    def determine_input_index(self, cursor_index: (int, int) = None) -> (int, int):
        if cursor_index is None:
            cursor_index = self.cursor_position_tracker.get_cursor_index()

        line_index, character_index = cursor_index
        if line_index > -1 and character_index > -1: 
            for input_index, input_event in enumerate(self.input_history):
                if input_event.line_index == line_index and \
                    input_event.index_from_line_end <= character_index and input_event.index_from_line_end + len(input_event.text) >= character_index:
                    input_character_index = (len(input_event.text.replace("\n", "")) + input_event.index_from_line_end) - character_index
                    return input_index, input_character_index
            
            # Detect new lines properly
            if len(self.input_history) > 0 and "\n" in self.input_history[-1].text:
                return len(self.input_history) - 1, len(self.input_history[-1].text)
        return -1, -1
    
    def determine_context(self) -> InputContext:
        index, character_index = self.determine_input_index()
        if index > -1 and character_index > -1:
            current = self.input_history[index]
            previous = None if index == 0 else self.input_history[index - 1]
            next = None if index >= len(self.input_history) - 1 else self.input_history[index + 1]
            return InputContext(character_index, previous, current, next)

        else:
            return InputContext(0)
    
    def insert_input_events(self, events: List[InputHistoryEvent]):
        for index, event in enumerate(events):
            self.insert_input_event(event, index == len(events) - 1)

    def insert_input_event(self, event: InputHistoryEvent, reformat = True):
        if self.is_selecting() and event.text != "":
            self.remove_selection()

        line_index, character_index = self.cursor_position_tracker.get_cursor_index()
        if line_index > -1 and character_index > -1:
            input_index, input_character_index = self.determine_input_index()

            merge_strategies = self.detect_merge_strategy(input_index, input_character_index, event)

            appended = False
            if merge_strategies[0] == MERGE_STRATEGY_APPEND_AFTER or merge_strategies[1] == MERGE_STRATEGY_APPEND_AFTER:
                # Update the previous input events on this line to have accurate character count
                for input_event in self.input_history:
                    if input_event.line_index == line_index:
                        input_event.index_from_line_end += len(event.text.replace("\n", ""))
                event.line_index += line_index
                
                if merge_strategies[1] == MERGE_STRATEGY_APPEND_AFTER:
                    if input_index < len(self.input_history) - 1:
                        self.append_event_after(input_index, event, reformat)
                    else:
                        self.input_history.append(event)
                else:
                    self.append_event_after(input_index - 1, event, reformat)

                self.cursor_position_tracker.append_before_cursor(event.text)
                appended = True

            # If empty events are inserted in the middle, just ignore them
            elif input_index < len(self.input_history) - 1 and event.text == "":
                return
            
            if appended == False:
                self.cursor_position_tracker.append_before_cursor(event.text)

                if MERGE_STRATEGY_JOIN in merge_strategies:
                    if merge_strategies[1] == MERGE_STRATEGY_JOIN:
                        self.merge_input_events(input_index, input_character_index, event)
                    elif merge_strategies[0] == MERGE_STRATEGY_JOIN:
                        self.merge_input_events(input_index - 1, len(self.input_history[input_index - 1].text), event)
                    elif merge_strategies[2] == MERGE_STRATEGY_JOIN:
                        self.merge_input_events(input_index + 1, 0, event)
                    if reformat:
                        self.reformat_events()

                elif MERGE_STRATEGY_SPLIT in merge_strategies or \
                    MERGE_STRATEGY_JOIN_LEFT_SPLIT_RIGHT in merge_strategies or MERGE_STRATEGY_SPLIT_LEFT_JOIN_RIGHT in merge_strategies:
                    self.split_input_events(input_index, input_character_index, event, merge_strategies)
        else:
            self.clear_input_history()
            self.input_history.append(event)
            self.cursor_position_tracker.append_before_cursor(event.text)
        
        self.last_action_type = "insert"

    def append_event_after(self, input_index: int, appended_event: InputHistoryEvent, should_reindex = True):
        appended_event.line_index = self.input_history[input_index].line_index
        if self.input_history[input_index].text.endswith("\n"):
            appended_event.line_index += 1

        reindex = should_reindex and input_index + 1 < len(self.input_history)
        self.input_history.insert(input_index + 1, appended_event)
        if reindex:
            self.reformat_events()

    def find_self_repair(self, phrase: List[str]):
        return self.input_matcher.find_self_repair_match(self, phrase)

    def detect_self_repair(self, phrase: List[str]) -> bool:
        return self.find_self_repair(phrase) is not None

    def detect_merge_strategy(self, input_index: int, input_character_index: int, event: InputHistoryEvent) -> (int, int, int):
        current_strategy = MERGE_STRATEGY_IGNORE
        previous_strategy = MERGE_STRATEGY_IGNORE
        next_strategy = MERGE_STRATEGY_IGNORE

        if len(self.input_history) != 0:
            event_text = normalize_text(event.text)
            previous_event_text = "" if input_index - 1 < 0 else normalize_text(self.input_history[input_index - 1].text)
            current_event_text = "" if input_index < 0 else normalize_text(self.input_history[input_index].text)
            next_event_text = "" if input_index + 1 > len(self.input_history) - 1 else normalize_text(self.input_history[input_index + 1].text)

        if len(self.input_history) == 0:
            current_strategy = MERGE_STRATEGY_APPEND_AFTER

        # When we are at the start of an event, we can possibly join the previous event with the current input
        elif input_character_index == 0:
            if current_event_text == "" or ( not event_text.endswith(" ") and not current_event_text.startswith(" ") ):
                current_strategy = MERGE_STRATEGY_JOIN
            
            if input_index > 0 and not event_text.startswith(" ") and not previous_event_text.endswith(" "):
                previous_strategy = MERGE_STRATEGY_JOIN
            elif current_strategy != MERGE_STRATEGY_JOIN:
                previous_strategy = MERGE_STRATEGY_APPEND_AFTER
        
        # When we are at the end of an event, we can possibly join the next event with the current input
        elif input_character_index >= len(self.input_history[input_index].text):
            if (not event_text.startswith(" ") or event_text.replace(" ", "") == "") and not current_event_text.endswith(" "):
                current_strategy = MERGE_STRATEGY_JOIN

            if input_index < len(self.input_history) - 1 and not event_text.endswith(" ") and not next_event_text.startswith(" "):
                next_strategy = MERGE_STRATEGY_JOIN
            elif event.text.endswith("\n"):
                current_strategy = MERGE_STRATEGY_JOIN
            elif current_strategy != MERGE_STRATEGY_JOIN:
                current_strategy = MERGE_STRATEGY_APPEND_AFTER

        # Determine how to divide and join the current event
        else:
            current_text = self.input_history[input_index].text
            previous_character = " " if input_character_index - 1 < 0 else current_text[input_character_index - 1]
            next_character = " " if input_character_index < 0 and input_character_index != len(current_text) else current_text[input_character_index]
            can_join_left = ( not event_text.startswith(" ") and normalize_text(previous_character) != " " ) or event.text == "\n"
            can_join_right = not event_text.endswith(" ") and normalize_text(next_character) != " "

            if can_join_left and can_join_right:
                current_strategy = MERGE_STRATEGY_JOIN
            elif can_join_left:
                current_strategy = MERGE_STRATEGY_JOIN_LEFT_SPLIT_RIGHT
            elif can_join_right:
                current_strategy = MERGE_STRATEGY_SPLIT_LEFT_JOIN_RIGHT
            else:
                current_strategy = MERGE_STRATEGY_SPLIT

        return (previous_strategy, current_strategy, next_strategy)

    def split_input_events(self, input_index: int, input_character_index: int, event: InputHistoryEvent, merge_strategy: (int, int, int)):
        before_text = self.input_history[input_index].text[:input_character_index]
        after_text = self.input_history[input_index].text[input_character_index:]
        if merge_strategy[1] == MERGE_STRATEGY_SPLIT:
            self.input_history[input_index].text = before_text
            self.input_history[input_index].phrase = text_to_phrase(before_text)
            self.append_event_after(input_index, event)
            self.append_event_after(input_index + 1, InputHistoryEvent(after_text, text_to_phrase(after_text), self.input_history[input_index].format))

        elif merge_strategy[1] == MERGE_STRATEGY_JOIN_LEFT_SPLIT_RIGHT:
            self.input_history[input_index].text = before_text + event.text
            self.input_history[input_index].phrase = text_to_phrase(before_text + event.text)
            self.append_event_after(input_index, InputHistoryEvent(after_text, text_to_phrase(after_text), self.input_history[input_index].format))

        elif merge_strategy[1] == MERGE_STRATEGY_SPLIT_LEFT_JOIN_RIGHT:
            self.input_history[input_index].text = before_text
            self.input_history[input_index].phrase = text_to_phrase(before_text)
            event.text = event.text + after_text
            event.phrase = text_to_phrase(event.text)
            self.append_event_after(input_index, event)
        self.reformat_events()

    def merge_input_events(self, input_index: int, input_character_index: int, event: InputHistoryEvent):
        previous_input_event = self.input_history[input_index]

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
                event.phrase = text_to_phrase(text)
            return [event]
            # If there are line endings, split them up properly
        else:
            for line_index, line in enumerate(lines):
                event = InputHistoryEvent(line + "\n" if line_index < len(lines) - 1 else line, "", "" if format is None else format)
                event.phrase = text_to_phrase(line)
                events.append(event)
            return events
        
    def remove_selection(self) -> bool:
        selection_indexes = self.cursor_position_tracker.remove_selection()
        if selection_indexes[0][0] != selection_indexes[1][0] or \
            selection_indexes[0][1] != selection_indexes[1][1]:
            
            start_index = self.determine_input_index(selection_indexes[0])
            end_index = self.determine_input_index(selection_indexes[1])

            merge_event = None
            should_detect_merge = False

            events = []
            for event_index, event in enumerate(self.input_history):
                if event_index < start_index[0] or event_index > end_index[0]:

                    # Attempt merge if the events can be combined
                    if should_detect_merge and not re.sub(r"[^\w\s]", ' ', event.text).replace("\n", " ").startswith(" ") and \
                            not re.sub(r"[^\w\s]", ' ', events[-1].text).replace("\n", " ").endswith(" "):

                        merge_event = events[-1]
                        text = merge_event.text + event.text
                        events[-1].text = text
                        events[-1].phrase = text_to_phrase(text)
                        merge_event = None
                        should_detect_merge = False

                    # Otherwise just add the event
                    else:
                        events.append(event)
                else:
                    text = event.text

                    # Same event - No overlap between events
                    if event_index == start_index[0] and event_index == end_index[0]:
                        text = text[:start_index[1]] + text[end_index[1]:]
                        if text != "":
                            events.append(InputHistoryEvent(text, text_to_phrase(text), "", event.line_index))
                            should_detect_merge = start_index[1] == 0 or end_index[1] >= len(text.replace("\n", ""))
                    # Split event, remember the first event from the selection
                    elif event_index == start_index[0]:
                        text = text[:start_index[1]]
                        merge_event = InputHistoryEvent(text, text_to_phrase(text), "", event.line_index)
                        should_detect_merge = not re.sub(r"[^\w\s]", ' ', text).replace("\n", " ").endswith(" ")
                    # Split event, attempt to merge the first event with the current event
                    elif event_index == end_index[0]:
                        text = text[end_index[1]:]

                        if should_detect_merge and not re.sub(r"[^\w\s]", ' ', text).replace("\n", " ").startswith(" "):
                            text = merge_event.text + text
                        elif merge_event is not None:
                            events.append(merge_event)
                        merge_event = None
                        should_detect_merge = False
                        if text != "":
                            events.append(InputHistoryEvent(text, text_to_phrase(text), "", event.line_index))
            
            # If we are left with a merge event, add it anyway
            if merge_event is not None:
                events.append(merge_event)

            self.input_history = events
            self.reformat_events()

            return True
        else:
            return False
    
    def apply_delete(self, delete_count = 0):
        if self.is_selecting() and delete_count > 0:
            if self.remove_selection():
                delete_count -= 1

        if delete_count <= 0:
            return

        line_index, character_index = self.cursor_position_tracker.get_cursor_index()
        if line_index > -1 and character_index > -1:
            input_index, input_character_index = self.determine_input_index()
            text = self.input_history[input_index].text
            remove_from_input_event = min(len(text) - input_character_index, delete_count)
            remove_from_next_input_events = delete_count - (len(text) - input_character_index)

            # If we are removing a full event in the middle, make sure to just remove the event
            text = text[:input_character_index] + text[input_character_index + remove_from_input_event:]
            should_detect_merge = input_character_index == 0 or input_character_index >= len(text.replace("\n", ""))

            if text == "":
                del self.input_history[input_index]
                input_index -= 1
            else:
                self.input_history[input_index].text = text
                self.input_history[input_index].phrase = text_to_phrase(text)

            next_input_index = input_index + 1
            if remove_from_next_input_events > 0:
                while next_input_index < len(self.input_history) and remove_from_next_input_events > 0:
                    if len(self.input_history[next_input_index].text) <= remove_from_next_input_events:
                        remove_from_next_input_events -= len(self.input_history[next_input_index].text)
                        del self.input_history[next_input_index]
                    else:
                        next_text = self.input_history[next_input_index].text[remove_from_next_input_events:]
                        self.input_history[next_input_index].text = next_text
                        self.input_history[next_input_index].phrase = text_to_phrase(next_text)

                        remove_from_next_input_events = 0
                        self.reformat_events()

            # Detect if we should merge the input events if the text combines
            if should_detect_merge and next_input_index - 1 >= 0:
                input_index = next_input_index - 1
                next_input_index = input_index + 1
                
                if next_input_index < len(self.input_history):
                    previous_text = "" if input_index < 0 else self.input_history[input_index].text
                    text = self.input_history[next_input_index].text

                    if should_detect_merge and (text == "\n" or not re.sub(r"[^\w\s]", ' ', text).replace("\n", " ").startswith(" ") ) and not re.sub(r"[^\w\s]", ' ', previous_text).replace("\n", " ").endswith(" "):
                        text = previous_text + text
                        self.input_history[input_index].text = text
                        self.input_history[input_index].phrase = text_to_phrase(text)
                        del self.input_history[next_input_index]
                        self.reformat_events()            

            self.cursor_position_tracker.remove_after_cursor(delete_count)
        self.last_action_type = "remove"
        
    def apply_backspace(self, backspace_count = 0):
        if self.is_selecting() and backspace_count > 0:
            if self.remove_selection():
                backspace_count -= 1

        if backspace_count <= 0:
            return

        line_index, character_index = self.cursor_position_tracker.get_cursor_index()
        if line_index > -1 and character_index > -1:
            input_index, input_character_index = self.determine_input_index()
            remove_from_previous_input_events = abs(min(0, input_character_index - backspace_count ))
            remove_from_input_event = backspace_count - remove_from_previous_input_events
            text = self.input_history[input_index].text

            # If we are removing a full event in the middle, make sure to just remove the event
            text = text[:input_character_index - remove_from_input_event] + text[input_character_index:]
            should_detect_merge = input_character_index - backspace_count <= 0 or input_character_index >= len(text.replace("\n", ""))            
            if text == "" and input_index + 1 < len(self.input_history) - 1:
                del self.input_history[input_index]
            else:
                self.input_history[input_index].text = text
                self.input_history[input_index].phrase = text_to_phrase(text)
            
            previous_input_index = input_index - 1
            if remove_from_previous_input_events > 0:
                while previous_input_index >= 0 and remove_from_previous_input_events > 0:
                    if len(self.input_history[previous_input_index].text) <= remove_from_previous_input_events:
                        remove_from_previous_input_events -= len(self.input_history[previous_input_index].text)
                        del self.input_history[previous_input_index]
                        previous_input_index -= 1
                    else:
                        previous_text = self.input_history[previous_input_index].text
                        previous_text = previous_text[:len(previous_text) - remove_from_previous_input_events]
                        self.input_history[previous_input_index].text = previous_text
                        self.input_history[previous_input_index].phrase = text_to_phrase(previous_text)

                        remove_from_previous_input_events = 0
                        self.reformat_events()

            # Detect if we should merge the input events if the text combines
            if should_detect_merge:
                input_index = previous_input_index + 1
                if input_index == 0 and len(self.input_history) > 1:
                    previous_input_index = 0

                if previous_input_index + 1 < len(self.input_history):
                    previous_text = "" if previous_input_index < 0 else self.input_history[previous_input_index].text
                    text = self.input_history[previous_input_index + 1].text

                    if should_detect_merge and (text == "\n" or not re.sub(r"[^\w\s]", ' ', text).replace("\n", " ").startswith(" ") ) and not re.sub(r"[^\w\s]", ' ', previous_text).replace("\n", " ").endswith(" "):
                        text = previous_text + text
                        self.input_history[previous_input_index].text = text
                        self.input_history[previous_input_index].phrase = text_to_phrase(text)
                        del self.input_history[previous_input_index + 1]

                        self.reformat_events()            

            self.cursor_position_tracker.remove_before_cursor(backspace_count)
        self.last_action_type = "remove"

    def reformat_events(self):
        length = len(self.input_history)
        if length == 0:
            return

        # First sync the line counts
        line_index = 0
        previous_line_index = self.input_history[0].line_index
        new_events = []
        for index, event in enumerate(self.input_history):
            event.line_index = line_index
            new_events.append(event)
            if event.text.endswith("\n"):
                line_index += 1

        # Then sync the character count
        previous_line_index = new_events[-1].line_index
        previous_line_end_count = 0
        for index, event in enumerate(reversed(new_events)):
            true_index = length - 1 - index
            if event.line_index == previous_line_index:
                new_events[true_index].index_from_line_end = previous_line_end_count
            else:
                previous_line_end_count = 0
                new_events[true_index].index_from_line_end = 0
                previous_line_index = event.line_index
            previous_line_end_count += len(event.text.replace("\n", ""))

        self.input_history = new_events

    def apply_key(self, keystring: str):
        keys = keystring.lower().split(" ")
        for key in keys:
            key_used = self.cursor_position_tracker.apply_key(key)
            if key_used:
                self.last_action_type = self.cursor_position_tracker.last_cursor_movement
            if not key_used and "backspace" in key or "delete" in key:
                key_modifier = key.split(":")
                if len(key_modifier) > 1 and key_modifier[-1] == "up":
                    continue
                if "ctrl" in key_modifier[0]:
                    self.clear_input_history()
                else:
                    key_presses = 1
                    if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                        key_presses = int(key_modifier[-1])

                    if "delete" in key:
                        self.apply_delete(key_presses)
                    else:
                        self.apply_backspace(key_presses)

        if not self.cursor_position_tracker.text_history:
            self.clear_input_history()

    def has_matching_phrase(self, phrase: str) -> bool:
        return self.input_matcher.has_matching_phrase(self, phrase)
    
    def go_phrase(self, phrase: str, position: str = 'end', keep_selection: bool = False, next_occurrence: bool = True) -> List[str]:
        event = self.find_event_by_phrase(phrase, -1 if position == 'end' else 0, next_occurrence)
        if event:
            return self.navigate_to_event(event, -1 if position == 'end' else 0, keep_selection)
        else:
            return None
        
    def select_until_end(self, phrase: str = "") -> List[str]:
        keys = []
        if len(self.input_history) > 0:
            if phrase != "":
                start_event = self.find_event_by_phrase(phrase, 0, True, False)
                if start_event:
                    keys.extend(self.navigate_to_event(start_event, 0, False))
            
            keys.extend(self.select_event(self.input_history[-1], True))

        return keys
    
    def select_phrases(self, phrases: List[str], match_threshold: float = 1, extend_selection: bool = False) -> List[str]:
        # For a single phrase we can fall back to a single selection
        if len(phrases) == 1:
            return self.select_phrase(phrases[0], extend_selection)

        # Determine if we need to cycle between selections
        should_go_to_next_occurrence = not extend_selection
        if should_go_to_next_occurrence:
            for phrase in phrases:
                should_go_to_next_occurrence = self.input_matcher.is_phrase_selected(self, phrase)
                if not should_go_to_next_occurrence:
                    break

        best_match = self.input_matcher.find_best_match_by_phrases(self, phrases, match_threshold, should_go_to_next_occurrence, True)
        if best_match is not None and len(best_match) > 0:
            if not extend_selection:
                keys = self.navigate_to_event(best_match[0], 0)
            else:
                keys = self.select_event(best_match[0], extend_selection)
            keys.extend( self.select_event(best_match[-1], True))
            return keys
        else:
            return []

    def select_phrase(self, phrase: str, extend_selection: bool = False) -> List[str]:        
        event = self.find_event_by_phrase(phrase, 0, not extend_selection and self.input_matcher.is_phrase_selected(self, phrase), True)
        return self.select_event(event, extend_selection)
    
    def select_event(self, event: InputHistoryEvent, extend_selection: bool = False) -> List[str]:
        if event:
            self.use_last_set_formatter = False
            select_key_down = "shift:down"
            select_key_up = "shift:up"

            keys = []

            # Continue the selection we have going right now
            if extend_selection:
                # By default, go towards the end of the event
                event_cursor_end = -1            
                reset_selection = False

                left_cursor = self.cursor_position_tracker.get_leftmost_cursor_index()
                right_cursor = self.cursor_position_tracker.get_rightmost_cursor_index()

                cursor_index = self.cursor_position_tracker.get_cursor_index()
                cursor_on_left_side = cursor_index[0] == left_cursor[0] and cursor_index[1] == left_cursor[1]

                # We need to reset our selection if we are adding new tokens in the opposite side of the selection
                if event.line_index < left_cursor[0] or \
                    (event.line_index == left_cursor[0] and event.index_from_line_end + len(event.text.replace('\n', '')) > left_cursor[1]):

                    # When extending left, make sure to move to the start of the event to be selected
                    left_cursor = (event.line_index, event.index_from_line_end + len(event.text.replace('\n', '')))
                    if cursor_on_left_side:
                        event_cursor_end = 0
                    else:
                        reset_selection = True
                
                # When going right, we need to reset the selection if our cursor is on the left side of the seletion
                elif event.line_index > right_cursor[0] or \
                    (event.line_index == right_cursor[0] and event.index_from_line_end < right_cursor[1]):

                    right_cursor = (event.line_index, event.index_from_line_end)                
                    if cursor_on_left_side:
                        reset_selection = True

                if not reset_selection:
                    if not self.cursor_position_tracker.shift_down:
                        self.apply_key(select_key_down)
                        keys.append(select_key_down)
                    
                    after_keys = self.navigate_to_event(event, event_cursor_end, True)
                    keys.extend(after_keys)

                # Reset the selection, go to the left side and all the way to the right side
                else:
                    key_events = self.cursor_position_tracker.navigate_to_position(left_cursor[0], left_cursor[1], True)
                    for key in key_events:
                        self.apply_key(key)
                    keys.extend(key_events)

                    self.apply_key(select_key_down)
                    keys.append(select_key_down)

                    key_events = self.cursor_position_tracker.navigate_to_position(right_cursor[0], right_cursor[1], False)
                    for key in key_events:
                        self.apply_key(key)
                    keys.extend(key_events)
            
            # New selection - just go to the event and select it
            else:                
                before_keys = self.navigate_to_event(event, 0, False)
                keys.extend(before_keys)
                keys.append(select_key_down)
                self.apply_key(select_key_down)
                after_keys = self.navigate_to_event(event, -1, True)                
                keys.extend(after_keys)

            self.apply_key(select_key_up)
            keys.append(select_key_up)

            return keys
        else: 
            return None

    def find_event_by_phrase(self, phrase: str, char_position: int = -1, next_occurrence: bool = True, selecting: bool = False) -> InputHistoryEvent:
        return self.input_matcher.find_single_match_by_phrase(self, phrase, char_position, next_occurrence, selecting)

    def navigate_to_event(self, event: InputHistoryEvent, char_position: int = -1, keep_selection: bool = False) -> List[str]:
        if event != None:
            index_from_end = event.index_from_line_end + len(event.text)
            if char_position == -1:
                char_position = -len(event.text)

            key_events = self.cursor_position_tracker.navigate_to_position(event.line_index, index_from_end + char_position, not keep_selection)
            for key in key_events:
                self.apply_key(key)

            # If we do not move, still keep a memory that a cursor movement was done rather than an insertion or removal
            if len(key_events) == 0:
                self.last_action_type = self.cursor_position_tracker.last_cursor_movement
        else:
            key_events = []
        return key_events
    
    def get_current_formatters(self) -> List[str]:
        formatters = []
        input_index = self.determine_leftmost_input_index()
        if input_index[0] != -1:
            event = self.input_history[input_index[0]]
            if len(event.format) > 0:
                formatters = event.format.split("|")
        return formatters
    
    # Get the text before the cursor, or a possible selection
    def get_previous_text(self):
        input_index = self.determine_leftmost_input_index()
        previous_text = ""
        if input_index[0] != -1:
            previous_text = ""
            for index, event in enumerate(self.input_history):
                if index < input_index[0]:
                    previous_text += event.text
                elif index == input_index[0]:
                    if input_index[1] > 0 and input_index[1] <= len(event.text.replace("\n", "")):
                        previous_text += event.text[:input_index[1]]
                else:
                    break

        return previous_text

    # Get the text after the cursor, or a possible selection
    def get_next_text(self) -> str:
        right_input_index = self.determine_rightmost_input_index()
        next_text = ""
        if right_input_index[0] != -1:
            for index, event in enumerate(self.input_history):
                if index > right_input_index[0]:
                    next_text += event.text
                elif index == right_input_index[0]:
                    if right_input_index[1] > 0 and right_input_index[1] < len(event.text.replace("\n", "")):
                        next_text += self.input_history[index].text[right_input_index[1]:]

        return next_text
