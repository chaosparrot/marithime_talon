from ..input_history import InputHistoryManager
from ..input_indexer import text_to_input_history_events
from ...utils.test import create_test_suite

def get_filled_ihm():
    ihm = InputHistoryManager()
    ihm.insert_input_events(text_to_input_history_events("Insert ", "insert"))
    ihm.insert_input_events(text_to_input_history_events("a ", "a"))
    ihm.insert_input_events(text_to_input_history_events("new ", "new"))
    ihm.insert_input_events(text_to_input_history_events("sentence, ", "sentence"))
    ihm.insert_input_events(text_to_input_history_events("that ", "that"))
    ihm.insert_input_events(text_to_input_history_events("will ", "will"))
    ihm.insert_input_events(text_to_input_history_events("have ", "have"))
    ihm.insert_input_events(text_to_input_history_events("new ", "new"))
    ihm.insert_input_events(text_to_input_history_events("words ", "words"))
    ihm.insert_input_events(text_to_input_history_events("compared ", "compared"))
    ihm.insert_input_events(text_to_input_history_events("to ", "to"))
    ihm.insert_input_events(text_to_input_history_events("the ", "the"))
    ihm.insert_input_events(text_to_input_history_events("previous ", "previous"))
    ihm.insert_input_events(text_to_input_history_events("two ", "two"))
    ihm.insert_input_events(text_to_input_history_events("sentences.", "sentences"))
    return ihm

def test_multiple_fuzzy_matching(assertion):
    input_history = get_filled_ihm()
    assertion( "    Moving from the end of the word 'sentences' searching for 'to'...") 
    keys = input_history.go_phrase("to", 'start')
    assertion( "        Should go left until the word 'two' is found", keys[0] == "left:14" )
    assertion( "    Searching for 'to' again...") 
    keys = input_history.go_phrase("to", 'start')
    assertion( "        Should go left until the word 'to' is found", keys[0] == "left:16" )
    keys = input_history.go_phrase("wil", 'end')
    assertion( "    Searching for 'wil', which isn't available directly...") 
    assertion( "        Should go left until the word 'will' is found", keys[0] == "left:24" )

suite = create_test_suite("Using a filled input history which contains homophones of certain words")
suite.add_test(test_multiple_fuzzy_matching)