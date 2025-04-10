from ...virtual_buffer.caret_tracker import _CARET_MARKER
from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite
from ...virtual_buffer.settings import VirtualBufferSettings

def get_virtual_buffer() -> VirtualBuffer:
    settings = VirtualBufferSettings(live_checking=False)
    return VirtualBuffer(settings)

def test_selection_tracking(assertion):
    vb = get_virtual_buffer()
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a new sentence. \n", "insert a new sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a second sentence. \n", "insert a second sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a third sentence.", "insert a third sentence"))
    vb.caret_tracker.text_buffer = """Insert a new sentence. 
Insert a second """ + _CARET_MARKER + """sentence. 
Insert a third sentence."""

    assertion( "Selecting characters in the virtual buffer")
    assertion( "    Selecting a single character to the left...")
    vb.apply_key("shift:down left shift:up")
    assertion( "        Expect buffer length to stay the same (3)", len(vb.tokens) == 3)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be one less than before (11)", caret_index[1] == 11)
    assertion( "        Expect ' ' selected detected", vb.caret_tracker.get_selection_text() == ' ')
    assertion( "    Moving the caret to the right while selecting...") 
    vb.apply_key("shift:down right shift:up")
    assertion( "        Expect buffer length to stay the same (3)", len(vb.tokens) == 3)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be one more than before (10)", caret_index[1] == 10)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "    Selecting 10 characters to the left...")
    vb.apply_key("shift:down left:10 shift:up")
    assertion( "        Expect buffer length to stay the same (3)", len(vb.tokens) == 3)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be ten less than before (20)", caret_index[1] == 20)
    assertion( "        Expect the selection to be ' a second '", vb.caret_tracker.get_selection_text() == ' a second ')
    assertion( "    Move one character to the left without selecting...")   
    vb.apply_key("left")   
    assertion( "        Expect buffer length to stay the same (3)", len(vb.tokens) == 3)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to not have changed (20)", caret_index[1] == 20)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "    Selecting 10 characters to the right and moving one to the left...")
    vb.apply_key("shift:down right:10 shift:up left")  
    assertion( "        Expect buffer length to stay the same (3)", len(vb.tokens) == 3)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be at the same place as the start of the selection (20)", caret_index[1] == 20)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "    Selecting 10 characters to the right and moving one to the right...")
    vb.apply_key("shift:down right:10 shift:up right")
    assertion( "        Expect buffer length to stay the same (3)", len(vb.tokens) == 3)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be at the end of the selection (10)", caret_index[1] == 10)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "    Selecting 10 characters to the left and moving one to the right...")
    vb.apply_key("shift-left:10 right")
    assertion( "        Expect buffer length to stay the same (3)", len(vb.tokens) == 3)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to stay the same as the start of the selection (10)", caret_index[1] == 10)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)

suite = create_test_suite("Selection tracking")
suite.add_test(test_selection_tracking)