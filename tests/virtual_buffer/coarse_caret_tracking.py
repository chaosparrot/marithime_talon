from ...virtual_buffer.caret_tracker import _CARET_MARKER
from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite

def coarse_caret_tracker_splitting(assertion):
    vb = VirtualBuffer()
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a new sentence. \n", "insert a new sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a second sentence. \n", "insert a second sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a third sentence.", "insert a third sentence"))
    vb.caret_tracker.system = "Windows"
    vb.caret_tracker.is_macos = False
    vb.caret_tracker.text_buffer = """Insert a new sentence. 
    Insert a second """ + _CARET_MARKER + """sentence. 
    Insert a third sentence."""

    assertion( "Caret tracking coarse splitting" )
    cpt = vb.caret_tracker 
    items = cpt.split_string_with_punctuation("Testing")
    assertion( "    Expect single word length to be 1", len(items) == 1 )
    items = cpt.split_string_with_punctuation("Testing items")
    assertion( "    Expect double word length to be 2", len(items) == 2 )
    items = cpt.split_string_with_punctuation("Testing  items")
    assertion( "    Expect double word, with two spaces in between length to be 2", len(items) == 2 )
    items = cpt.split_string_with_punctuation("Testing-items")
    assertion( "    Expect word with dashes length to be 2", len(items) == 2 )
    items = cpt.split_string_with_punctuation("Words... don't come easy")
    assertion( "    Expect 'Words... don't come easy' length to be 5", len(items) == 5 )
    assertion( "    Expect 'Words' to be the first split", items[0] == "Words" )
    assertion( "    Expect 'don' to be the second split", items[1] == "don" )
    items = cpt.split_string_with_punctuation("""This is a 
                                            split sentence. """)
    assertion( "    Expect a sentence with new lines to have a length of 5", len(items) == 5 )

def coarse_caret_tracking_single_line(assertion):
    vb = VirtualBuffer()
    vb.caret_tracker.system = "Windows"
    vb.caret_tracker.is_macos = False    
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a new sentence. \n", "insert a new sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a second sentence. \n", "insert a second sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a third sentence.", "insert a third sentence"))
    vb.caret_tracker.text_buffer = """Insert a new sentence. 
    Insert a second """ + _CARET_MARKER + """sentence. 
    Insert a third sentence."""

    assertion( "Coarse caret tracking with a filled virtual buffer")
    assertion( "    Move a word left...")
    vb.apply_key("ctrl-left")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect coarse character index to be before the word second (17)", caret_index[1] == 17)
    assertion( "    Moving a word right...")
    vb.apply_key("ctrl-right")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect coarse character index to be after the word second (11)", caret_index[1] == 11)
    assertion( "    Moving two words to the left...")
    vb.apply_key("ctrl-left:2")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect coarse character index to be after the word a (7)", caret_index[1] == 19)
    assertion( "    Moving three words to the right...")
    vb.apply_key("ctrl-right:3")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect coarse character index to be after the word sentence (1)", caret_index[1] == 1)
    assertion( "    Moving left twice...")
    vb.apply_key("left:2")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect coarse character index to be two characters inside the word sentence (3)", caret_index[1] == 3)
    assertion( "    Moving right twice...")
    vb.apply_key("right:2")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect coarse character index to be after the word sentence (1)", caret_index[1] == 1)
    assertion( "    Moving one more word to the right to simulate a line end transfer...")
    vb.apply_key("ctrl-shift-right")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be lost", caret_index[0] == -1 )
    assertion( "    Moving one more word to the left to simulate a line end transfer...")
    vb.apply_key("ctrl-shift-left")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be lost", caret_index[0] == -1 )
 
def coarse_caret_tracking_multi_line(assertion):
    vb = VirtualBuffer()
    vb.caret_tracker.system = "Windows"
    vb.caret_tracker.is_macos = False    
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a new sentence. \n", "insert a new sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a second sentence. \n", "insert a second sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a third sentence.", "insert a third sentence"))
    vb.caret_tracker.text_buffer = """Insert a new sentence. 
Insert a second """ + _CARET_MARKER + """sentence. 
Insert a third sentence."""
    assertion( "    Pressing up to go to the first sentence...")
    vb.apply_key("up")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be 0", caret_index[0] == 0)
    assertion( "    Pressing down twice to go to the third sentence...")
    vb.apply_key("down:2") 
    caret_index = vb.caret_tracker.get_caret_index(True) 
    assertion( "        Expect caret line index to be 2", caret_index[0] == 2)
    assertion( "    Pressing home to go to the start of the third sentence...")
    vb.apply_key("home")
    caret_index = vb.caret_tracker.get_caret_index(True)  
    assertion( "        Expect caret line index to be 2", caret_index[0] == 2)
    assertion( "        Expect coarse character index to be before the word insert (24)", caret_index[1] == 24)

def coarse_caret_tracking_single_line_macos(assertion):
    vb = VirtualBuffer()
    vb.caret_tracker.system = "Darwin"
    vb.caret_tracker.is_macos = True    
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a new sentence. \n", "insert a new sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a second sentence. \n", "insert a second sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a third sentence.", "insert a third sentence"))
    vb.caret_tracker.text_buffer = """Insert a new sentence. 
    Insert a second """ + _CARET_MARKER + """sentence. 
    Insert a third sentence."""

    assertion( "Coarse caret tracking with a filled virtual buffer on MacOS")
    assertion( "    Move a word left...")
    vb.apply_key("alt-left")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect coarse character index to be before the word second (17)", caret_index[1] == 17)
    assertion( "    Moving a word right...")
    vb.apply_key("alt-right")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect coarse character index to be after the word second (11)", caret_index[1] == 11)
    assertion( "    Moving two words to the left...")
    vb.apply_key("alt-left:2")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect coarse character index to be after the word a (7)", caret_index[1] == 19)
    assertion( "    Moving three words to the right...")
    vb.apply_key("alt-right:3")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect coarse character index to be after the word sentence (1)", caret_index[1] == 1)
    assertion( "    Moving left twice...")
    vb.apply_key("left:2")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect coarse character index to be two characters inside the word sentence (3)", caret_index[1] == 3)
    assertion( "    Moving right twice...")
    vb.apply_key("right:2")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be 1", caret_index[0] == 1)
    assertion( "        Expect coarse character index to be after the word sentence (1)", caret_index[1] == 1)
    assertion( "    Moving one more word to the right to simulate a line end transfer...")
    vb.apply_key("alt-shift-right")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be lost", caret_index[0] == -1 )
    assertion( "    Moving one more word to the left to simulate a line end transfer...")
    vb.apply_key("alt-shift-left")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be lost", caret_index[0] == -1 )

def coarse_caret_tracking_multi_line_macos(assertion):
    vb = VirtualBuffer()
    vb.caret_tracker.system = "Darwin"
    vb.caret_tracker.is_macos = True    
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a new sentence. \n", "insert a new sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a second sentence. \n", "insert a second sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert a third sentence.", "insert a third sentence"))
    vb.caret_tracker.text_buffer = """Insert a new sentence. 
Insert a second """ + _CARET_MARKER + """sentence. 
Insert a third sentence."""
    assertion( "    Pressing up to go to the first sentence on MacOS...")
    vb.apply_key("up")
    caret_index = vb.caret_tracker.get_caret_index(True)
    assertion( "        Expect caret line index to be 0", caret_index[0] == 0)
    assertion( "    Pressing down twice to go to the third sentence...")
    vb.apply_key("down:2")
    caret_index = vb.caret_tracker.get_caret_index(True) 
    assertion( "        Expect caret line index to be 2", caret_index[0] == 2)
    assertion( "    Pressing CMD+LEFT to go to the start of the third sentence...")
    vb.apply_key("cmd-left")
    caret_index = vb.caret_tracker.get_caret_index(True)  
    assertion( "        Expect caret line index to be 2", caret_index[0] == 2)
    assertion( "        Expect coarse character index to be before the word insert (24)", caret_index[1] == 24)


suite = create_test_suite("Coarse caret tracking")
suite.add_test(coarse_caret_tracker_splitting)
suite.add_test(coarse_caret_tracking_single_line)
suite.add_test(coarse_caret_tracking_multi_line)
suite.add_test(coarse_caret_tracking_single_line_macos)
suite.add_test(coarse_caret_tracking_multi_line_macos)