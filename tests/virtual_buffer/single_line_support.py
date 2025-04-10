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

def get_filled_vb():
    search = PhoneticSearch()
    search.set_homophones("")
    search.set_phonetic_similiarities("")
    search.set_semantic_similarities("")    

    vb = get_virtual_buffer()
    vb.matcher = VirtualBufferMatcher(search)
    vb.settings.shift_selection = True
    vb.settings.multiline_supported = False
    vb.settings.clear_key = ""
    vb.settings.start_of_line_key = "home"
    vb.settings.end_of_line_key = "end"
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
    vb.insert_tokens(text_to_virtual_buffer_tokens("previous ", "previous"))
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

def test_press_enter_key(assertion):
    vb = get_filled_vb()
    assertion( "    Pressing 'Enter' in a single line field")
    vb.apply_key("enter")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to stay the same", caret_index[0] == 0)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect token length to be the same", len(vb.tokens) == 20)

    assertion( "    Inserting tokens after pressing 'Enter' in a single line field")
    vb.insert_tokens(text_to_virtual_buffer_tokens(" A ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("type ", "type"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("of ", "of"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("text", "text"))
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to stay the same", caret_index[0] == 0)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect token length to increase by 5", len(vb.tokens) == 25)

def test_press_enter_on_select_key(assertion):
    # Inserting newlines is different from enter presses in single line fields
    # As it clears the input field and makes the final line the one used
    # Rather than ignoring the new line
    vb = get_filled_vb()
    assertion( "    Pressing 'Enter' in a single line field with text selection")
    vb.select_phrases(["can", "be", "anything"])
    vb.apply_key("enter")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to stay the same", caret_index[0] == 0)
    assertion( "        Expect selection detected", vb.is_selecting() == True)
    assertion( "        Expect token length to be the same", len(vb.tokens) == 20)

    assertion( "    Inserting tokens with a selection after pressing 'Enter' in a single line field")
    vb.insert_tokens(text_to_virtual_buffer_tokens(" A ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("type ", "type"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("of ", "of"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("text", "text"))
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to stay the same", caret_index[0] == 0)
    assertion( "        Expect no selection detected after insertions", vb.is_selecting() == False)
    assertion( "        Expect token length to increase by 2", len(vb.tokens) == 22)

def test_newline_insert(assertion):
    assertion( "    Inserting a new line after adding text in a single line field")
    vb = get_filled_vb()
    vb.insert_tokens(text_to_virtual_buffer_tokens("A ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("type ", "type"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("of ", "of"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("text\n", "text"))
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be unknown", caret_index[0] == -1)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect only one token available", len(vb.tokens) == 1)

    assertion( "    Inserting a new line in the middle of adding text in a single line field")
    vb = get_filled_vb()
    vb.insert_tokens(text_to_virtual_buffer_tokens("A ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("type", "type"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("\n", ""))
    vb.insert_tokens(text_to_virtual_buffer_tokens("of ", "of"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("text.", "text"))
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to stay the same", caret_index[0] == 0)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect only two tokens available", len(vb.tokens) == 2)

def test_arrow_key_press(assertion):
    vb = get_filled_vb()
    assertion( "    Pressing 'Down' in a single line field")
    caret_index = vb.caret_tracker.get_caret_index()

    vb.apply_key("down")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( caret_index )
    assertion( vb.caret_tracker.text_buffer )    
    assertion( "        Expect caret line index to be the same", caret_index[0] == 0)
    assertion( "        Expect caret character index to be coarse", caret_index[1] == -1)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect token length to be the same", len(vb.tokens) == 20)

    assertion( "    Pressing 'Up' in a single line field")
    vb.apply_key("up")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be the same", caret_index[0] == 0)
    assertion( "        Expect caret character index to be coarse", caret_index[1] == -1)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect token length to be the same", len(vb.tokens) == 20)

def test_line_navigation_key_press(assertion):
    vb = get_filled_vb()
    assertion( "    Pressing 'Home' in a single line field")

    vb.apply_key("home")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be the same", caret_index[0] == 0)
    assertion( "        Expect caret character index to be at the start", caret_index[1] == 119)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect token length to be the same", len(vb.tokens) == 20)

    assertion( "    Pressing 'End' in a single line field")
    vb.apply_key("end")
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be the same", caret_index[0] == 0)
    assertion( "        Expect caret character index to be at the end", caret_index[1] == 0)
    assertion( "        Expect no selection detected", vb.is_selecting() == False)
    assertion( "        Expect token length to be the same", len(vb.tokens) == 20)

suite = create_test_suite("Handling 'Enter' presses within fields that do not have multiline support")
suite.add_test(test_press_enter_key)
suite.add_test(test_press_enter_on_select_key)
suite.add_test(test_newline_insert)
suite.add_test(test_arrow_key_press)
suite.add_test(test_line_navigation_key_press)