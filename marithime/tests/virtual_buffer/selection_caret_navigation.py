from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite

def test_track_selection_caret(assertion):
    vb = VirtualBuffer()
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert ", "insert"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("a ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("sentence.", "sentence"))

    assertion( "Selecting characters in the virtual buffer")
    assertion( "    Selecting a single character to the left and then moving to the first character...")
    vb.apply_key("shift:down left shift:up")
    keys = vb.navigate_to_token(vb.find_token_by_phrase("insert"), 0)
    assertion( "        Should move the caret to the left one extra time compared to non-selected text", keys[0] == "left" and keys[1] == "left:21")
    assertion( "    Selecting five characters to the right and then moving to the first character...")
    vb.apply_key("shift:down right:5 shift:up")
    keys = vb.navigate_to_token(vb.find_token_by_phrase("insert"), 0)
    assertion( "        Should move the caret to the left one time as the selection started on the first character", keys[0] == "left" and len(keys) == 1)
    assertion( "    Selecting five characters to the right and then moving to the first character of the final word...")
    vb.apply_key("shift:down right:5 shift:up")
    keys = vb.navigate_to_token(vb.find_token_by_phrase("sentence"), 0)
    assertion( "        Should move the caret to the right one time as the selection started on the first character", keys[0] == "right" and keys[1] == "right:8")
    assertion( "    Selecting one character to the left and then moving to the first character of the final word...")
    vb.apply_key("shift:down left shift:up")
    keys = vb.navigate_to_token(vb.find_token_by_phrase("sentence"), 0)
    assertion( "        Should move the caret to the right one time as the selection started on the first character", keys[0] == "right" and len(keys) == 1)

suite = create_test_suite("Selection tracking caret navigation")
suite.add_test(test_track_selection_caret)