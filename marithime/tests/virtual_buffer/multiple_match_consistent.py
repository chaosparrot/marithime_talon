from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite

def get_filled_vb():
    vb = VirtualBuffer()
    vb.caret_tracker.system = "Windows"
    vb.caret_tracker.is_macos = False
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

def test_multiple_match_consistent(assertion):
    vb = get_filled_vb()
    assertion( "Using a filled virtual buffer which contains duplicates of certain words")
    vb.apply_key("left:6")    
    assertion( "    Moving from the center of the word 'sentence' and finding 'sentence'...") 
    keys = vb.go_phrase("sentence", 'start')
    assertion( "        Should go left until the last occurrence of sentence", keys[0] == "left:3")

    vb = get_filled_vb()
    vb.apply_key("left:6")
    assertion( "    Moving from the center of the word 'sentence' and finding 'sentence'...") 
    keys = vb.go_phrase("sentence", 'end')
    assertion( "        Should go right until the last occurrence of sentence", keys[0] == "right:6")

    vb = get_filled_vb()
    vb.apply_key("left:9 right:9") 
    assertion( "    Moving from the end of the word 'sentence' and finding 'sentence'...") 
    keys = vb.go_phrase("sentence", 'start')
    assertion( "        Should go left until the last occurrence of sentence", keys[0] == "left:9")

    vb = get_filled_vb()
    vb.apply_key("left:9")
    assertion( "    Moving from the start of the word 'sentence' and finding 'sentence'...")
    keys = vb.go_phrase("sentence", 'end')
    assertion( "        Should go right until the last occurrence of sentence", keys[0] == "right:9")

suite = create_test_suite("Using a filled virtual buffer which contains duplicates of certain words which can be consistently navigated towards")
suite.add_test(test_multiple_match_consistent)