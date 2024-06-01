from ..matcher import VirtualBufferMatcher
from ...phonetics.phonetics import PhoneticSearch
from ..indexer import text_to_virtual_buffer_tokens
from ..typing import VirtualBufferMatchMatrix, VirtualBufferMatch
from ...utils.test import create_test_suite
from typing import List

max_score_per_word = 3
select_threshold = 0.66

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
    matches = matcher.find_matches_in_matrix(calculation, submatrix, max_score_per_word * 3)
    assertion("    should give no possible matches", len(matches) == 0)

def test_one_match_for_highest_threshold(assertion):
    matcher = get_matcher()

    assertion("Using the query 'an incredible' on 'test with the incredibly good match' and a threshold which will only reach one match")
    calculation = matcher.generate_match_calculation(["an", "incredible"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    matches = matcher.find_matches_in_matrix(calculation, submatrix, max_score_per_word * 2 / 3)
    assertion("    should give 1 possible match", len(matches) == 1)

def test_check_expand_backward(assertion):
    matcher = get_matcher()

    assertion("Using the match 'an' on 'test with the incredibly good match'")
    calculation = matcher.generate_match_calculation(["an", "incredible"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    match_tree = get_single_word_match_tree_root(matcher, calculation, submatrix, 0, 3)
    assertion("    should not be able to expand backward", match_tree.can_expand_backward(submatrix) == False)

    assertion("Using the match 'incredible' on 'test with the incredibly good match'")
    calculation = matcher.generate_match_calculation(["an", "incredible"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    match_tree = get_single_word_match_tree_root(matcher, calculation, submatrix, 1, 3)
    assertion("    should be able to expand backward", match_tree.can_expand_backward(submatrix))
    match_trees = matcher.expand_match_tree_backward(match_tree, calculation, submatrix)
    assertion("    should have one result after expanding", len(match_trees))
    assertion("    should have a lower score potential than before", match_trees[0].score_potential < match_tree.score_potential)
    assertion("    should still have a score potential bigger than the threshold", match_trees[0].score_potential >= calculation.match_threshold)
    assertion("    should have two tokens matched", len(match_trees[0].query) == 2 and len(match_trees[0].buffer) == 2)
    assertion("    should have queried 'an incredible'", " ".join(match_trees[0].query) == "an incredible")
    assertion("    should have matched 'the incredibly'", " ".join(match_trees[0].buffer) == "the incredibly")    

    # TODO CHECK EXPAND BACKWARD RESULT

def test_check_expand_forward(assertion):
    matcher = get_matcher()

    assertion("Using the match 'an' on 'test with the incredibly good match'")
    calculation = matcher.generate_match_calculation(["an", "incredible"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    match_tree = get_single_word_match_tree_root(matcher, calculation, submatrix, 0, 2)
    assertion("    should be able to expand forward", match_tree.can_expand_forward(calculation, submatrix))
    match_trees = matcher.expand_match_tree_forward(match_tree, calculation, submatrix)
    assertion("    should have one result after expanding", len(match_trees))
    assertion("    should have a lower score potential than before", match_trees[0].score_potential < match_tree.score_potential)
    assertion("    should still have a score potential bigger than the threshold", match_trees[0].score_potential >= calculation.match_threshold)
    assertion("    should have two tokens matched", len(match_trees[0].query) == 2 and len(match_trees[0].buffer) == 2 )
    assertion("    should have queried 'an incredible'", " ".join(match_trees[0].query) == "an incredible" )
    assertion("    should have matched 'the incredibly'", " ".join(match_trees[0].buffer) == "the incredibly" )

    assertion("Using the match 'incredible' on 'test with the incredibly good match'")
    calculation = matcher.generate_match_calculation(["an", "incredible"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    match_tree = get_single_word_match_tree_root(matcher, calculation, submatrix, 1, 3)
    assertion("    should not be able to expand forward", match_tree.can_expand_forward(calculation, submatrix) == False)
    # TODO CHECK EXPAND FORWARD RESULT

suite = create_test_suite("Virtual buffer matcher branching")
suite.add_test(test_check_expand_backward) 
suite.add_test(test_check_expand_forward)
#suite.add_test(test_no_matches_for_too_high_threshold)
#suite.add_test(test_one_match_for_highest_threshold)
suite.run() 