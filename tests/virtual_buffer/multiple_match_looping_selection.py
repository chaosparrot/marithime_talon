from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.caret_tracker import _CARET_MARKER
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite
from ...virtual_buffer.settings import VirtualBufferSettings

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
    vb.insert_tokens(text_to_virtual_buffer_tokens("and ", "and"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("phrases ", "phrases"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("compared ", "compared"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("to ", "to"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("the ", "the"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("previous ", "previous"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("sentence.", "sentence"))
    return vb

def test_looping_new_from_end(assertion):
    vb = get_filled_vb()
    assertion( "    Moving from the end to the buffer to selecting the first occurrence of 'new'...") 
    keys = vb.select_phrases(["new"])
    assertion( "        Should move to the left until we have reached the word 'new'", keys[0] == "left:46")
    assertion( "        Should move to the right until we have reached the end of the word 'new'", keys[1] == "shift-right:4")
    assertion( "    Repeating the search for 'new' again...")
    keys = vb.select_phrases(["new"])
    assertion( "        Should move to the left until we have reached the second occurrence", keys[1] == "left:14")
    assertion( "        Should move to the right until we have reached the end of the word 'new'", keys[2] == "shift-right:4")
    assertion( "    Repeating the search for 'new' a second time...")
    keys = vb.select_phrases(["new"])
    assertion( "        Should move to the left until we have reached the third occurrence", keys[1] == "left:29")
    assertion( "        Should move to the right until we have reached the end of the word 'new'", keys[2] == "shift-right:4")
    assertion( "    Repeating the search for 'new' a final time to loop back around...")
    keys = vb.select_phrases(["new"])
    assertion( "        Should move to the right until we have reached the first occurrence", keys[1] == "right:39")
    assertion( "        Should move to the right until we have reached the end of the word 'new'", keys[2] == "shift-right:4")
    assertion( "    Repeating the search for 'new' again...")
    keys = vb.select_phrases(["new"]) 
    assertion( "        Should move to the left until we have reached the second occurrence once more", keys[1] == "left:14")
    assertion( "        Should move to the right until we have reached the end of the word 'new'", keys[2] == "shift-right:4") 

def test_looping_new_from_start(assertion):
    vb = get_filled_vb()
    vb.caret_tracker.text_buffer = _CARET_MARKER + vb.caret_tracker.text_buffer.replace(_CARET_MARKER, "")
    assertion( "    Moving from the start to the buffer to selecting the first occurrence of 'new'...") 
    keys = vb.select_phrases(["new"])
    assertion( "        Should move to the right until we have reached the word 'new'", keys[0] == "right:9")
    assertion( "        Should move to the right until we have reached the end of the word 'new'", keys[1] == "shift-right:4")
    assertion( "    Repeating the search for 'new' again...")
    keys = vb.select_phrases(["new"])
    assertion( "        Should move to the left until we have reached the second occurrence", keys[1] == "right:25")
    assertion( "        Should move to the right until we have reached the end of the word 'new'", keys[2] == "shift-right:4")
    assertion( "    Repeating the search for 'new' a second time...")
    keys = vb.select_phrases(["new"])
    assertion( "        Should move to the left until we have reached the third occurrence", keys[1] == "right:10")
    assertion( "        Should move to the right until we have reached the end of the word 'new'", keys[2] == "shift-right:4")
    assertion( "    Repeating the search for 'new' a final time to loop back around...")
    keys = vb.select_phrases(["new"])
    assertion( "        Should move to the left until we have reached the first occurrence", keys[1] == "left:43")
    assertion( "        Should move to the right until we have reached the end of the word 'new'", keys[2] == "shift-right:4")
    assertion( "    Repeating the search for 'new' again...")
    keys = vb.select_phrases(["new"])
    assertion( "        Should move to the right until we have reached the second occurrence once more", keys[1] == "right:25")
    assertion( "        Should move to the right until we have reached the end of the word 'new'", keys[2] == "shift-right:4")

suite = create_test_suite("Using a filled virtual buffer which contains duplicates of certain words used for testing looping multiple times")

suite.add_test(test_looping_new_from_end) 
suite.add_test(test_looping_new_from_start)