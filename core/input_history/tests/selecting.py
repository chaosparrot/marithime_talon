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

print( "Selecting characters in the input history")
print( "    Selecting a single character to the left...")
input_history.apply_key("shift:down left shift:up")
print( "        Expect history length to stay the same (3)", len(input_history.input_history) == 3)
cursor_index = input_history.cursor_position_tracker.get_cursor_index()
print( "        Expect cursor line index to be 1", cursor_index[0] == 1)
print( "        Expect cursor character index to be one less than before (11)", cursor_index[1] == 11)
print( "        Expect selection detected", input_history.is_selecting())
print( "    Moving the cursor to the right while selecting...")
input_history.apply_key("shift:down right shift:up")
print( "        Expect history length to stay the same (3)", len(input_history.input_history) == 3)
cursor_index = input_history.cursor_position_tracker.get_cursor_index()
print( "        Expect cursor line index to be 1", cursor_index[0] == 1)
print( "        Expect cursor character index to be one more than before (10)", cursor_index[1] == 10)
print( "        Expect no selection detected", input_history.is_selecting() == False)
print( "    Selecting 10 characters to the left...")
input_history.apply_key("shift:down left:10 shift:up")
print( "        Expect history length to stay the same (3)", len(input_history.input_history) == 3)
cursor_index = input_history.cursor_position_tracker.get_cursor_index()
print( "        Expect cursor line index to be 1", cursor_index[0] == 1)
print( "        Expect cursor character index to be ten less than before (20)", cursor_index[1] == 20)
print( "        Expect a selection detected", input_history.is_selecting() == True)
print( "    Move one character to the left without selecting...")   
input_history.apply_key("left")   
print( "        Expect history length to stay the same (3)", len(input_history.input_history) == 3)
cursor_index = input_history.cursor_position_tracker.get_cursor_index()
print( "        Expect cursor line index to be 1", cursor_index[0] == 1)
print( "        Expect cursor character index to not have changed (20)", cursor_index[1] == 20)
print( "        Expect no selection detected", input_history.is_selecting() == False)
print( "    Selecting 10 characters to the right and moving one to the left...")
input_history.apply_key("shift:down right:10 shift:up left")  
print( "        Expect history length to stay the same (3)", len(input_history.input_history) == 3)
cursor_index = input_history.cursor_position_tracker.get_cursor_index()
print( "        Expect cursor line index to be 1", cursor_index[0] == 1)
print( "        Expect cursor character index to be at the same place as the start of the selection (20)", cursor_index[1] == 20)
print( "        Expect no selection detected", input_history.is_selecting() == False)
print( "    Selecting 10 characters to the right and moving one to the right...")
input_history.apply_key("shift:down right:10 shift:up right")
print( "        Expect history length to stay the same (3)", len(input_history.input_history) == 3)
cursor_index = input_history.cursor_position_tracker.get_cursor_index()
print( "        Expect cursor line index to be 1", cursor_index[0] == 1)
print( "        Expect cursor character index to be at the end of the selection (10)", cursor_index[1] == 10)
print( "        Expect no selection detected", input_history.is_selecting() == False)
print( "    Selecting 10 characters to the left and moving one to the right...")
input_history.apply_key("shift:down left:10 shift:up right")
print( "        Expect history length to stay the same (3)", len(input_history.input_history) == 3)
cursor_index = input_history.cursor_position_tracker.get_cursor_index()
print( "        Expect cursor line index to be 1", cursor_index[0] == 1)
print( "        Expect cursor character index to stay the same as the start of the selection (10)", cursor_index[1] == 10)
print( "        Expect no selection detected", input_history.is_selecting() == False)   