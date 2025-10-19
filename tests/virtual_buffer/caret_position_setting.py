from ...virtual_buffer.caret_tracker import _CARET_MARKER
from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite
from ...virtual_buffer.settings import VirtualBufferSettings

def get_virtual_buffer() -> VirtualBuffer:
    settings = VirtualBufferSettings(live_checking=False)
    vb = VirtualBuffer(settings)
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a new sentence. \n", "insert a new sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a second sentence. \n", "insert a second sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a third sentence.", "insert a third sentence"))
    vb.caret_tracker.text_buffer = """Insert a new sentence. 
Insert a second """ + _CARET_MARKER + """sentence. 
Insert a third sentence."""
    return vb

def exact_caret_setting_first_line(assertion):
    assertion( "    Setting the caret on the first character and line...")
    vb = get_virtual_buffer()
    vb.caret_tracker.set_caret_position(0, 0)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 0", caret_index[0] == 0)
    assertion( "        Expect caret character index to be at the start of the line", caret_index[1] == 23)
    assertion( "    Setting the caret before the fifth character and first line...")
    vb.caret_tracker.set_caret_position(0, 4)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 0", caret_index[0] == 0)
    assertion( "        Expect caret character index to be four characters removed from the start of the line", caret_index[1] == 19)
    assertion( "    Setting the caret at the end character and first line...")
    vb.caret_tracker.set_caret_position(0, 23)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 0", caret_index[0] == 0)
    assertion( "        Expect caret character index to be at the end of the line", caret_index[1] == 0)
    assertion( "    Setting the caret beyond the end character and first line...")
    vb.caret_tracker.set_caret_position(0, 30)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 0", caret_index[0] == 0)
    assertion( "        Expect caret character index to be at the end of the line", caret_index[1] == 0)

def exact_caret_setting_second_line(assertion):
    assertion( "    Setting the caret on the first character and second line...")
    vb = get_virtual_buffer()
    vb.caret_tracker.set_caret_position(1, 0)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be at the start of the line", caret_index[1] == 26)
    assertion( "    Setting the caret before the fifth character and second line...")
    vb.caret_tracker.set_caret_position(1, 4)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be four characters removed from the start of the line", caret_index[1] == 22)
    assertion( "    Setting the caret at the end character and second line...")
    vb.caret_tracker.set_caret_position(1, 26)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be at the end of the line", caret_index[1] == 0)
    assertion( "    Setting the caret beyond the end character and second line...")
    vb.caret_tracker.set_caret_position(1, 30)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect caret character index to be at the end of the line", caret_index[1] == 0)

def exact_caret_setting_last_line(assertion):
    assertion( "    Setting the caret on the first character and last line...")
    vb = get_virtual_buffer()
    vb.caret_tracker.set_caret_position(2, 0)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 2", caret_index[0] == 2)
    assertion( "        Expect caret character index to be at the start of the line", caret_index[1] == 24)
    assertion( "    Setting the caret before the fifth character and last line...")
    vb.caret_tracker.set_caret_position(2, 4)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 2", caret_index[0] == 2)
    assertion( "        Expect caret character index to be four characters removed from the start of the line", caret_index[1] == 20)
    assertion( "    Setting the caret at the end character and last line...")
    vb.caret_tracker.set_caret_position(2, 24)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 2", caret_index[0] == 2)
    assertion( "        Expect caret character index to be at the end of the line", caret_index[1] == 0)
    assertion( "    Setting the caret beyond the end character and last line...")
    vb.caret_tracker.set_caret_position(2, 30)
    caret_index = vb.caret_tracker.get_caret_index()
    assertion( "        Expect caret line index to be 2", caret_index[0] == 2)
    assertion( "        Expect caret character index to be at the end of the line", caret_index[1] == 0)

def exact_caret_setting_selection(assertion):
    vb = get_virtual_buffer()
    assertion( "    Setting the caret on the first character and line until the second character...")
    vb.caret_tracker.set_caret_position(0, 0, 0, 1)
    caret_index = vb.caret_tracker.get_caret_index()
    selection_index = vb.caret_tracker.selection_caret_marker
    assertion( "        Expect caret line index to be 0", caret_index[0] == 0)
    assertion( "        Expect caret character index to be at the start of the line", caret_index[1] == 23)
    assertion( "        Expect selection index to be at line 0", selection_index[0] == 0)
    assertion( "        Expect selection character index to be one less than the caret position", selection_index[1] == 22)
    assertion( "    Setting the caret on the first character and line until the second line and second character...")
    vb.caret_tracker.set_caret_position(0, 0, 1, 1)
    caret_index = vb.caret_tracker.get_caret_index()
    selection_index = vb.caret_tracker.selection_caret_marker
    assertion( "        Expect caret line index to be 0", caret_index[0] == 0)
    assertion( "        Expect caret character index to be at the start of the line", caret_index[1] == 23)
    assertion( "        Expect selection index to be at line 1", selection_index[0] == 1)
    assertion( "        Expect selection character index to be one after the line start", selection_index[1] == 25)
    assertion( "    Setting the caret on the last character of the first line until the last line and first character...")
    vb.caret_tracker.set_caret_position(0, 26, 2, 0)
    caret_index = vb.caret_tracker.get_caret_index()
    selection_index = vb.caret_tracker.selection_caret_marker
    assertion( "        Expect caret line index to be 0", caret_index[0] == 0)
    assertion( "        Expect caret character index to be at the end of the line", caret_index[1] == 0)
    assertion( "        Expect selection index to be at line 2", selection_index[0] == 2)
    assertion( "        Expect selection character index to be one after the line start", selection_index[1] == 24)


suite = create_test_suite("Setting the exact caret position from outside marithime")
suite.add_test(exact_caret_setting_first_line)
suite.add_test(exact_caret_setting_second_line)
suite.add_test(exact_caret_setting_last_line)
suite.add_test(exact_caret_setting_selection)