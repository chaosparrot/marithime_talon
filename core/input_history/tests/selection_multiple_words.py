from ..cursor_position_tracker import CursorPositionTracker, _CURSOR_MARKER
from ..input_history import InputHistoryManager
from ..input_history_typing import InputHistoryEvent
from time import perf_counter

input_history = InputHistoryManager()
for i in range(0, 1000):
    input_history.insert_input_events(input_history.text_to_input_history_events("Insert ", "insert"))
    input_history.insert_input_events(input_history.text_to_input_history_events("a ", "a"))
    input_history.insert_input_events(input_history.text_to_input_history_events("new ", "new"))
    input_history.insert_input_events(input_history.text_to_input_history_events("sentence.", "sentence"))
    
print( "Selecting a whole phrase in the input history")  
print( "    Starting from the end and searching for 'Insert a'...") 
print( perf_counter() ) 
keys = input_history.select_phrases(["insert", "an", "new"])     
print( "SELECTION='" + input_history.cursor_position_tracker.get_selection_text() + "'" ) 
print( perf_counter() )
#print( keys ) 
#print( "    Starting from the end and searching for 'Insert a'...")      
#print( "    Starting from the end and searching for 'Insert a new'...")
#print( "    Starting from the end and searching for 'Insert new'...")
#print( "    Starting from the end and searching for 'a new sentence'...")