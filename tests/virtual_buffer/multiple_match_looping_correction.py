from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite
from ...virtual_buffer.settings import VirtualBufferSettings
from ...phonetics.phonetics import PhoneticSearch

def get_virtual_buffer() -> VirtualBuffer:
    settings = VirtualBufferSettings(live_checking=False)
    return VirtualBuffer(settings)

def get_filled_vb():
    vb = get_virtual_buffer()
    
    # Reset the phonetic search to make sure there is no influence from user settings    
    vb.matcher.phonetic_search = PhoneticSearch()
    vb.matcher.phonetic_search.set_homophones("where,ware,wear")
    vb.matcher.phonetic_search.set_phonetic_similiarities("where,we're,were")
    vb.matcher.phonetic_search.set_semantic_similarities("")    
    
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert ", "insert"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("a ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("sentence, ", "sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("where ", "where"))
    return vb

def test_looping_correction_where(assertion):
    vb = get_filled_vb()
    assertion( "    Moving from the end to the buffer to selecting the first occurrence of 'where'...") 
    keys = vb.select_phrases(["where"])
    assertion( "        Should move to the left until we have reached the word 'new'", keys[0] == "left:44")
    assertion( "        Should move to the right until we have reached the end of the word 'new'", keys[1] == "shift-right:4")
    assertion("     Inserting 'where' again...")

    repeating_inserts = [text_to_virtual_buffer_tokens("where ", "where")]

    # TODO FIXER?
    vb.set_last_action("phonetic_correction", ["where"])
    assertion( "    Inserting where again...")
    vb.insert_tokens(repeating_inserts)
    keys = vb.select_phrases(["new"])
    assertion( "        Should move to the left until we have reached the second occurrence", keys[1] == "left:29")
    assertion( "        Should move to the right until we have reached the end of the word 'new'", keys[2] == "shift-right:4")

def test_looping_self_repair_where(assertion):
    vb = get_filled_vb()
    assertion( "    Moving from the end to the buffer to selecting the first occurrence of 'where'...") 
    keys = vb.select_phrases(["where"])
    assertion( "        Should move to the left until we have reached the word 'new'", keys[0] == "left:44")
    assertion( "        Should move to the right until we have reached the end of the word 'new'", keys[1] == "shift-right:4")
    assertion( "    Repeating the search for 'new' again...")
    keys = vb.select_phrases(["new"])
    assertion( "        Should move to the left until we have reached the second occurrence", keys[1] == "left:29")
    assertion( "        Should move to the right until we have reached the end of the word 'new'", keys[2] == "shift-right:4")


suite = create_test_suite("Using a filled virtual buffer which contains duplicates of certain words used for testing looping")
# TODO FIX LOOPING GO
#suite.add_test(test_looping_correction_where)
#suite.add_test(test_looping_self_repair_where)