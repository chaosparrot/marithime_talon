from ..cursor_position_tracker import CursorPositionTracker
from ..input_history import InputHistoryManager
from ..input_history_typing import InputHistoryEvent

input_history = InputHistoryManager()
input_history.insert_input_events(input_history.text_to_input_history_events("Insert ", "insert"))
input_history.insert_input_events(input_history.text_to_input_history_events("a ", "a"))
input_history.insert_input_events(input_history.text_to_input_history_events("new ", "new"))
input_history.insert_input_events(input_history.text_to_input_history_events("word.", "word"))

print( "Navigating between input events on a single line")
print( "    Navigating to the end of the first event...") 
keys = input_history.go_phrase("insert")
print( "        Expect history length to stay the same (4)", len(input_history.input_history) == 4)
cursor_index = input_history.cursor_position_tracker.get_cursor_index()
print( "        Expect cursor line index to be 0", cursor_index[0] == 0)
print( "        Expect cursor character index to be the end of the first word", cursor_index[1] == 11)
print( "    Navigating to the start of the first event...") 
keys = input_history.go_phrase("insert", "start") 
print( "        Expect left to be pressed 7 times", keys[0] == "left:7")
cursor_index = input_history.cursor_position_tracker.get_cursor_index() 
print( "        Expect cursor line index to be 0", cursor_index[0] == 0)
print( "        Expect cursor character index to be the start of the first word", cursor_index[1] == 18)
print( "    Navigating to the start of the third event...")
keys = input_history.go_phrase("new", "start")
print( "        Expect right to be pressed 9 times", keys[0] == "right:9")
cursor_index = input_history.cursor_position_tracker.get_cursor_index() 
print( "        Expect cursor line index to be 0", cursor_index[0] == 0)
print( "        Expect cursor character index to be the start of the third word", cursor_index[1] == 9)
print( "    Navigating to the end of the last event...") 
keys = input_history.go_phrase("word", "end")
print( "        Expect right to be pressed 9 times", keys[0] == "right:9")
cursor_index = input_history.cursor_position_tracker.get_cursor_index() 
print( "        Expect cursor line index to be 0", cursor_index[0] == 0)
print( "        Expect cursor character index to be the end of the sentence", cursor_index[1] == 0)
print( "    Navigating to a non-existing event...") 
keys = input_history.go_phrase("bee", "end")
print( "        Expect no keys to be pressed", keys is None)
cursor_index = input_history.cursor_position_tracker.get_cursor_index() 
print( "        Expect cursor index to be the same", cursor_index == (0, 0))

input_history.insert_input_events(input_history.text_to_input_history_events("\n", ""))
input_history.insert_input_events(input_history.text_to_input_history_events("Append ", "append"))
input_history.insert_input_events(input_history.text_to_input_history_events("a ", "a"))
input_history.insert_input_events(input_history.text_to_input_history_events("new ", "new"))
input_history.insert_input_events(input_history.text_to_input_history_events("sentence.", "sentence"))
input_history.insert_input_events(input_history.text_to_input_history_events("\n", ""))
input_history.insert_input_events(input_history.text_to_input_history_events("Add ", "add"))
input_history.insert_input_events(input_history.text_to_input_history_events("a ", "a"))
input_history.insert_input_events(input_history.text_to_input_history_events("final ", "final"))
input_history.insert_input_events(input_history.text_to_input_history_events("line.", "line"))
print( "Navigating between input events on multiple lines")
print( "    Navigating to the end of the second sentence...")
keys = input_history.go_phrase("sentence") 
print( "        Expect up to be pressed once", "up" in keys)
print( "        Expect end to be pressed at least once", "end" in keys)
cursor_index = input_history.cursor_position_tracker.get_cursor_index()
print( "        Expect cursor line index to be 1", cursor_index[0] == 1)
print( "        Expect cursor character index to be the end of the sentence", cursor_index[1] == 0)
print( "    Navigating to the end of the final sentence...")
keys = input_history.go_phrase("line")
print( "        Expect down to be pressed once", "down" in keys)
print( "        Expect end to be pressed at least once", "end" in keys)
cursor_index = input_history.cursor_position_tracker.get_cursor_index()
print( "        Expect cursor line index to be 2", cursor_index[0] == 2)
print( "        Expect cursor character index to be the end of the sentence", cursor_index[1] == 0)
print( "    Navigating to the end of the first event...")   
keys = input_history.go_phrase("insert")
print( "        Expect up to be pressed two times", "up:2" in keys)
print( "        Expect end to be pressed at least once", "end" in keys)
cursor_index = input_history.cursor_position_tracker.get_cursor_index()
print( "        Expect cursor line index to be 0", cursor_index[0] == 0)
print( "        Expect cursor character index to be the end of the first word", cursor_index[1] == 11)
print( "    Navigating to the end of the third word on the final sentence...")
keys = input_history.go_phrase("final")
cursor_index = input_history.cursor_position_tracker.get_cursor_index()
print( "        Expect down to be pressed two times", "down:2" in keys)
print( "        Expect end to be pressed at least once", "end" in keys)
print( "        Expect cursor line index to be 2", cursor_index[0] == 2)
print( "        Expect cursor character index to be the end of the third word", cursor_index[1] == 5)
print( "    Navigating to a non-existing event...") 
keys = input_history.go_phrase("bee", "end")
print( "        Expect no keys to be pressed", keys is None)
cursor_index = input_history.cursor_position_tracker.get_cursor_index()  
print( "        Expect cursor index to be the same", cursor_index == (2, 5)) 
