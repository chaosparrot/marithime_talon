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
    ihm.insert_input_events(text_to_input_history_events("sentence.", "sentence"))
    return ihm

def test_multiple_match_consistent(assertion):
    input_history = get_filled_ihm()
    assertion( "Using a filled input history which contains duplicates of certain words")
    input_history.apply_key("left:6")    
    assertion( "    Moving from the center of the word 'sentence' and finding 'sentence'...") 
    keys = input_history.go_phrase("sentence", 'start')
    assertion( "        Should go left until the last occurrence of sentence", keys[0] == "left:3")

    input_history = get_filled_ihm()
    input_history.apply_key("left:6")
    assertion( "    Moving from the center of the word 'sentence' and finding 'sentence'...") 
    keys = input_history.go_phrase("sentence", 'end')
    assertion( "        Should go right until the last occurrence of sentence", keys[0] == "right:6")

    input_history = get_filled_ihm()
    input_history.apply_key("left:9 right:9") 
    assertion( "    Moving from the end of the word 'sentence' and finding 'sentence'...") 
    keys = input_history.go_phrase("sentence", 'start')
    assertion( "        Should go left until the last occurrence of sentence", keys[0] == "left:9")

    input_history = get_filled_ihm()
    input_history.apply_key("left:9")
    assertion( "    Moving from the start of the word 'sentence' and finding 'sentence'...")
    keys = input_history.go_phrase("sentence", 'end')
    assertion( "        Should go right until the last occurrence of sentence", keys[0] == "right:9")

suite = create_test_suite("Using a filled input history which contains duplicates of certain words")
suite.add_test(test_multiple_match_consistent)