from ..matcher import VirtualBufferMatcher
from ...phonetics.phonetics import PhoneticSearch
from ...phonetics.detection import EXACT_MATCH
from ..indexer import text_to_virtual_buffer_tokens
from ..typing import VirtualBufferMatchMatrix, VirtualBufferMatch, VirtualBufferMatchVisitCache, SELECTION_THRESHOLD, CORRECTION_THRESHOLD
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

def get_single_word_match_tree_root(matcher: VirtualBufferMatcher, calculation, submatrix, query_index: int, buffer_index: int) -> VirtualBufferMatch:
    query_word = calculation.words[query_index]
    buffer_word = submatrix.tokens[buffer_index].phrase
    score = matcher.get_memoized_similarity_score(query_word, buffer_word)
    match_tree =  VirtualBufferMatch([[query_index]], [[buffer_index]], [calculation.words[query_index]], [submatrix.tokens[buffer_index].phrase], [score], max_score_per_word)
    match_tree.reduce_potential(max_score_per_word, score, calculation.weights[query_index])
    return match_tree

def get_multiple_query_word_match_tree_root(matcher: VirtualBufferMatcher, calculation, submatrix, query_indices: List[int], buffer_index: int) -> VirtualBufferMatch:
    query_words = [calculation.words[query_index] for query_index in query_indices]
    buffer_word = submatrix.tokens[buffer_index].phrase
    score = matcher.get_memoized_similarity_score("".join(query_words), buffer_word)
    summed_weights = sum([calculation.weights[query_index] for query_index in query_indices])
    match_tree =  VirtualBufferMatch([query_indices], [[buffer_index]], query_words, [submatrix.tokens[buffer_index].phrase], [score], max_score_per_word)
    match_tree.reduce_potential(max_score_per_word, score, summed_weights)
    return match_tree

def get_multiple_buffer_word_match_tree_root(matcher: VirtualBufferMatcher, calculation, submatrix, query_index: int, buffer_indices: List[int]) -> VirtualBufferMatch:
    query_word = calculation.words[query_index]
    buffer_words = [submatrix.tokens[buffer_index].phrase for buffer_index in buffer_indices]
    score = matcher.get_memoized_similarity_score(query_word, "".join(buffer_words))
    summed_weights = calculation.weights[query_index]
    match_tree =  VirtualBufferMatch([[query_index]], [buffer_indices], [query_word], buffer_words, [score], max_score_per_word)
    match_tree.reduce_potential(max_score_per_word, score, summed_weights)
    return match_tree

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
    match_trees, _ = matcher.expand_match_tree_backward(match_tree, calculation, submatrix)
    assertion( match_trees )
    assertion("    should have at least one result after expanding", len(match_trees) > 0 )
    if len(match_trees) > 0:
        assertion("    should have a lower score potential than before", match_trees[0].score_potential < match_tree.score_potential)
        assertion("    should still have a score potential bigger than the threshold", match_trees[0].score_potential >= calculation.match_threshold)
        assertion("    should have two tokens matched", len(match_trees[0].query) == 2 and len(match_trees[0].buffer) == 2)
        assertion("    should have queried 'an incredible'", " ".join(match_trees[0].query) == "an incredible")
        assertion("    should have matched 'the incredibly'", " ".join(match_trees[0].buffer) == "the incredibly")

def test_check_expand_forward(assertion):
    matcher = get_matcher()

    assertion("Using the match 'an' on 'test with the incredibly good match'")
    calculation = matcher.generate_match_calculation(["an", "incredible"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    match_tree = get_single_word_match_tree_root(matcher, calculation, submatrix, 0, 2)
    assertion("    should be able to expand forward", match_tree.can_expand_forward(calculation, submatrix))
    match_trees, _ = matcher.expand_match_tree_forward(match_tree, calculation, submatrix)
    assertion("    should have at least one result after expanding", len(match_trees) > 0)
    if len(match_trees) > 0:
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

def test_expand_skip_one_forward(assertion):
    matcher = get_matcher()

    assertion("Using the match 'with' on 'test with the incredibly good match'")
    assertion("Making sure to use the 'correction' strategy, as the 'selection' strategy does not allow for skips between 2 words")
    calculation = matcher.generate_match_calculation(["with", "incredible"], select_threshold, purpose="correction")
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    match_tree = get_single_word_match_tree_root(matcher, calculation, submatrix, 0, 1)
    assertion("    should be able to expand forward", match_tree.can_expand_forward(calculation, submatrix))
    match_trees, _ = matcher.expand_match_tree_forward(match_tree, calculation, submatrix)
    assertion("    should have at least one result after expanding", len(match_trees) > 0)
    if len(match_trees) > 0:
        match_trees.sort(key=lambda x: x.score_potential, reverse=True)
        assertion("    should have a lower score potential than before", match_trees[0].score_potential < match_tree.score_potential)
        assertion("    should still have a score potential bigger than the threshold", match_trees[0].score_potential >= calculation.match_threshold)
        assertion("    should have two tokens matched", len(match_trees[0].query) == 2 and len(match_trees[0].buffer) == 3 )
        assertion("    should have queried 'with incredible'", " ".join(match_trees[0].query) == "with incredible" )
        assertion("    should have matched 'with the incredibly'", " ".join(match_trees[0].buffer) == "with the incredibly" )

    assertion("Using the match 'incredible' on 'test with the incredibly good match'")
    calculation = matcher.generate_match_calculation(["with", "incredible"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    match_tree = get_single_word_match_tree_root(matcher, calculation, submatrix, 1, 3)
    assertion("    should not be able to expand forward", match_tree.can_expand_forward(calculation, submatrix) == False)

def test_expand_skip_one_backward(assertion):
    matcher = get_matcher()

    assertion("Using the match 'incredible' on 'test with the incredibly good match'")
    assertion("Making sure to use the 'correction' strategy, as the 'selection' strategy does not allow for skips between 2 words")    
    calculation = matcher.generate_match_calculation(["with", "incredible"], select_threshold, purpose="correction")
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    match_tree = get_single_word_match_tree_root(matcher, calculation, submatrix, 1, 3)
    assertion("    should be able to expand backward", match_tree.can_expand_backward(submatrix))
    match_trees, _ = matcher.expand_match_tree_backward(match_tree, calculation, submatrix)
    assertion("    should have at least one result after expanding", len(match_trees) > 0)
    if len(match_trees) > 0:
        match_trees.sort(key=lambda x: x.score_potential, reverse=True)
        assertion("    should have a slighly lower score potential than before, because of the exact match with a skip", match_trees[0].score_potential < match_tree.score_potential)
        assertion("    should still have a score potential bigger than the threshold", match_trees[0].score_potential >= calculation.match_threshold)
        assertion("    should have two tokens matched", len(match_trees[0].query) == 2 and len(match_trees[0].buffer) == 3 )
        assertion("    should have queried 'with incredible'", " ".join(match_trees[0].query) == "with incredible" )
        assertion("    should have matched 'with the incredibly'", " ".join(match_trees[0].buffer) == "with the incredibly" )

    assertion("Using the match 'with' on 'test with the incredibly good match'")
    calculation = matcher.generate_match_calculation(["with", "incredible"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    match_tree = get_single_word_match_tree_root(matcher, calculation, submatrix, 0, 1)
    assertion("    should not be able to expand backward", match_tree.can_expand_backward(submatrix) == False)


def test_fully_combined_query_match_tree(assertion):
    matcher = get_matcher()

    assertion("Using the query 'an incredible' on 'test with the incredibly good match' and a selection threshold")
    assertion("Making sure to use the 'correction' strategy, as the 'selection' strategy does not allow for skips between 2 words")    
    calculation = matcher.generate_match_calculation(["an", "incredible"], select_threshold, purpose="correction")
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    calculation.cache.index_matrix(submatrix)
    match_tree = get_multiple_query_word_match_tree_root(matcher, calculation, submatrix, [0, 1], 2)
    assertion("    should not be able to expand forward", match_tree.can_expand_forward(calculation, submatrix) == False)
    assertion("    should not be able to expand backward", match_tree.can_expand_backward(submatrix) == False)
    match_trees, _ = matcher.expand_match_tree(match_tree, calculation, submatrix)
    assertion("    should not have a single result after expanding due to lower score than individual components", len(match_trees) == 0)

def test_partially_combined_query_match_tree(assertion):
    matcher = get_matcher()

    assertion("Using the query 'an incredible good' on 'test with the incredibly good match' and a selection threshold, starting with 'an incredible'")
    calculation = matcher.generate_match_calculation(["an", "incredible", "good"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    calculation.cache.index_matrix(submatrix)
    match_tree = get_multiple_query_word_match_tree_root(matcher, calculation, submatrix, [0, 1], 3)
    assertion("    should be able to expand forward", match_tree.can_expand_forward(calculation, submatrix))
    assertion("    should not be able to expand backward", match_tree.can_expand_backward(submatrix) == False)
    match_trees, _ = matcher.expand_match_tree(match_tree, calculation, submatrix)
    assertion("    should have a single result after expanding", len(match_trees) == 1)

    assertion("Using the query 'the incredible good' on 'test with the incredibly good match' and a selection threshold, starting with 'incredibly good'")
    calculation = matcher.generate_match_calculation(["the", "incredible", "good"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    match_tree = get_multiple_query_word_match_tree_root(matcher, calculation, submatrix, [1, 2], 3)
    assertion("    should not be able to expand forward", match_tree.can_expand_forward(calculation, submatrix) == False)
    assertion("    should be able to expand backward", match_tree.can_expand_backward(submatrix))
    match_trees, _ = matcher.expand_match_tree(match_tree, calculation, submatrix)
    assertion("    should have a single result after expanding", len(match_trees) == 1)

def test_fully_combined_buffer_match_tree(assertion):
    matcher = get_matcher()

    assertion("Using the query 'incredible' on 'test with the in credible good match' and a selection threshold")
    calculation = matcher.generate_match_calculation(["incredible"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the in credible good match"))
    calculation.cache.index_matrix(submatrix)
    match_tree = get_multiple_buffer_word_match_tree_root(matcher, calculation, submatrix, 0, [3, 4])
    assertion("    should not be able to expand forward", match_tree.can_expand_forward(calculation, submatrix) == False)
    assertion("    should not be able to expand backward", match_tree.can_expand_backward(submatrix) == False)
    match_trees, _ = matcher.expand_match_tree(match_tree, calculation, submatrix)
    assertion("    should have a single result after expanding", len(match_trees) == 1)

def test_partially_combined_buffer_match_tree(assertion):
    matcher = get_matcher()

    assertion("Using the query 'incredible good' on 'test with the in credible good match' and a selection threshold, starting with 'incredible'")
    calculation = matcher.generate_match_calculation(["incredible", "good"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the in credible good match"))
    calculation.cache.index_matrix(submatrix)
    match_tree = get_multiple_buffer_word_match_tree_root(matcher, calculation, submatrix, 0, [3, 4])
    assertion("    should be able to expand forward", match_tree.can_expand_forward(calculation, submatrix))
    assertion("    should not be able to expand backward", match_tree.can_expand_backward(submatrix) == False)
    match_trees, _ = matcher.expand_match_tree(match_tree, calculation, submatrix)
    assertion("    should have at least a single result after expanding", len(match_trees) >= 1)

    assertion("Using the query 'the incredible' on 'test with the in credible good match' and a selection threshold, starting with 'incredible'")
    calculation = matcher.generate_match_calculation(["the", "incredible"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the in credible good match"))
    calculation.cache.index_matrix(submatrix)
    match_tree = get_multiple_buffer_word_match_tree_root(matcher, calculation, submatrix, 1, [3, 4])
    assertion("    should not be able to expand forward", match_tree.can_expand_forward(calculation, submatrix) == False)
    assertion("    should be able to expand backward", match_tree.can_expand_backward(submatrix))
    match_trees, _ = matcher.expand_match_tree(match_tree, calculation, submatrix)
    assertion("    should have at least a single result after expanding", len(match_trees) >= 1)

suite = create_test_suite("Virtual buffer matcher branching")
suite.add_test(test_check_expand_backward)
suite.add_test(test_check_expand_forward)
suite.add_test(test_expand_skip_one_forward)
suite.add_test(test_expand_skip_one_backward)

combined_suite = create_test_suite("Virtual buffer matcher branching for combined tokens")
combined_suite.add_test(test_fully_combined_query_match_tree)
combined_suite.add_test(test_partially_combined_query_match_tree)
combined_suite.add_test(test_fully_combined_buffer_match_tree)
combined_suite.add_test(test_partially_combined_buffer_match_tree)