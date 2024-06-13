from ..matcher import VirtualBufferMatcher
from ...phonetics.phonetics import PhoneticSearch
from ...phonetics.detection import EXACT_MATCH
from ..indexer import text_to_virtual_buffer_tokens
from ..typing import VirtualBufferMatchMatrix, VirtualBufferMatch, SELECTION_THRESHOLD, CORRECTION_THRESHOLD
from ...utils.test import create_test_suite
from typing import List

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

def get_multiple_query_word_match_tree_root(matcher: VirtualBufferMatcher, calculation, submatrix, query_indices: List[int], buffer_index: int) -> VirtualBufferMatch:
    query_words = [calculation.words[query_index] for query_index in query_indices]
    buffer_word = submatrix.tokens[buffer_index].phrase
    score = matcher.get_memoized_similarity_score("".join(query_words), buffer_word)
    summed_weights = sum([calculation.weights[query_index] for query_index in query_indices])
    match_tree =  VirtualBufferMatch([query_indices], [[buffer_index]], query_words, [submatrix.tokens[buffer_index].phrase], [score], max_score_per_word)
    match_tree.reduce_potential(max_score_per_word, score, summed_weights)
    return match_tree

def test_fully_combined_match_tree(assertion):
    matcher = get_matcher()

    assertion("Using the query 'an incredible' on 'test with the incredibly good match' and an impossibly high threshold")
    calculation = matcher.generate_match_calculation(["an", "incredible"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    match_tree = get_multiple_query_word_match_tree_root(matcher, calculation, submatrix, [0, 1], 2)
    assertion("    should not be able to expand forward", match_tree.can_expand_forward(calculation, submatrix) == False)
    assertion("    should not be able to expand backward", match_tree.can_expand_backward(submatrix) == False)
    match_trees = matcher.expand_match_tree(match_tree, calculation, submatrix)
    assertion("    should have a single result after expanding", len(match_trees) == 1)

def test_partially_combined_match_tree(assertion):
    matcher = get_matcher()

    assertion("Using the query 'an incredible good' on 'test with the incredibly good match' and an impossibly high threshold")
    calculation = matcher.generate_match_calculation(["an", "incredible", "good"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    match_tree = get_multiple_query_word_match_tree_root(matcher, calculation, submatrix, [0, 1], 3)
    assertion("    should be able to expand forward", match_tree.can_expand_forward(calculation, submatrix))
    assertion("    should not be able to expand backward", match_tree.can_expand_backward(submatrix) == False)
    match_trees = matcher.expand_match_tree(match_tree, calculation, submatrix)
    assertion("    should have a single result after expanding", len(match_trees) == 1)
    assertion( match_trees )

suite = create_test_suite("Virtual buffer matcher branching for combined tokens")
#suite.add_test(test_fully_combined_match_tree)
suite.add_test(test_partially_combined_match_tree)
suite.run()