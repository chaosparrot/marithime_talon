from ..input_history import InputHistoryManager
from ..input_history_typing import InputHistoryEvent
from ..input_indexer import InputIndexer
from ...utils.test import create_test_suite

input_indexer = InputIndexer()

def test_index_single_sentence(assertion):
    sentence_input_events = input_indexer.index_text("This is a test.")
    assertion( "Indexing the sentence 'This is a test.'...")
    assertion("    should consist of 4 input events", len(sentence_input_events) == 4)
    assertion("    should only be on one line", len([event for event in sentence_input_events if event.line_index == 0]) == len(sentence_input_events))
    assertion("    The first event should be 'This '", sentence_input_events[0].text == 'This ')
    assertion("    The first event should be be 10 characters from the end on 'This is a test.'", sentence_input_events[0].index_from_line_end == 10)
    assertion("    The second event should be 'is '", sentence_input_events[1].text == 'is ')
    assertion("    The second event should be be 7 characters from the end on 'This is a test.'", sentence_input_events[1].index_from_line_end == 7)
    assertion("    The third event should be 'a '", sentence_input_events[2].text == 'a ')
    assertion("    The third event should be be 5 characters from the end on 'This is a test.'", sentence_input_events[2].index_from_line_end == 5)
    assertion("    The last event should be 'test.'", sentence_input_events[2].text == 'test.')
    assertion("    The last event should be be 0 characters from the end on 'This is a test.'", sentence_input_events[2].index_from_line_end == 0)
    #assertion(sentence_input_events, False)

def test_index_multiple_sentences(assertion):
    sentence_input_events = input_indexer.index_text("""This is the first sentence.
And this is a second sentence!""")
    assertion( "Indexing the sentence 'This is the first sentence.' followed by 'And this is a second sentence!'...")
    assertion("    should consist of 11 input events", len(sentence_input_events) == 11)
    assertion("    should have 4 events on the first line", len([event for event in sentence_input_events if event.line_index == 0]) == 4)
    assertion("    should have 4 events on the first line", len([event for event in sentence_input_events if event.line_index == 1]) == 7)
    #assertion(sentence_input_events, False)

suite = create_test_suite("Text indexation")
suite.add_test(test_index_single_sentence)
suite.add_test(test_index_multiple_sentences)
suite.run()