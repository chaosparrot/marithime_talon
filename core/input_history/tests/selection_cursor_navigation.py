from ..input_history import InputHistoryManager
from ..input_indexer import text_to_input_history_events
from ...utils.test import create_test_suite

def test_track_selection_cursor(assertion):
    input_history = InputHistoryManager()
    input_history.insert_input_events(text_to_input_history_events("Insert ", "insert"))
    input_history.insert_input_events(text_to_input_history_events("a ", "a"))
    input_history.insert_input_events(text_to_input_history_events("new ", "new"))
    input_history.insert_input_events(text_to_input_history_events("sentence.", "sentence"))

    assertion( "Selecting characters in the input history")
    assertion( "    Selecting a single character to the left and then moving to the first character...")
    input_history.apply_key("shift:down left shift:up")
    keys = input_history.navigate_to_event(input_history.find_event_by_phrase("insert"), 0)
    assertion( "        Should move the cursor to the left one extra time compared to non-selected text", keys[0] == "left" and keys[1] == "left:21")
    assertion( "    Selecting five characters to the right and then moving to the first character...")
    input_history.apply_key("shift:down right:5 shift:up")
    keys = input_history.navigate_to_event(input_history.find_event_by_phrase("insert"), 0)
    assertion( "        Should move the cursor to the left one time as the selection started on the first character", keys[0] == "left" and len(keys) == 1)
    assertion( "    Selecting five characters to the right and then moving to the first character of the final word...")
    input_history.apply_key("shift:down right:5 shift:up")
    keys = input_history.navigate_to_event(input_history.find_event_by_phrase("sentence"), 0)
    assertion( "        Should move the cursor to the right one time as the selection started on the first character", keys[0] == "right" and keys[1] == "right:8")
    assertion( "    Selecting one character to the left and then moving to the first character of the final word...")
    input_history.apply_key("shift:down left shift:up")
    keys = input_history.navigate_to_event(input_history.find_event_by_phrase("sentence"), 0)
    assertion( "        Should move the cursor to the right one time as the selection started on the first character", keys[0] == "right" and len(keys) == 1)

suite = create_test_suite("Selection tracking cursor navigation")
suite.add_test(test_track_selection_cursor)