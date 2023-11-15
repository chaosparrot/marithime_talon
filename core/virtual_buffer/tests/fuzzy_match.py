from ..buffer import VirtualBuffer
from ..indexer import text_to_virtual_buffer_tokens
from ...utils.test import create_test_suite

suite = create_test_suite("With a filled virtual buffer containing a full sentence")
def test_fuzzy_matching(assertion):
    vb = VirtualBuffer()
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert ", "insert"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("an ", "an"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("ad ", "ad"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("that ", "that"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("will ", "will"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("get ", "get"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("attention.", "attention"))

    assertion( "    Attempting to find 'will' should result in an exact match...", vb.has_matching_phrase("will") == True)
    assertion( "    Attempting to find 'add' should result in a fuzzy match...", vb.has_matching_phrase("add") == True)
    assertion( "    Attempting to find 'apt' should not result in a match...", vb.has_matching_phrase("apt") == False)
    assertion( "    Attempting to find 'dad' should result in a fuzzy match...", vb.has_matching_phrase("dad") == True)
    assertion( "    Attempting to find 'and' should result in a match...", vb.has_matching_phrase("and") == True)
    assertion( "    Attempting to find 'end' should not result in a match...", vb.has_matching_phrase("end") == False)

suite.add_test(test_fuzzy_matching)