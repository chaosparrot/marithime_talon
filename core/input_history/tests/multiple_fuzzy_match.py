from ..cursor_position_tracker import CursorPositionTracker, _CURSOR_MARKER
from ..input_history import InputHistoryManager
from ..input_history_typing import InputHistoryEvent

def get_filled_ihm():
    ihm = InputHistoryManager()
    ihm.insert_input_events(ihm.text_to_input_history_events("Insert ", "insert"))
    ihm.insert_input_events(ihm.text_to_input_history_events("a ", "a"))
    ihm.insert_input_events(ihm.text_to_input_history_events("new ", "new"))
    ihm.insert_input_events(ihm.text_to_input_history_events("sentence, ", "sentence"))
    ihm.insert_input_events(ihm.text_to_input_history_events("that ", "that"))
    ihm.insert_input_events(ihm.text_to_input_history_events("will ", "will"))
    ihm.insert_input_events(ihm.text_to_input_history_events("have ", "have"))
    ihm.insert_input_events(ihm.text_to_input_history_events("new ", "new"))
    ihm.insert_input_events(ihm.text_to_input_history_events("words ", "words"))
    ihm.insert_input_events(ihm.text_to_input_history_events("compared ", "compared"))
    ihm.insert_input_events(ihm.text_to_input_history_events("to ", "to"))
    ihm.insert_input_events(ihm.text_to_input_history_events("the ", "the"))
    ihm.insert_input_events(ihm.text_to_input_history_events("previous ", "previous"))
    ihm.insert_input_events(ihm.text_to_input_history_events("two ", "two"))
    ihm.insert_input_events(ihm.text_to_input_history_events("sentences.", "sentences"))
    return ihm

input_history = get_filled_ihm()
print( "Using a filled input history which contains homophones of certain words")
print( "    Moving from the end of the word 'sentences' searching for 'to'...") 
keys = input_history.go_phrase("to", 'start')
print( "        Should go left until the word 'two' is found", keys[0] == "left:14" )
print( "    Searching for 'to' again...") 
keys = input_history.go_phrase("to", 'start')
print( "        Should go left until the word 'to' is found", keys[0] == "left:16" )
keys = input_history.go_phrase("wil", 'end')
print( "    Searching for 'wil', which isn't available directly...") 
print( "        Should go left until the word 'will' is found", keys[0] == "left:24" )