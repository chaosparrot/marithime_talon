from ..input_history import InputHistoryManager
from ..input_indexer import text_to_input_history_events
from ...utils.test import create_test_suite

def test_selecting_multiple_fuzzy_words(assertion):
    input_history = InputHistoryManager()
    input_events = []
    input_events.extend(text_to_input_history_events("Insert ", "insert"))
    input_events.extend(text_to_input_history_events("a ", "a"))
    input_events.extend(text_to_input_history_events("new ", "new"))
    input_events.extend(text_to_input_history_events("sentence.", "sentence"))

    input_history.insert_input_events(input_events)

    assertion( "    Starting from the end and searching for 'Insert an'...") 
    keys = input_history.select_phrases(["insert", "an"])
    assertion( "        Should have the text 'Insert a ' selected", input_history.cursor_position_tracker.get_selection_text() == 'Insert a ')
    assertion( "        Should go left 22 times to go to the start of 'Insert'", keys[0] == "left:22")
    assertion( "        Should then hold down shift", keys[1] == "shift:down")
    assertion( "        And then go right until 'a ' is selected", keys[2] == "right:9")
    keys = input_history.select_phrases(["insert", "new"])
    assertion( "    Starting from the current selection and searching for 'Insert new' ( forgetting 'a' )...")
    assertion( "        Should have the text 'Insert a new ' selected", input_history.cursor_position_tracker.get_selection_text() == 'Insert a new ')
    assertion( "        Should go left once to go to the start of 'Insert'", keys[0] == "left")
    assertion( "        Should then hold down shift", keys[1] == "shift:down")
    assertion( "        And then go right until 'new ' is selected", keys[2] == "right:13")
    assertion( "    Starting from the current selection and searching for 'an new'...")
    keys = input_history.select_phrases(["an", "new"])
    assertion( "        Should have the text 'a new ' selected", input_history.cursor_position_tracker.get_selection_text() == 'a new ')
    assertion( "        Should go right once to go to the end of 'Insert a new '", keys[0] == "right")
    assertion( "        Should then go left 6 times to go to the start of 'a'", keys[1] == "left:6")
    assertion( "        Should then hold down shift", keys[2] == "shift:down")
    assertion( "        And then go right until 'new ' is selected", keys[3] == "right:6")
    keys = input_history.select_phrases(["a", "nyou", "sentences"])
    assertion( "    Starting from the current selection and searching for 'a nyou sentences'...")
    assertion( "        Should have the text 'a new sentence.' selected", input_history.cursor_position_tracker.get_selection_text() == 'a new sentence.')
    assertion( "        Should go left once to go to the start of 'a '", keys[0] == "left")
    assertion( "        Should then hold down shift", keys[1] == "shift:down")
    assertion( "        Should then go right 15 times to go to the end of 'sentence'", keys[2] == "right:15" )

suite = create_test_suite("Selecting a whole mispronounced phrase in the input history")
suite.add_test(test_selecting_multiple_fuzzy_words)