from ..cursor_position_tracker import CursorPositionTracker, _CURSOR_MARKER
from ..input_history import InputHistoryManager
from ..input_history_typing import InputHistoryEvent
from ...utils.test import create_test_suite

suite = create_test_suite("With a filled input history containing a full sentence")
def test_fuzzy_matching(assertion):
    input_history = InputHistoryManager()
    input_history.insert_input_events(input_history.text_to_input_history_events("Insert ", "insert"))
    input_history.insert_input_events(input_history.text_to_input_history_events("an ", "an"))
    input_history.insert_input_events(input_history.text_to_input_history_events("ad ", "ad"))
    input_history.insert_input_events(input_history.text_to_input_history_events("that ", "that"))
    input_history.insert_input_events(input_history.text_to_input_history_events("will ", "will"))
    input_history.insert_input_events(input_history.text_to_input_history_events("get ", "get"))
    input_history.insert_input_events(input_history.text_to_input_history_events("attention.", "attention"))

    assertion( "    Attempting to find 'will' should result in an exact match...", input_history.has_matching_phrase("will") == True)
    assertion( "    Attempting to find 'add' should result in a fuzzy match...", input_history.has_matching_phrase("add") == True)
    assertion( "    Attempting to find 'apt' should not result in a match...", input_history.has_matching_phrase("apt") == False)
    assertion( "    Attempting to find 'dad' should result in a fuzzy match...", input_history.has_matching_phrase("dad") == True)
    assertion( "    Attempting to find 'and' should not result in a match...", input_history.has_matching_phrase("and") == False)
suite.add_test(test_fuzzy_matching)

