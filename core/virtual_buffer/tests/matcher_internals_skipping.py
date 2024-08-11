from ..matcher import VirtualBufferMatcher
from ...phonetics.phonetics import PhoneticSearch
from ..indexer import text_to_virtual_buffer_tokens
from ..typing import VirtualBufferMatchVisitCache
from ...utils.test import create_test_suite
from typing import List

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

def get_empty_cache() -> VirtualBufferMatchVisitCache:
    return VirtualBufferMatchVisitCache()

starting_branch = [[1], [2], [1], [2]]
inversed_starting_branch = [[2], [1], [2], [1]]
second_starting_branch = [[2], [3], [1], [2]]
second_inversed_starting_branch = [[3], [2], [2], [1]]
starting_skipped_branch = [[1], [2], [1], [3]]
inversed_starting_skipped_branch = [[2], [1], [3], [1]]

def test_key_generation(assertion):
    cache = get_empty_cache()

    assertion("Using an empty cache")
    assertion("    should generate 1-1:2-2 for the starting branch", cache.get_cache_key(starting_branch[0], starting_branch[1], starting_branch[2], starting_branch[3]) == "1-1:2-2")
    assertion("    should generate 1-1:2-2 for the inverse of the starting branch", cache.get_cache_key(inversed_starting_branch[0], inversed_starting_branch[1], inversed_starting_branch[2], inversed_starting_branch[3]) == "1-1:2-2")
    assertion("    should generate 2-1:3-2 for the second branch", cache.get_cache_key(second_starting_branch[0], second_starting_branch[1], second_starting_branch[2], second_starting_branch[3]) == "2-1:3-2")
    assertion("    should generate 2-1:3-2 for the inverse of the second branch", cache.get_cache_key(second_inversed_starting_branch[0], second_inversed_starting_branch[1], second_inversed_starting_branch[2], second_inversed_starting_branch[3]) == "2-1:3-2")
    assertion("    should generate 1-1:2-3 for the skipped branch", cache.get_cache_key(starting_skipped_branch[0], starting_skipped_branch[1], starting_skipped_branch[2], starting_skipped_branch[3]) == "1-1:2-3")
    assertion("    should generate 1-1:2-3 for the inverse of the skipped branch", cache.get_cache_key(inversed_starting_skipped_branch[0], inversed_starting_skipped_branch[1], inversed_starting_skipped_branch[2], inversed_starting_skipped_branch[3]) == "1-1:2-3")


suite = create_test_suite("Virtual buffer branch skipping")
suite.add_test(test_key_generation)
suite.run()