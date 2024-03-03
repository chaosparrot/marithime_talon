from ..caret_tracker import _CARET_MARKER
from ..buffer import VirtualBuffer
from ...utils.test import create_test_suite
from ..indexer import text_to_virtual_buffer_tokens

def exact_caret_tracking(assertion):
    vb = VirtualBuffer()
    vb.caret_tracker.is_macos = False
    vb.caret_tracker.system = "Windows"
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a new sentence. \n", "insert a new sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a second sentence. \n", "insert a second sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a third sentence.", "insert a third sentence"))
    vb.caret_tracker.text_buffer = """Insert a new sentence. 
Insert a second """ + _CARET_MARKER + """sentence. 
Insert a third sentence."""

    assertion( "    Moving one key to the left...") 
    vb.apply_key("left")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be one more than before (11)", caret_index[1] == 11)
    assertion( "    Moving one key to the right...")
    vb.apply_key("right")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be the same as moving back (10)", caret_index[1] == 10)
    assertion( "    Moving two keys to the left...")
    vb.apply_key("left:2")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be two before the previous point (12)", caret_index[1] == 12)
    assertion( "    Moving two keys to the right again...")
    vb.apply_key("right:2")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be the same as the starting point (10)", caret_index[1] == 10)
    assertion( "    Moving to the left and to the right in succession...")
    vb.apply_key("left right")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be the same as the starting point (10)", caret_index[1] == 10)
    assertion( "    Moving over to the next sentence to the right...")
    vb.apply_key("right:11")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 2", caret_index[0] == 2)
    assertion( "        Expect caret character index to be the same as the third sentence (24)", caret_index[1] == 24)
    vb.apply_key("left:28")
    assertion( "    Moving two sentences to the left...")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 0", caret_index[0] == 0)
    assertion( "        Expect caret character index to be at the end of the first sentence", caret_index[1] == 0)
    assertion( "    Moving one character to the right...")
    vb.apply_key("right")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be at the start of the second sentence", caret_index[1] == 26)
    assertion( "    Moving one character to the left...")
    vb.apply_key("left")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 0", caret_index[0] == 0)
    assertion( "        Expect caret character index to be at the end of the first sentence", caret_index[1] == 0)
    assertion( "    Moving one character to the right and pressing end...")
    vb.apply_key("right")
    vb.apply_key("end")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be at the end of the second sentence", caret_index[1] == 0)
    vb.apply_key("left:10")
    assertion( "    Moving one character to the left and pressing CMD-right ( on MacOS ) instead...")    
    vb.caret_tracker.is_macos = True
    vb.caret_tracker.system = "Darwin"
    vb.apply_key("super-right")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be at the end of the second sentence", caret_index[1] == 0)
    

suite = create_test_suite("Exact caret tracking with a filled virtual buffer ( Windows + MacOS )")
suite.add_test(exact_caret_tracking)