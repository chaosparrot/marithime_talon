from ..indexer import VirtualBufferIndexer
from ...utils.test import create_test_suite

def test_single_line_estimation(assertion):
    input_indexer = VirtualBufferIndexer()
    location = input_indexer.determine_caret_position("test", "This is a test.")
    assertion("Within the sentence 'This is a test.'...")
    assertion("    The word 'test' should be found at line 0, 1 character away from the end", location == (0, 1))
    location = input_indexer.determine_caret_position("This", "This is a test.")
    assertion("    The word 'This' should be found at line 0, 11 characters away from the end", location == (0, 11))
    location = input_indexer.determine_caret_position("This is", "This is a test.")
    assertion("    The words 'This is' should be found at line 0, 8 characters away from the end", location == (0, 8))
    location = input_indexer.determine_caret_position("t.", "This is a test.")    
    assertion("    The characters 't.' should be found at line 0, 0 characters away from the end", location == (0, 0))
    location = input_indexer.determine_caret_position("testing", "This is a test.")
    assertion("    The word 'testing' should not be found", location == (-1, -1))
    location = input_indexer.determine_caret_position("is", "This is a test.")
    assertion("    The word 'is' is found multiple times, and thus the exact location is unknown", location == (-2, -2))

def test_single_line_within_multiline_estimation(assertion):
    input_indexer = VirtualBufferIndexer()
    multiline_haystack = """This is a sentence.
This adds to the sentence and turns it into a small paragraph."""

    location = input_indexer.determine_caret_position("This is", multiline_haystack)
    assertion("Within the sentence 'This is a sentence.' followed by 'This adds to the sentence and turns it into a small paragraph.'...")
    assertion("    The words 'This is' should be found at line 0, 12 characters away from the end", location == (0, 12))
    location = input_indexer.determine_caret_position("sentence.", multiline_haystack)
    assertion("    The word 'sentence.' should be found at line 0, 0 characters away from the end", location == (0, 0))
    location = input_indexer.determine_caret_position("paragraph.", multiline_haystack)
    assertion("    The words 'paragraph.' should be found at line 1, 0 characters away from the end", location == (1, 0))
    location = input_indexer.determine_caret_position("and",multiline_haystack)    
    assertion("    The characters 'and' should be found at line 1, 33 characters away from the end", location == (1, 33))
    location = input_indexer.determine_caret_position("testing", multiline_haystack)
    assertion("    The word 'testing' should not be found", location == (-1, -1))
    location = input_indexer.determine_caret_position("This", multiline_haystack)
    assertion("    The word 'This' is found multiple times, and thus the exact location is unknown", location == (-2, -2))

def test_multiline_in_multiline_estimation(assertion):
    input_indexer = VirtualBufferIndexer()
    multiline_haystack = """This is a sentence.
This adds to the sentence and turns it into a small paragraph."""
    multiline_needle_this = """a sentence.
This"""
    multiline_needle_this_adds = """
This adds"""
    multiline_needle_paragraph = """paragraph.
"""
    multiline_needle_test = """Test.
"""

    location = input_indexer.determine_caret_position(multiline_needle_this, multiline_haystack)
    assertion("Within the sentence 'This is a sentence.' followed by 'This adds to the sentence and turns it into a small paragraph.'...")
    assertion("    The sequence 'sentence.<newline>This' should be found at line 1, 58 characters away from the end", location == (1, 58))
    location = input_indexer.determine_caret_position(multiline_needle_this_adds, multiline_haystack)
    assertion("    The sequence '<newline>This adds' should be found at line 1, 53 characters away from the end", location == (1, 53))
    location = input_indexer.determine_caret_position(multiline_needle_paragraph, multiline_haystack)
    assertion("    The sequence 'paragraph.<newline>' should not be found as no newline exists after paragraph", location == (-1, -1))
    location = input_indexer.determine_caret_position(multiline_needle_test, multiline_haystack)    
    assertion("    The sequence 'Test.<newline>' should not be found as the word Test does not exist", location == (-1, -1))

suite = create_test_suite("Caret position estimation based on selection")
suite.add_test(test_single_line_estimation)
suite.add_test(test_single_line_within_multiline_estimation)
suite.add_test(test_multiline_in_multiline_estimation)