from ...virtual_buffer.caret_tracker import _CARET_MARKER
from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite
from ...phonetics.phonetics import PhoneticSearch
from ...virtual_buffer.matcher import VirtualBufferMatcher

def get_filled_vb(with_multiline = False):
    search = PhoneticSearch()
    search.set_homophones("")
    search.set_phonetic_similiarities("")

    vb = VirtualBuffer()
    vb.matcher = VirtualBufferMatcher(search)
    vb.shift_selection = False
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert ", "insert"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("two ", "two"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("words ", "words"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("into ", "into"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("a ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("previous ", "previous"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("sentence, ", "sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("so ", "so"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("that ", "that"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("the ", "the"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("previous" + ("\n" if with_multiline else " "), "previous"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("sentence ", "sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("will ", "will"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("become ", "become"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("longer ", "longer"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("too! ", "too"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Words ", "words"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("can ", "can"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("be ", "be"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("anything.", "anything"), )

    return vb

def test_remove_selecting_single_tokens(assertion):
    vb = get_filled_vb()

    assertion( "    Virtually selecting a single token to the left and remove it...")
    vb.select_phrases(["anything"])
    keys = vb.remove_virtual_selection()
    for key in keys:
        vb.apply_key(key)

    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 0", caret_index[0] == 0)
    assertion( "        Expect caret character index to be the same as before (0)", caret_index[1] == 0)
    assertion( "        Expect 'backspace' to have been pressed 9 times to remove 'anything.'", keys[0] == "backspace:9")
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect final token to have changed", vb.tokens[-2].text == "be ")

    assertion( "    Virtually selecting a single token to the left in the middle of the text and remove it...")
    vb.select_phrases(["will"])
    keys = vb.remove_virtual_selection()
    for key in keys:
        vb.apply_key(key)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 0", caret_index[0] == 0)
    assertion( "        Expect caret character index to be different than before behind 'will'", caret_index[1] == 41)
    assertion( "        Expect 'backspace' to have been pressed 5 times to remove 'will '", keys[0] == "backspace:5")
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect final token to not have changed", vb.tokens[-2].text == "be ")

def test_remove_selecting_multiple_tokens_left(assertion):
    vb = get_filled_vb()
    vb.select_phrases(["can", "be", "anything"])
    assertion( "    Virtually selecting multiple tokens to the left and remove it...")
    keys = vb.remove_virtual_selection()
    for key in keys:
        vb.apply_key(key)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 0", caret_index[0] == 1)
    assertion( "        Expect caret character index to be the same as before (0)", caret_index[1] == 0)
    assertion( "        Expect 'backspace' to have been pressed 16 times to remove 'can be anything.'", keys[0] == "backspace:16")    
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect final token to have changed", vb.tokens[-1].text == "Words ")

suite = create_test_suite("Removing virtually selected text")
suite.add_test(test_remove_selecting_single_tokens)
# suite.add_test(test_remove_selecting_multiple_tokens_left)
# suite.add_test(test_remove_multiline_multiple_tokens)
suite.run()