from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite
from ...virtual_buffer.settings import VirtualBufferSettings
from ...virtual_buffer.input_history import InputEventType

def get_virtual_buffer() -> VirtualBuffer:
    settings = VirtualBufferSettings(live_checking=False)
    return VirtualBuffer(settings)

def get_filled_vb():
    vb = get_virtual_buffer()
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert ", "insert"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("a ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("sentence, ", "sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("that ", "that"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("will ", "will"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("have ", "have"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("words ", "words"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("compared ", "compared"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("to ", "to"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("the ", "the"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("previous ", "previous"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("sentence.", "sentence"))
    return vb

def test_looping_sentence(assertion):
    vb = get_filled_vb()
    assertion( "    Moving from the end to the buffer to the last occurrence of 'sentence'...")
    
    vb.input_history.add_event(InputEventType.NAVIGATION, ["sentence"])
    keys = vb.go_phrase("sentence", 'start', next_occurrence=False)
    assertion( "        Should go left until the last occurrence of sentence", keys[0] == "left:9")
    assertion( "    Repeating the search for 'sentence'...")
    keys = vb.go_phrase("sentence", 'start')
    assertion( "        Should go left until the first occurrence of sentence", keys[0] == "left:60")
    assertion( "    Repeating the search for 'sentence' again...")
    keys = vb.go_phrase("sentence", 'start')
    assertion( "        Should loop back to the last occurrence", keys[0] == "right:60")
    assertion( "    Repeating the search for 'sentence' once more...")
    keys = vb.go_phrase("sentence", 'start')
    assertion( "        Should loop back to the first occurrence", keys[0] == "left:60")

    vb = get_filled_vb()
    assertion( "    Moving from the end to the buffer to the last occurrence of 'sentence'...")
    keys = vb.go_phrase("sentence", 'end', next_occurrence=False)
    assertion( "        Should not move anywhere as we are already at the end", len(keys) == 0)
    assertion( "    Repeating the search for 'sentence'...")
    keys = vb.go_phrase("sentence", 'end')
    assertion( "        Should go left until the first occurrence of sentence", keys[0] == "left:59")
    assertion( "    Repeating the search for 'sentence' again...")
    keys = vb.go_phrase("sentence", 'end')
    assertion( "        Should loop back to the last occurrence", keys[0] == "right:59")
    assertion( "    Repeating the search for 'sentence' once more...")
    keys = vb.go_phrase("sentence", 'end')
    assertion( "        Should loop back to the first occurrence", keys[0] == "left:59")

def test_looping_new_sentence(assertion):
    vb = get_filled_vb()
    assertion( "    Moving from the end to the buffer to the last occurrence of 'new'...") 
    keys = vb.go_phrase("new", 'end', next_occurrence=False)
    assertion( "        Should move to the left until we have reached the word new", keys[0] == "left:40")
    assertion( "    Searching for 'sentence'...")
    keys = vb.go_phrase("sentence", 'end', next_occurrence=False)
    assertion( "        Should go left until the first occurrence of sentence, because it comes before the current caret", keys[0] == "left:19")
    assertion( "    Repeating the search for 'sentence' again...")
    keys = vb.go_phrase("sentence", 'end')
    assertion( "        Should loop back to the last occurrence", keys[0] == "right:59")

def test_looping_to(assertion):
    vb = get_filled_vb()
    assertion( "    Moving from the end to the buffer to the last occurrence of 'to'...") 
    vb.input_history.add_event(InputEventType.NAVIGATION, ["to"])
    keys = vb.go_phrase("to", 'end')
    assertion( "        Should move to the left until we have reached the word 'to'", keys[0] == "left:22")
    assertion( "    Repeating the search for 'to' again...")
    keys = vb.go_phrase("to", 'end')
    assertion( "        Should not move the caret as there is only one option", len(keys) == 0)

suite = create_test_suite("Using a filled virtual buffer which contains duplicates of certain words used for testing looping")
suite.add_test(test_looping_sentence)
suite.add_test(test_looping_new_sentence)
suite.add_test(test_looping_to)