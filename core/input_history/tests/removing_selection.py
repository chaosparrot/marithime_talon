from ..cursor_position_tracker import CursorPositionTracker, _CURSOR_MARKER
from ..input_history import InputHistoryManager
from ..input_history_typing import InputHistoryEvent

input_history = InputHistoryManager()
input_history.insert_input_events(input_history.text_to_input_history_events("Insert a new sentence. \n", "insert a new sentence"))
input_history.insert_input_events(input_history.text_to_input_history_events("Insert a second sentence. \n", "insert a second sentence"))
input_history.insert_input_events(input_history.text_to_input_history_events("Insert a third sentence.", "insert a third sentence"))
input_history.cursor_position_tracker.text_history = """Insert a new sentence. 
Insert a second """ + _CURSOR_MARKER + """sentence. 
Insert a third sentence."""

print( "With a filled input history")
print( "    Selecting a single character to the left and remove it...")
input_history.apply_key("shift:down left shift:up backspace")
print( "        Expect history length to stay the same (3)", len(input_history.input_history) == 3)
cursor_index = input_history.cursor_position_tracker.get_cursor_index() 
print( "        Expect cursor line index to be 1", cursor_index[0] == 1)
print( "        Expect cursor character index to be the same as before (10)", cursor_index[1] == 10)
print( "        Expect no selection detected", input_history.is_selecting() == False)
print( "        Expect text to be merged", input_history.input_history[1].text == "Insert a secondsentence. \n")
print( "        Expect phrase to be merged", input_history.input_history[1].phrase == "insert a secondsentence")
print( "    Selecting three characters to the right and remove them...")
input_history.apply_key("shift:down right:3 shift:up delete")
print( "        Expect history length to stay the same (3)", len(input_history.input_history) == 3)
cursor_index = input_history.cursor_position_tracker.get_cursor_index() 
print( "        Expect cursor line index to be 1", cursor_index[0] == 1)
print( "        Expect cursor character index to be the three less than before (7)", cursor_index[1] == 7)
print( "        Expect no selection detected", input_history.is_selecting() == False)
print( "        Expect text to be merged", input_history.input_history[1].text == "Insert a secondtence. \n")
print( "        Expect phrase to be merged", input_history.input_history[1].phrase == "insert a secondtence")