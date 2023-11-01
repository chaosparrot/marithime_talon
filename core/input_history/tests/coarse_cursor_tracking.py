from ..cursor_position_tracker import _CURSOR_MARKER
from ..input_history import InputHistoryManager
from ...utils.test import create_test_suite

def coarse_cursor_tracker_splitting(assertion):
    input_history = InputHistoryManager()
    input_history.insert_input_events(input_history.text_to_input_history_events("Insert a new sentence. \n", "insert a new sentence"))
    input_history.insert_input_events(input_history.text_to_input_history_events("Insert a second sentence. \n", "insert a second sentence"))
    input_history.insert_input_events(input_history.text_to_input_history_events("Insert a third sentence.", "insert a third sentence"))
    input_history.cursor_position_tracker.text_history = """Insert a new sentence. 
    Insert a second """ + _CURSOR_MARKER + """sentence. 
    Insert a third sentence."""

    assertion( "Cursor tracking coarse splitting" )
    cpt = input_history.cursor_position_tracker 
    items = cpt.split_string_with_punctuation("Testing")
    assertion( "    Expect single word length to be 1", len(items) == 1 )
    items = cpt.split_string_with_punctuation("Testing items")
    assertion( "    Expect double word length to be 2", len(items) == 2 )
    items = cpt.split_string_with_punctuation("Testing  items")
    assertion( "    Expect double word, with two spaces in between length to be 2", len(items) == 2 )
    items = cpt.split_string_with_punctuation("Testing-items")
    assertion( "    Expect word with dashes length to be 2", len(items) == 2 )
    items = cpt.split_string_with_punctuation("Words... don't come easy")
    assertion( "    Expect 'Words... don't come easy' length to be 5", len(items) == 5 )
    assertion( "    Expect 'Words' to be the first split", items[0] == "Words" )
    assertion( "    Expect 'don' to be the second split", items[1] == "don" )
    items = cpt.split_string_with_punctuation("""This is a 
                                            split sentence. """)
    assertion( "    Expect a sentence with new lines to have a length of 5", len(items) == 5 )

def coarse_cursor_tracking_single_line(assertion):
    input_history = InputHistoryManager()
    input_history.insert_input_events(input_history.text_to_input_history_events("Insert a new sentence. \n", "insert a new sentence"))
    input_history.insert_input_events(input_history.text_to_input_history_events("Insert a second sentence. \n", "insert a second sentence"))
    input_history.insert_input_events(input_history.text_to_input_history_events("Insert a third sentence.", "insert a third sentence"))
    input_history.cursor_position_tracker.text_history = """Insert a new sentence. 
    Insert a second """ + _CURSOR_MARKER + """sentence. 
    Insert a third sentence."""

    assertion( "Coarse cursor tracking with a filled input history")
    assertion( "    Move a word left...")
    input_history.apply_key("ctrl-left")
    cursor_index = input_history.cursor_position_tracker.get_cursor_index(True)
    assertion( "        Expect cursor line index to be 1", cursor_index[0] == 1)
    assertion( "        Expect coarse character index to be before the word second (17)", cursor_index[1] == 17)
    assertion( "    Moving a word right...")
    input_history.apply_key("ctrl-right")
    cursor_index = input_history.cursor_position_tracker.get_cursor_index(True)
    assertion( "        Expect cursor line index to be 1", cursor_index[0] == 1)
    assertion( "        Expect coarse character index to be after the word second (11)", cursor_index[1] == 11)
    assertion( "    Moving two words to the left...")
    input_history.apply_key("ctrl-left:2")
    cursor_index = input_history.cursor_position_tracker.get_cursor_index(True)
    assertion( "        Expect cursor line index to be 1", cursor_index[0] == 1)
    assertion( "        Expect coarse character index to be after the word a (7)", cursor_index[1] == 19)
    assertion( "    Moving three words to the right...")
    input_history.apply_key("ctrl-right:3")
    cursor_index = input_history.cursor_position_tracker.get_cursor_index(True)
    assertion( "        Expect cursor line index to be 1", cursor_index[0] == 1)
    assertion( "        Expect coarse character index to be after the word sentence (1)", cursor_index[1] == 1)
    assertion( "    Moving left twice...")
    input_history.apply_key("left:2")
    cursor_index = input_history.cursor_position_tracker.get_cursor_index(True)
    assertion( "        Expect cursor line index to be 1", cursor_index[0] == 1)
    assertion( "        Expect coarse character index to be two characters inside the word sentence (3)", cursor_index[1] == 3)
    assertion( "    Moving right twice...")
    input_history.apply_key("right:2")
    cursor_index = input_history.cursor_position_tracker.get_cursor_index(True)
    assertion( "        Expect cursor line index to be 1", cursor_index[0] == 1)
    assertion( "        Expect coarse character index to be after the word sentence (1)", cursor_index[1] == 1)
    assertion( "    Moving one more word to the right to simulate a line end transfer...")
    input_history.apply_key("ctrl-shift-right")
    cursor_index = input_history.cursor_position_tracker.get_cursor_index(True)
    assertion( "        Expect cursor line index to be lost", cursor_index[0] == -1 )
    assertion( "    Moving one more word to the left to simulate a line end transfer...")
    input_history.apply_key("ctrl-shift-left")
    cursor_index = input_history.cursor_position_tracker.get_cursor_index(True)
    assertion( "        Expect cursor line index to be lost", cursor_index[0] == -1 )
 
def coarse_cursor_tracking_multi_line(assertion):
    input_history = InputHistoryManager()
    input_history.insert_input_events(input_history.text_to_input_history_events("Insert a new sentence. \n", "insert a new sentence"))
    input_history.insert_input_events(input_history.text_to_input_history_events("Insert a second sentence. \n", "insert a second sentence"))
    input_history.insert_input_events(input_history.text_to_input_history_events("Insert a third sentence.", "insert a third sentence"))
    input_history.cursor_position_tracker.text_history = """Insert a new sentence. 
Insert a second """ + _CURSOR_MARKER + """sentence. 
Insert a third sentence."""
    assertion( "    Pressing up to go to the first sentence...")
    input_history.apply_key("up")
    cursor_index = input_history.cursor_position_tracker.get_cursor_index(True)
    assertion( "        Expect cursor line index to be 0", cursor_index[0] == 0)
    assertion( "    Pressing down twice to go to the third sentence...")
    input_history.apply_key("down:2") 
    cursor_index = input_history.cursor_position_tracker.get_cursor_index(True) 
    assertion( "        Expect cursor line index to be 2", cursor_index[0] == 2)
    assertion( "    Pressing home to go to the start of the third sentence...")
    input_history.apply_key("home")
    cursor_index = input_history.cursor_position_tracker.get_cursor_index(True)  
    assertion( "        Expect cursor line index to be 2", cursor_index[0] == 2)
    assertion( "        Expect coarse character index to be before the word insert (24)", cursor_index[1] == 24)

suite = create_test_suite("Coarse cursor tracking")
suite.add_test(coarse_cursor_tracker_splitting)
suite.add_test(coarse_cursor_tracking_single_line)
suite.add_test(coarse_cursor_tracking_multi_line)