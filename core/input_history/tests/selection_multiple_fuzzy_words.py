from ..cursor_position_tracker import CursorPositionTracker, _CURSOR_MARKER
from ..input_history import InputHistoryManager
from ..input_history_typing import InputHistoryEvent
from time import perf_counter

input_history = InputHistoryManager()
input_events = []
input_events.extend(input_history.text_to_input_history_events("Insert ", "insert"))
input_events.extend(input_history.text_to_input_history_events("a ", "a"))
input_events.extend(input_history.text_to_input_history_events("new ", "new"))
input_events.extend(input_history.text_to_input_history_events("sentence.", "sentence"))

input_history.insert_input_events(input_events)

print( "Selecting a whole mispronounced phrase in the input history")  
print( "    Starting from the end and searching for 'Insert an'...") 
keys = input_history.select_phrases(["insert", "an"])
print( "        Should have the text 'Insert a ' selected", input_history.cursor_position_tracker.get_selection_text() == 'Insert a ')
print( "        Should go left 22 times to go to the start of 'Insert'", keys[0] == "left:22")
print( "        Should then hold down shift", keys[1] == "shift:down")
print( "        And then go right until 'a ' is selected", keys[2] == "right:9")
keys = input_history.select_phrases(["insert", "new"])
print( "    Starting from the current selection and searching for 'Insert new' ( forgetting 'a' )...")
print( "        Should have the text 'Insert a new ' selected", input_history.cursor_position_tracker.get_selection_text() == 'Insert a new ')
print( "        Should go left once to go to the start of 'Insert'", keys[0] == "left")
print( "        Should then hold down shift", keys[1] == "shift:down")
print( "        And then go right until 'new ' is selected", keys[2] == "right:13")
print( "    Starting from the current selection and searching for 'an new'...")
keys = input_history.select_phrases(["an", "new"])
print( "        Should have the text 'a new ' selected", input_history.cursor_position_tracker.get_selection_text() == 'a new ')
print( "        Should go right once to go to the end of 'Insert a new '", keys[0] == "right")
print( "        Should then go left 6 times to go to the start of 'a'", keys[1] == "left:6")
print( "        Should then hold down shift", keys[2] == "shift:down")
print( "        And then go right until 'new ' is selected", keys[3] == "right:6")
keys = input_history.select_phrases(["a", "nyou", "sentences"])
print( "    Starting from the current selection and searching for 'a nyou sentences'...")
print( "        Should have the text 'a new sentence.' selected", input_history.cursor_position_tracker.get_selection_text() == 'a new sentence.')
print( "        Should go left once to go to the start of 'a '", keys[0] == "left")
print( "        Should then hold down shift", keys[1] == "shift:down")
print( "        Should then go right 15 times to go to the end of 'sentence'", keys[2] == "right:15" ) 
 