from ...virtual_buffer.matcher import VirtualBufferMatcher
from ...phonetics.phonetics import PhoneticSearch
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ...virtual_buffer.typing import VirtualBufferMatchVisitCache, VirtualBufferTokenList
from ..test import create_test_suite
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
    token_list = VirtualBufferTokenList(0, get_tokens_from_sentence("is IT true that it could happen to any of us?"))
    cache = get_empty_cache()

    assertion("Using an empty cache")
    assertion("    should generate 1-1:2-2 for the starting branch", cache.get_cache_key(starting_branch[0], starting_branch[1], starting_branch[2], starting_branch[3], token_list) == "1-1:2-2")
    assertion("    should generate 1-1:2-2 for the inverse of the starting branch", cache.get_cache_key(inversed_starting_branch[0], inversed_starting_branch[1], inversed_starting_branch[2], inversed_starting_branch[3], token_list) == "1-1:2-2")
    assertion("    should generate 2-1:3-2 for the second branch", cache.get_cache_key(second_starting_branch[0], second_starting_branch[1], second_starting_branch[2], second_starting_branch[3], token_list) == "2-1:3-2")
    assertion("    should generate 2-1:3-2 for the inverse of the second branch", cache.get_cache_key(second_inversed_starting_branch[0], second_inversed_starting_branch[1], second_inversed_starting_branch[2], second_inversed_starting_branch[3], token_list) == "2-1:3-2")
    assertion("    should generate 1-1:2-3 for the skipped branch", cache.get_cache_key(starting_skipped_branch[0], starting_skipped_branch[1], starting_skipped_branch[2], starting_skipped_branch[3], token_list) == "1-1:2-3")
    assertion("    should generate 1-1:2-3 for the inverse of the skipped branch", cache.get_cache_key(inversed_starting_skipped_branch[0], inversed_starting_skipped_branch[1], inversed_starting_skipped_branch[2], inversed_starting_skipped_branch[3], token_list) == "1-1:2-3")

def test_token_list_indexation(assertion):
    token_list = VirtualBufferTokenList(1, get_tokens_from_sentence("is IT true that it could happen to any of us?"))
    cache = get_empty_cache()
    cache.index_token_list(token_list)
    assertion("Indexing a complete token_list with duplicates")
    assertion("    should generate two indices for the duplicate word", len(cache.word_indices["it"]) == 2)
    assertion("    should generate one index for singular words", len(cache.word_indices["is"]) == 1)
    assertion("    should index with the starting token_list index", cache.word_indices["is"][0] == 1)
    assertion("    should index with the starting token_list index", cache.word_indices["it"] == [2, 5])

def test_skip_word_sequences(assertion):
    token_list = VirtualBufferTokenList(0, get_tokens_from_sentence("is IT true that it could happen to any of us?"))
    cache = get_empty_cache()
    cache.index_token_list(token_list)
    assertion("Skipping 'Is it true' within 'is IT true that it could happen to any of us?'")
    cache.skip_word_sequence(["is", "it", "true"])
    assertion("    should skip the first three indices", ( cache.skip_indices[0] and cache.skip_indices[1] and cache.skip_indices[2] ))
    assertion("    should not skip part of the word that wasn't skipped", cache.skip_indices[4] == False)
    assertion("Skipping 'it' within 'is IT true that it could happen to any of us?'")
    cache.skip_word_sequence(["it"])
    assertion("    should skip the fifth index as well", cache.skip_indices[4] == True)
    assertion("Skipping 'testing'")
    old_sequence = "".join(["1" if index else "0" for index in cache.skip_indices])
    cache.skip_word_sequence(["testing"])
    new_sequence = "".join(["1" if index else "0" for index in cache.skip_indices])
    assertion("    should not change the skip indices because it doesn't exist", old_sequence == new_sequence)

def test_skip_sublists(assertion):
    matcher = get_matcher()
    token_list = VirtualBufferTokenList(0, get_tokens_from_sentence("is IT true that it could happen to any of us?"))
    calculation = matcher.generate_match_calculation(["a", "large", "metal"], 1)
    starting_sublist = token_list.get_sublist(0, 3)
    middle_sublist = token_list.get_sublist(4, 7)
    ending_sublist = token_list.get_sublist(2, 8)
    cache = get_empty_cache()
    cache.index_token_list(token_list)
    assertion("Skipping 'Is it true' and 'it' within 'is IT true that it could happen to any of us?', while searching for 'a large metal'")
    cache.skip_word_sequence(["is", "it", "true"])
    cache.skip_word_sequence(["it"])
    assertion("    should skip the first sublist that contains the skipped phrase", cache.should_skip_sublist(starting_sublist, calculation))
    assertion("    should not skip the middle sublist that contains a small skipped phrase", cache.should_skip_sublist(middle_sublist, calculation) == False)
    assertion("    should not skip the ending sublist that contains parts of both phrases but has enough to match", cache.should_skip_sublist(ending_sublist, calculation) == False)

suite = create_test_suite("Virtual buffer branch skipping")
suite.add_test(test_key_generation)
suite.add_test(test_token_list_indexation)
suite.add_test(test_skip_word_sequences)
suite.add_test(test_skip_sublists)