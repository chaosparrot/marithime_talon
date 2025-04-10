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
    vb.matcher.phonetic_search.set_homophones("to,too,two")
    vb.matcher.phonetic_search.set_phonetic_similiarities("")
    vb.matcher.phonetic_search.set_semantic_similarities("")

    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert ", "insert"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("a ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("sentence, ", "sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("that ", "that"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("will ", "will"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("have ", "have"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new")) 
    vb.insert_tokens(text_to_virtual_buffer_tokens("words ", "words"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("compared ", "compared"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("to ", "to"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("the ", "the"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("previous ", "previous"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("two ", "two"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("sentences.", "sentences"))
    return vb

def test_multiple_fuzzy_matching(assertion):
    vb = get_filled_vb()
    assertion( "    Moving from the end of the word 'sentences' searching for 'to'...") 
    keys = vb.go_phrase("to", 'start', next_occurrence=False, verbose=True)
    assertion( "        Should go left until the word 'two' is found", keys[0] == "left:14" )
    assertion( "    Searching for 'to' again...") 
    keys = vb.go_phrase("to", 'start', next_occurrence=True)
    assertion( "        Should go left until the word 'to' is found", keys[0] == "left:16" )
    keys = vb.go_phrase("wil", 'end', next_occurrence=False)
    assertion( "    Searching for 'wil', which isn't available directly...") 
    assertion( "        Should go left until the word 'will' is found", keys[0] == "left:24" )

suite = create_test_suite("Using a filled virtual buffer which contains homophones of certain words")
suite.add_test(test_multiple_fuzzy_matching)