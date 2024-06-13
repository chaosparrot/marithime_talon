from ..matcher import VirtualBufferMatcher
from ...phonetics.phonetics import PhoneticSearch
from ...phonetics.detection import EXACT_MATCH
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
    matches = matcher.find_matches_in_matrix(calculation, submatrix, max_score_per_word)
    assertion("    should give no possible matches", len(matches) == 0)

def test_one_match_for_highest_threshold(assertion):
    matcher = get_matcher()

    assertion("Using the query 'an incredible' on 'test with the incredibly good match' and a threshold which will only reach one match")
    calculation = matcher.generate_match_calculation(["an", "incredible"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match"))
    matches = matcher.find_matches_in_matrix(calculation, submatrix, select_threshold)
    assertion("    should give 1 possible match with single tokens", len([match for match in matches if len(match.buffer) == 2]) == 1)

def test_multiple_single_matches(assertion):
    matcher = get_matcher()

    assertion("Using the query 'an incredible' on 'test with the incredibly good match' and a threshold which will only reach one match")
    calculation = matcher.generate_match_calculation(["an", "incredible"], select_threshold)
    submatrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("test with the incredibly good match which had an incredible run up to"))
    matches = matcher.find_matches_in_matrix(calculation, submatrix, select_threshold)
    assertion("    should give 2 possible matches with single tokens", len([match for match in matches if len(match.buffer) == 2]) == 2)
    assertion("    should have 'an incredible' as the highest match", " ".join([match for match in matches if len(match.buffer) == 2][0].buffer) == "an incredible")
    assertion( " ".join([match for match in matches if len(match.buffer) == 2][0].buffer) )

suite = create_test_suite("Virtual buffer matcher submatrix matching")
suite.add_test(test_no_matches_for_too_high_threshold)
suite.add_test(test_one_match_for_highest_threshold)
suite.add_test(test_multiple_single_matches)
suite.run()