from ..cursor_position_tracker import CursorPositionTracker, _CURSOR_MARKER
from ..input_history import InputHistoryManager
from ..input_history_typing import InputHistoryEvent

input_history = InputHistoryManager()
input_history.insert_input_events(input_history.text_to_input_history_events("Insert ", "insert"))
input_history.insert_input_events(input_history.text_to_input_history_events("an ", "an"))
input_history.insert_input_events(input_history.text_to_input_history_events("ad ", "ad"))
input_history.insert_input_events(input_history.text_to_input_history_events("that ", "that"))
input_history.insert_input_events(input_history.text_to_input_history_events("will ", "will"))
input_history.insert_input_events(input_history.text_to_input_history_events("get ", "get"))
input_history.insert_input_events(input_history.text_to_input_history_events("attention.", "attention"))

print( "With a filled input history containing a full sentence")
print( "    Attempting to find 'will' should result in an exact match...", input_history.has_matching_phrase("will") == True)
print( "    Attempting to find 'add' should result in a fuzzy match...", input_history.has_matching_phrase("add") == True)
print( "    Attempting to find 'apt' should not result in a match...", input_history.has_matching_phrase("apt") == False)
print( "    Attempting to find 'dad' should result in a fuzzy match...", input_history.has_matching_phrase("dad") == True)
print( "    Attempting to find 'and' should not result in a match...", input_history.has_matching_phrase("and") == False)