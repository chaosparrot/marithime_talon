from ..matcher import VirtualBufferMatcher
from ...phonetics.detection import EXACT_MATCH, HOMOPHONE_MATCH
from ..typing import VirtualBufferMatch, VirtualBufferMatchWords
from ...utils.test import create_test_suite

def test_simple_matches_to_word_match(assertion):
    single_match = VirtualBufferMatch([[0]], [[0]], ["this"], ["this"], [EXACT_MATCH], EXACT_MATCH, 0)
    double_match = VirtualBufferMatch([[0], [1]], [[0], [1]], ["this", "is"], ["this", "is"], [EXACT_MATCH, EXACT_MATCH], EXACT_MATCH, 0)

    assertion("Using a single word match")
    single_matched_words = single_match.get_matched_words()
    assertion("    should have no query skips", single_matched_words.query_skips == 0)
    assertion("    should have no buffer skips", single_matched_words.buffer_skips == 0)
    assertion("    should have one score", len(single_matched_words.scores) == 1)
    assertion("    should have the same query length as buffer length", len(single_matched_words.query) == len(single_matched_words.buffer))

    assertion("Using a double word match")
    double_matched_words = double_match.get_matched_words()
    assertion("    should have no query skips", double_matched_words.query_skips == 0)
    assertion("    should have no buffer skips", double_matched_words.buffer_skips == 0)
    assertion("    should have two scores", len(double_matched_words.scores) == 2)
    assertion("    should have the same query length as buffer length", len(double_matched_words.query) == len(double_matched_words.buffer))

def test_simple_skip_matches(assertion):
    double_match = VirtualBufferMatch([[0], [1]], [[0], [2]], ["this", "is"], ["this", "evidently", "is"], [EXACT_MATCH, 0.0, EXACT_MATCH], EXACT_MATCH, 0)
    double_matched_words = double_match.get_matched_words()

    assertion("Using a double word match with a skip in the middle")
    assertion("    should have no query skips", double_matched_words.query_skips == 0)
    assertion("    should have 1 buffer skip", double_matched_words.buffer_skips == 1)
    assertion("    should have two scores", len(double_matched_words.scores) == 2)
    assertion("    should have the same query length as buffer length", len(double_matched_words.query) == len(double_matched_words.buffer))
    assertion("    should not contain the skipped buffer word", "evidently" not in "".join(double_matched_words.buffer[1]))

    double_query_match = VirtualBufferMatch([[0], [2]], [[0], [1]], ["this", "is", "evidently"], ["this", "evidently"], [EXACT_MATCH, EXACT_MATCH], EXACT_MATCH, 0)
    double_query_matched_words = double_query_match.get_matched_words()
    assertion("Using a double word match with a query skip in the middle")
    assertion("    should have 1 query skip", double_query_matched_words.query_skips == 1)
    assertion("    should have no buffer skips", double_query_matched_words.buffer_skips == 0)
    assertion("    should have two scores", len(double_query_matched_words.scores) == 2)
    assertion("    should have the same query length as buffer length", len(double_query_matched_words.query) == len(double_query_matched_words.buffer))
    assertion("    should not contain the skipped query word", "is" not in "".join(double_query_matched_words.query[1]))

def test_combined_matches_to_word_match(assertion):
    combined_query_match = VirtualBufferMatch([[0, 1]], [[0]], ["this", "is"], ["theses"], [HOMOPHONE_MATCH], HOMOPHONE_MATCH, 0)

    assertion("Using a single combined query word match")
    combined_query_word_matches = combined_query_match.get_matched_words()
    assertion("    should have no query skips", combined_query_word_matches.query_skips == 0)
    assertion("    should have no buffer skips", combined_query_word_matches.buffer_skips == 0)
    assertion("    should have one score", len(combined_query_word_matches.scores) == 1)
    assertion("    should have the same query length as buffer length", len(combined_query_word_matches.query) == len(combined_query_word_matches.buffer))

    combined_buffer_match = VirtualBufferMatch([[0]], [[0]], ["theses"], ["this", "is"], [HOMOPHONE_MATCH], HOMOPHONE_MATCH, 0)
    assertion("Using a single combined buffer word match")
    combined_buffer_word_matches = combined_buffer_match.get_matched_words()
    assertion("    should have no query skips", combined_buffer_word_matches.query_skips == 0)
    assertion("    should have no buffer skips", combined_buffer_word_matches.buffer_skips == 0)
    assertion("    should have one score", len(combined_buffer_word_matches.scores) == 1)
    assertion("    should have the same query length as buffer length", len(combined_buffer_word_matches.query) == len(combined_buffer_word_matches.buffer))

def test_combined_skip_matches(assertion):
    skip_query_matches = VirtualBufferMatch([[0], [2, 3], [4]], [[10], [11], [12]], ["this", "most", "likely", "is", "well"], ["this", "likelyness", "will"], [EXACT_MATCH, HOMOPHONE_MATCH, HOMOPHONE_MATCH], HOMOPHONE_MATCH, 0)
    skipped_query_matched_words = skip_query_matches.get_matched_words()

    assertion("Using a 5 word match with a skip in the middle")
    assertion("    should have 1 query skip", skipped_query_matched_words.query_skips == 1)
    assertion("    should have no buffer skips", skipped_query_matched_words.buffer_skips == 0)
    assertion("    should have three scores", len(skipped_query_matched_words.scores) == 3)
    assertion("    should have the same query length as buffer length", len(skipped_query_matched_words.query) == len(skipped_query_matched_words.buffer))
    assertion("    should not contain the skipped query word", "most" not in "".join(skipped_query_matched_words.query[1]))

    skip_buffer_matches = VirtualBufferMatch([[0], [1], [2]], [[10], [12, 13], [14]], ["this", "likelyness", "will"], ["this", "most", "likely", "is", "well"], [EXACT_MATCH, 0.0, HOMOPHONE_MATCH, HOMOPHONE_MATCH], HOMOPHONE_MATCH, 0)
    skipped_buffer_matched_words = skip_buffer_matches.get_matched_words()
    assertion("Using a 3 word match with a buffer skip in the middle")
    assertion("    should have no query skips", skipped_buffer_matched_words.query_skips == 0)
    assertion("    should have 1 buffer skip", skipped_buffer_matched_words.buffer_skips == 1)
    assertion("    should have three scores", len(skipped_buffer_matched_words.scores) == 3)
    assertion("    should have the same query length as buffer length", len(skipped_buffer_matched_words.query) == len(skipped_buffer_matched_words.buffer))
    assertion("    should not contain the skipped query word", "most" not in "".join(skipped_buffer_matched_words.buffer[1]))

suite = create_test_suite("Virtual buffer matcher find words matched to one another in a finished match")
suite.add_test(test_simple_matches_to_word_match)
suite.add_test(test_simple_skip_matches)
suite.add_test(test_combined_matches_to_word_match)
suite.add_test(test_combined_skip_matches)