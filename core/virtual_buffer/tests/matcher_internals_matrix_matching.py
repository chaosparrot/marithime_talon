from ..matcher import VirtualBufferMatcher
from ...phonetics.phonetics import PhoneticSearch
from ...phonetics.detection import EXACT_MATCH, HOMOPHONE_MATCH
from ..indexer import text_to_virtual_buffer_tokens
from ..typing import VirtualBufferMatchMatrix, VirtualBufferMatch, SELECTION_THRESHOLD, CORRECTION_THRESHOLD
from ...utils.test import create_test_suite

max_score_per_word = EXACT_MATCH
select_threshold = SELECTION_THRESHOLD
correct_threshold = CORRECTION_THRESHOLD

def get_tokens_from_sentence(sentence: str):
    text_tokens = sentence.split(" ")
    tokens = []
    for index, text_token in enumerate(text_tokens):
        tokens.extend(text_to_virtual_buffer_tokens(text_token + (" " if index < len(text_tokens) - 1 else "")))
    return tokens

def get_matcher() -> VirtualBufferMatcher:
    homophone_contents = "where,wear,ware"
    phonetic_contents = "where,we're,were"
    phonetic_search = PhoneticSearch()
    phonetic_search.set_homophones(homophone_contents)
    phonetic_search.set_phonetic_similiarities(phonetic_contents)
    return VirtualBufferMatcher(phonetic_search)

def get_single_word_match_tree_root(matcher: VirtualBufferMatcher, calculation, submatrix, query_index: int, buffer_index: int) -> VirtualBufferMatch:
    query_word = calculation.words[query_index]
    buffer_word = submatrix.tokens[buffer_index].phrase
    score = matcher.get_memoized_similarity_score(query_word, buffer_word)
    match_tree =  VirtualBufferMatch([[query_index]], [[buffer_index]], [calculation.words[query_index]], [submatrix.tokens[buffer_index].phrase], [score], max_score_per_word)
    match_tree.reduce_potential(max_score_per_word, score, calculation.weights[query_index])
    return match_tree

def test_no_matches_for_too_high_threshold(assertion):
    matcher = get_matcher()

    assertion("Using the query 'an incredible' on 'test with the incredibly good match' and an impossibly high threshold")
    calculation = matcher.generate_match_calculation(["an", "incredible"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    matcher.find_potential_submatrices(calculation, submatrix)
    matches = matcher.find_matches_in_matrix(calculation, submatrix, max_score_per_word)
    assertion("    should give no possible matches", len(matches) == 0)

def test_one_match_for_highest_threshold(assertion):
    matcher = get_matcher()

    assertion("Using the query 'an incredible' on 'test with the incredibly good match' and a threshold which will only reach one match")
    calculation = matcher.generate_match_calculation(["an", "incredible"], correct_threshold, purpose="correction")
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    matcher.find_potential_submatrices(calculation, submatrix)

    matches = matcher.find_matches_in_matrix(calculation, submatrix, 0)
    assertion("    should give 1 possible match with single tokens", len([match for match in matches if len(match.buffer) == 2 and len(match.query_indices) == 2]) == 1)

def test_multiple_single_matches(assertion):
    matcher = get_matcher()

    assertion("Using the query 'an incredible' on 'test with the incredibly good match' and a threshold which will only reach one match")
    calculation = matcher.generate_match_calculation(["an", "incredible"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match which had an incredible run up to"))
    matcher.find_potential_submatrices(calculation, submatrix)
    matches = matcher.find_matches_in_matrix(calculation, submatrix, select_threshold)
    assertion("    should give 1 possible match with single tokens", len([match for match in matches if len(match.buffer) == 2 and len(match.query_indices) == 2]) == 1)
    assertion("    should have 'an incredible' as the highest match", " ".join([match for match in matches if len(match.buffer) == 2][0].buffer) == "an incredible")
    assertion( " ".join([match for match in matches if len(match.buffer) == 2][0].buffer) )

def test_sorting_matches_for_selection(assertion):
    matcher = get_matcher()

    match_1 = VirtualBufferMatch([[0], [1]], [[0], [1]], ["this", "is"], ["this", "is"], [EXACT_MATCH, EXACT_MATCH], EXACT_MATCH, 0)
    match_2 = VirtualBufferMatch([[0], [1]], [[10], [11]], ["this", "is"], ["this", "is"], [EXACT_MATCH, EXACT_MATCH], EXACT_MATCH, 0)
    match_2_missing_one = VirtualBufferMatch([[0], [1]], [[10]], ["this", "is"], ["this"], [EXACT_MATCH], EXACT_MATCH, 0)    
    match_2_homophone = VirtualBufferMatch([[0], [1]], [[10], [11]], ["dis", "is"], ["this", "is"], [HOMOPHONE_MATCH, EXACT_MATCH], EXACT_MATCH - (EXACT_MATCH - HOMOPHONE_MATCH), 0)
    match_1_skip = VirtualBufferMatch([[0], [1]], [[0], [2]], ["this", "the"], ["this", "is", "the"], [EXACT_MATCH, 0, EXACT_MATCH], EXACT_MATCH, 0)
    match_2_skip = VirtualBufferMatch([[0], [1]], [[10], [12]], ["this", "the"], ["this", "is", "the"], [EXACT_MATCH, 0, EXACT_MATCH], EXACT_MATCH, 0)

    assertion("Sorting two matches for selection with where one score is better than the other")
    assertion("    should favour the one with the better score", matcher.compare_match_trees_by_score(match_1, match_2_homophone) == 1)
    assertion("    and the order should not matter", matcher.compare_match_trees_by_score(match_2_homophone, match_1) == -1)
    assertion("Sorting two matches for selection with the same score, but one has more matches")
    assertion("    should favour the one with the most matches", matcher.compare_match_trees_by_score(match_1, match_2_missing_one) == 1)
    assertion("    and the order should not matter", matcher.compare_match_trees_by_score(match_2_missing_one, match_1) == -1)
    assertion("Sorting two matches for selection with the same score and no skips")
    assertion("    should result in no change in the order", matcher.compare_match_trees_by_score(match_1, match_2) == 0)
    assertion("    and the order should not matter", matcher.compare_match_trees_by_score(match_2, match_1) == 0)    
    assertion("Sorting two matches for selection with the same score and the same amount of skips")
    assertion("    should result in no change in the order", matcher.compare_match_trees_by_score(match_1_skip, match_2_skip) == 0)
    assertion("    and the order should not matter", matcher.compare_match_trees_by_score(match_2_skip, match_1_skip) == 0)
    assertion("Sorting two matches for selection with the same score with one having more skips than the other")
    assertion("    should favour the one with the least skips", matcher.compare_match_trees_by_score(match_1, match_2_skip) == 1)
    assertion("    and the order should not matter", matcher.compare_match_trees_by_score(match_2_skip, match_1) == -1)

def test_sorting_matches_for_correction(assertion):
    matcher = get_matcher()

    match_1 = VirtualBufferMatch([[0], [1]], [[0], [1]], ["this", "is"], ["this", "is"], [EXACT_MATCH, EXACT_MATCH], EXACT_MATCH, 8)
    match_2 = VirtualBufferMatch([[0], [1]], [[1], [2]], ["this", "is"], ["this", "is"], [EXACT_MATCH, EXACT_MATCH], EXACT_MATCH, 7)
    match_3 = VirtualBufferMatch([[0], [1]], [[7], [8]], ["this", "is"], ["this", "is"], [EXACT_MATCH, EXACT_MATCH], EXACT_MATCH, 2)

    match_2_missing_one = VirtualBufferMatch([[0], [1]], [[1]], ["this", "is"], ["this"], [EXACT_MATCH], EXACT_MATCH, 8)
    match_2_homophone = VirtualBufferMatch([[0], [1]], [[1], [2]], ["dis", "is"], ["this", "is"], [HOMOPHONE_MATCH, EXACT_MATCH], EXACT_MATCH - (EXACT_MATCH - HOMOPHONE_MATCH), 7)
    match_3_homophone = VirtualBufferMatch([[0], [1]], [[7], [8]], ["dis", "is"], ["this", "is"], [HOMOPHONE_MATCH, EXACT_MATCH], EXACT_MATCH - (EXACT_MATCH - HOMOPHONE_MATCH), 2)
    match_1_skip = VirtualBufferMatch([[0], [1]], [[0], [2]], ["this", "the"], ["this", "is", "the"], [EXACT_MATCH, 0, EXACT_MATCH], EXACT_MATCH, 7)
    match_2_skip = VirtualBufferMatch([[0], [1]], [[1], [3]], ["this", "the"], ["this", "is", "the"], [EXACT_MATCH, 0, EXACT_MATCH], EXACT_MATCH, 6)
    match_3_skip = VirtualBufferMatch([[0], [1]], [[6], [8]], ["this", "the"], ["this", "is", "the"], [EXACT_MATCH, 0, EXACT_MATCH], EXACT_MATCH, 2)

    assertion("Sorting two matches for correction where an overlap occurs with where one score is better than the other")
    assertion("    should favour the one with the better score", matcher.compare_match_trees_for_correction(match_1, match_2_homophone) == 1)
    assertion("    and the order should not matter", matcher.compare_match_trees_for_correction(match_2_homophone, match_1) == -1)
    assertion("Sorting two matches for correction where an overlap occurs with the same score, but one has more matches")
    assertion("    should favour the one with the most matches", matcher.compare_match_trees_for_correction(match_1, match_2_missing_one) == 1)
    assertion("    and the order should not matter", matcher.compare_match_trees_for_correction(match_2_missing_one, match_1) == -1)
    assertion("Sorting two matches for correction where an overlap occurs with the same score and no skips")
    assertion("    should result in no change in the order", matcher.compare_match_trees_for_correction(match_1, match_2) == 0)
    assertion("    and the order should not matter", matcher.compare_match_trees_for_correction(match_2, match_1) == 0)    
    assertion("Sorting two matches for correction where an overlap occurs with the same score and the same amount of skips")
    assertion("    should result in no change in the order", matcher.compare_match_trees_for_correction(match_1_skip, match_2_skip) == 0)
    assertion("    and the order should not matter", matcher.compare_match_trees_for_correction(match_2_skip, match_1_skip) == 0)
    assertion("Sorting two matches for correction where an overlap occurs with the same score with one having more skips than the other")
    assertion("    should favour the one with the least skips", matcher.compare_match_trees_for_correction(match_1, match_2_skip) == 1)
    assertion("    and the order should not matter", matcher.compare_match_trees_for_correction(match_2_skip, match_1) == -1)

    assertion("Sorting two matches for correction where no overlap occurs but there is a score difference")
    assertion("    should favour the one with the shortest distance even if the other has a higher score", matcher.compare_match_trees_for_correction(match_1, match_3_homophone) == -1)
    assertion("    and the order should not matter", matcher.compare_match_trees_for_correction(match_3_homophone, match_1) == 1)
    assertion("Sorting two matches for correction where no overlap occurs and there is no score difference")
    assertion("    should favour the one with the shortest distance", matcher.compare_match_trees_for_correction(match_1, match_3) == -1)
    assertion("    and the order should not matter", matcher.compare_match_trees_for_correction(match_3, match_1) == 1)
    assertion("Sorting two matches for correction where no overlap occurs but the closest has more skips")
    assertion("    should favour the one with the shortest distance", matcher.compare_match_trees_for_correction(match_1, match_3_skip) == -1)
    assertion("    and the order should not matter", matcher.compare_match_trees_for_correction(match_3_skip, match_1) == 1)

def test_calculating_distance_for_matches(assertion):
    match_1 = VirtualBufferMatch([[0], [1]], [[0], [1]], ["this", "is"], ["this", "is"], [EXACT_MATCH, EXACT_MATCH], EXACT_MATCH, 0)
    match_2 = VirtualBufferMatch([[0], [1]], [[7], [8]], ["this", "is"], ["this", "is"], [EXACT_MATCH, EXACT_MATCH], EXACT_MATCH, 0)    
    match_3 = VirtualBufferMatch([[0], [1]], [[10], [11]], ["this", "is"], ["this", "is"], [EXACT_MATCH, EXACT_MATCH], EXACT_MATCH, 0)

    assertion("If the cursor is on the first token")
    match_1.calculate_distance(0, 0)    
    match_2.calculate_distance(0, 0)
    match_3.calculate_distance(0, 0)
    assertion("    a match starting at token 0 should have a distance of 0", match_1.distance == 0)
    assertion("    a match starting at token 7 should have a distance of 7", match_2.distance == 7)
    assertion("    a match starting at token 10 should have a distance of 10", match_3.distance == 10)

    assertion("If the cursor spreads from the first to the fourth token")
    match_1.calculate_distance(0, 3)    
    match_2.calculate_distance(0, 3)
    match_3.calculate_distance(0, 3)
    assertion("    a match starting at token 0 should have a distance of 0", match_1.distance == 0)
    assertion("    a match starting at token 7 should have a distance of 4", match_2.distance == 4)
    assertion("    a match starting at token 10 should have a distance of 7", match_3.distance == 7)

    assertion("If the cursor is on the last token")
    match_1.calculate_distance(12, 12)
    match_2.calculate_distance(12, 12)
    match_3.calculate_distance(12, 12)
    assertion("    a match ending at token 1 should have a distance of 11", match_1.distance == 11)
    assertion("    a match ending at token 8 should have a distance of 4", match_2.distance == 4)
    assertion("    a match ending at token 11 should have a distance of 1", match_3.distance == 1)

    assertion("If the cursor spreads from the fourth to last token to the last token")
    match_1.calculate_distance(9, 12)
    match_2.calculate_distance(9, 12)
    match_3.calculate_distance(9, 12)
    assertion("    a match ending at token 1 should have a distance of 8", match_1.distance == 8)
    assertion("    a match ending at token 8 should have a distance of 1", match_2.distance == 1)
    assertion("    a match ending at token 11 should have a distance of 0", match_3.distance == 0)

suite = create_test_suite("Virtual buffer matcher submatrix matching")
suite.add_test(test_no_matches_for_too_high_threshold)
suite.add_test(test_one_match_for_highest_threshold)
suite.add_test(test_multiple_single_matches)
suite.add_test(test_sorting_matches_for_selection)
suite.add_test(test_sorting_matches_for_correction)
suite.add_test(test_calculating_distance_for_matches)