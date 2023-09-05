from ..cursor_position_tracker import CursorPositionTracker, _CURSOR_MARKER
from ..input_history import InputHistoryManager
from ..input_history_typing import InputHistoryEvent

input_history = InputHistoryManager()
input_history.insert_input_events(input_history.text_to_input_history_events("Insert a new sentence. \n", "insert a new sentence"))
input_history.insert_input_events(input_history.text_to_input_history_events("Insert a second sentence. \n", "insert a second sentence"))
input_history.insert_input_events(input_history.text_to_input_history_events("Insert a third sentence.", "insert a third sentence"))
input_history.cursor_position_tracker.text_history = """Insert a new sentence.
Insert a second """ + _CURSOR_MARKER + """sentence.
Insert a third sentence""" 

print( "Inserting in between input events")
print( "    Inserting text into a filled input history...")
input_history.insert_input_events(input_history.text_to_input_history_events("important ", "important"))
print( "        Expect history length to stay the same (3)", len(input_history.input_history) == 3)
cursor_index = input_history.cursor_position_tracker.get_cursor_index()
print( "        Expect cursor line index to be 1", cursor_index[0] == 1)
print( "        Expect cursor character index to be the same as before (9)", cursor_index[1] == 9, cursor_index)
input_index = input_history.determine_input_index()
print( "        Expect input index to be 1", input_index[0] == 1)
print( "        Expect input character index to be the length of the merged sentence minus the word sentence (28)", input_index[1] == 28 )
print( "        Expect the phrase to be merged", input_history.input_history[1].phrase == "insert a second important sentence" )
print( "    Inserting a new line into the filled input history...")
input_history.insert_input_events(input_history.text_to_input_history_events("\n", ""))
print( "        Expect history length to increase by one (4)", len(input_history.input_history) == 4)