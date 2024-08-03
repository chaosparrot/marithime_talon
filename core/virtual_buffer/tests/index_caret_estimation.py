from ..indexer import VirtualBufferIndexer
from ...utils.test import create_test_suite

def test_single_line_estimation(assertion):
    input_indexer = VirtualBufferIndexer()
    location = input_indexer.determine_caret_position("", "This is a test.", 0)
    assertion("Within the sentence 'This is a test.'...")
    assertion("    The position 0 should be found at line 0, 15 characters away from the end", location == (0, 15))
    location = input_indexer.determine_caret_position("", "This is a test.", 7)
    assertion("    The position 7 should be found at line 0, 8 characters away from the end", location == (0, 8))
    location = input_indexer.determine_caret_position("", "This is a test.", 15)
    assertion("    The position 15 should be found at line 0, 0 characters away from the end", location == (0, 0))
    location = input_indexer.determine_caret_position("", "This is a test.", 16)
    assertion("    The position 16 should not be found", location == (-1, -1))

def test_multiline_estimation(assertion):
    input_indexer = VirtualBufferIndexer()
    multiline_haystack = """This is a sentence.
This adds to the sentence and turns it into a small paragraph."""

    location = input_indexer.determine_caret_position("", multiline_haystack, 0)
    assertion("Within the sentence 'This is a sentence.' followed by 'This adds to the sentence and turns it into a small paragraph.'...")
    assertion("    The position 0 should be found at line 0, 19 characters away from the end", location == (0, 19))
    location = input_indexer.determine_caret_position("", multiline_haystack, 8)
    assertion("    The position 8 should be found at line 0, 11 characters away from the end", location == (0, 11))
    location = input_indexer.determine_caret_position("", multiline_haystack, 19)
    assertion("    The position 19 should be found at line 0, 0 characters away from the end", location == (0, 0))
    location = input_indexer.determine_caret_position("", multiline_haystack, 20)
    assertion("    The position 20 should be found at line 1, 62 characters away from the end", location == (1, 62))
    location = input_indexer.determine_caret_position("", multiline_haystack, 82)
    assertion("    The position 82 should be found at line 1, 0 characters away from the end", location == (1, 0))
    location = input_indexer.determine_caret_position("", multiline_haystack, 100)
    assertion("    The position 100 should not be found", location == (-1, -1))

suite = create_test_suite("Caret position estimation based on total and a character index position")
suite.add_test(test_single_line_estimation)
suite.add_test(test_multiline_estimation)