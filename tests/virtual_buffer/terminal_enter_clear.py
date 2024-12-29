from ...virtual_buffer.caret_tracker import _CARET_MARKER
from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite
from ...phonetics.phonetics import PhoneticSearch
from ...virtual_buffer.matcher import VirtualBufferMatcher
from ...virtual_buffer.settings import VirtualBufferSettings

def get_virtual_buffer() -> VirtualBuffer:
    settings = VirtualBufferSettings(live_checking=False)
    return VirtualBuffer(settings)

def get_filled_vb(with_multiline = False):
    search = PhoneticSearch()
    search.set_homophones("")
    search.set_phonetic_similiarities("")

    vb = get_virtual_buffer()
    vb.matcher = VirtualBufferMatcher(search)
    vb.settings.shift_selection = False
    vb.settings.clear_key = "enter"
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
    vb.insert_tokens(text_to_virtual_buffer_tokens("anything.", "anything"))

    return vb

def test_clear_single_line(assertion):
    vb = get_filled_vb()
    assertion( "    Pressing 'Enter' in a terminal with a single line")
    vb.apply_key("enter")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be unknown", caret_index[0] == -1)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect the tokens to be cleared", len(vb.tokens) == 0)

    assertion( "    Inserting a new line after adding text in a terminal with a single line")
    vb = get_filled_vb()
    vb.insert_tokens(text_to_virtual_buffer_tokens("A ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("type ", "type"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("of ", "of"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("text\n", "text"))
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be unknown", caret_index[0] == -1)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect the tokens to be cleared", len(vb.tokens) == 1)

    assertion( "    Inserting a new line in the middle of adding text in a terminal with a single line")
    vb = get_filled_vb()
    vb.insert_tokens(text_to_virtual_buffer_tokens("A ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("type\n", "type"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("of ", "of"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("text.", "text"))
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 0", caret_index[0] == 0)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect two tokens to exist", len(vb.tokens) == 2)

def test_clear_multi_line(assertion):
    vb = get_filled_vb(True)
    assertion( "    Pressing 'Enter' in a terminal with multiple lines")
    vb.apply_key("enter")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be unknown", caret_index[0] == -1)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect the tokens to be cleared", len(vb.tokens) == 0)

    assertion( "    Inserting a new line after adding text in a terminal with multiple lines")
    vb = get_filled_vb(True)
    vb.insert_tokens(text_to_virtual_buffer_tokens("A ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("type ", "type"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("of ", "of"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("text\n", "text"))
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be unknown", caret_index[0] == -1)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect the tokens to be cleared", len(vb.tokens) == 1)

    assertion( "    Inserting a new line in the middle of adding text in a terminal with multiple lines")
    vb = get_filled_vb(True)
    vb.insert_tokens(text_to_virtual_buffer_tokens("A ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("type\n", "type"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("of ", "of"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("text.", "text"))
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 0", caret_index[0] == 0)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect two tokens to exist", len(vb.tokens) == 2)

suite = create_test_suite("Removing the entire terminal context on 'Enter'")
suite.add_test(test_clear_single_line)
suite.add_test(test_clear_multi_line)