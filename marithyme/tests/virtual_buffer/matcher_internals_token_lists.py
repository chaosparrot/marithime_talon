from ...virtual_buffer.matcher import VirtualBufferMatcher
from ...phonetics.phonetics import PhoneticSearch
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ...virtual_buffer.typing import VirtualBufferTokenList, VirtualBufferMatchCalculation
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

def get_single_branches(calculation: VirtualBufferMatchCalculation) -> List[List[int]]:
    return [branch for branch in calculation.get_possible_branches() if len(branch) == 1]

def get_double_branches(calculation: VirtualBufferMatchCalculation) -> List[List[int]]:
    return [branch for branch in calculation.get_possible_branches() if len(branch) > 1]

def test_empty_potential_sublists(assertion):
    matcher = get_matcher()

    assertion("Using the mixed syllable words 'An incredible' and searching a token_list without a match for incredible")
    calculation = matcher.generate_match_calculation(["an", "incredible"], 1)
    token_list = VirtualBufferTokenList(0, get_tokens_from_sentence("this is a large test with a bunch of connections"))
    calculation.cache.index_token_list(token_list)
    sublists, _ = matcher.find_potential_sublists(calculation, token_list, [])
    assertion("    should not give a single possible sublist", len(sublists) == 0) # 1 if impossible branching isn't fixed! )

def test_single_potential_sublists(assertion):
    matcher = get_matcher()

    assertion("Using the mixed syllable words 'An incredible' and searching a token_list with a match for incredible")
    calculation = matcher.generate_match_calculation(["an", "incredible"], 1)
    token_list = VirtualBufferTokenList(0, get_tokens_from_sentence("this is a large test with the incredibly good match that can"))
    calculation.cache.index_token_list(token_list)
    sublists, _ = matcher.find_potential_sublists(calculation, token_list, [])
    assertion("    should give a single possible sublist", len(sublists) == 1)
    assertion("    should start 3 indecis from the start", sublists[0].index == 3)
    assertion("    should start 2 indecis from the end", sublists[0].index + len(sublists[0].tokens) == 10)

    assertion("Using the mixed syllable words 'An incredible' and searching a token_list with a match for incredible clipped at the end")
    second_token_list = VirtualBufferTokenList(0, get_tokens_from_sentence("this is a large test with the incredibly good"))
    sublists, _ = matcher.find_potential_sublists(calculation, second_token_list, [])
    assertion("    should give a single possible sublist", len(sublists) == 1)
    # Fix when impossible branches is readded
    assertion("    should start 3 indecis from the start", sublists[0].index == 3)
    assertion("    should start 0 indecis from the end", sublists[0].index + len(sublists[0].tokens) == 9)

    assertion("Using the mixed syllable words 'An incredible' and searching a token_list with a match for incredible clipped at the start")
    second_token_list = VirtualBufferTokenList(0, get_tokens_from_sentence("the incredibly good match that can"))
    sublists, _ = matcher.find_potential_sublists(calculation, second_token_list, [])
    assertion("    should give a single possible sublist", len(sublists) == 1)
    assertion("    should start 0 indecis from the start", sublists[0].index == 0)
    # Fix when impossible branches is readded
    assertion("    should start 2 indecis from the end", sublists[0].index + len(sublists[0].tokens) == 4)

def test_can_merge_token_lists(assertion):
    matcher = get_matcher()

    assertion("Using multiple token_lists that overlap")
    token_list0_2 = VirtualBufferTokenList(0, get_tokens_from_sentence("an incredibly dense"))
    token_list1_3 = VirtualBufferTokenList(1, get_tokens_from_sentence("an incredibly dense"))
    token_list2_4 = VirtualBufferTokenList(2, get_tokens_from_sentence("an incredibly dense"))
    token_list3_5 = VirtualBufferTokenList(3, get_tokens_from_sentence("an incredibly dense"))    
    token_list100_102 = VirtualBufferTokenList(100, get_tokens_from_sentence("an incredibly dense"))

    assertion("    should allow merges between 0_2 and 1_3", matcher.can_merge_token_lists(token_list0_2, token_list1_3))
    assertion("    should allow merges between 0_2 and 2_4", matcher.can_merge_token_lists(token_list0_2, token_list2_4))
    assertion("    should not allow merges between 0_2 and 3_5", not matcher.can_merge_token_lists(token_list0_2, token_list3_5))    
    assertion("    should not allow merges between 0_2 and 100_103", not matcher.can_merge_token_lists(token_list0_2, token_list100_102))
    assertion("    should allow merges between 1_3 and 0_2", matcher.can_merge_token_lists(token_list1_3, token_list0_2))
    assertion("    should allow merges between 1_3 and 3_5", matcher.can_merge_token_lists(token_list1_3, token_list3_5))
    assertion("    should not allow merges between 1_3 and 100_103", not matcher.can_merge_token_lists(token_list1_3, token_list100_102))
    assertion("    should not allow merges between 100_102 and 0_2", not matcher.can_merge_token_lists(token_list100_102, token_list0_2))
    assertion("    should not allow merges between 100_102 and 1_3", not matcher.can_merge_token_lists(token_list100_102, token_list1_3))
    assertion("    should not allow merges between 100_102 and 2_4", not matcher.can_merge_token_lists(token_list100_102, token_list2_4))
    assertion("    should not allow merges between 100_102 and 3_5", not matcher.can_merge_token_lists(token_list100_102, token_list3_5)) 

def test_merge_token_lists(assertion):
    matcher = get_matcher()

    assertion("Using multiple token_lists that overlap (an incredibly dense) with (incredibly dense cake)")
    token_list0_2 = VirtualBufferTokenList(0, get_tokens_from_sentence("an incredibly dense"))
    token_list1_3 = VirtualBufferTokenList(1, get_tokens_from_sentence("incredibly dense cake"))
    merged_token_list = matcher.merge_token_lists(token_list0_2, token_list1_3)
    assertion("    should have the token_list start at 0", merged_token_list.index == 0)
    assertion("    should have the token_list end at 2", merged_token_list.end_index == 3)
    assertion("    should start with 'an'", merged_token_list.tokens[0].phrase == "an")
    assertion("    should end with 'cake'", merged_token_list.tokens[-1].phrase == "cake")
    assertion("    should have four tokens", len(merged_token_list.tokens) == 4)

    assertion("Swapping these token_lists around should result in the same outcome")
    merged_token_list = matcher.merge_token_lists(token_list1_3, token_list0_2)
    assertion("    should have the token_list start at 0", merged_token_list.index == 0)
    assertion("    should have the token_list end at 2", merged_token_list.end_index == 3)
    assertion("    should start with 'an'", merged_token_list.tokens[0].phrase == "an")
    assertion("    should end with 'cake'", merged_token_list.tokens[-1].phrase == "cake")
    assertion("    should have four tokens", len(merged_token_list.tokens) == 4)

def test_merge_token_lists_at_end(assertion):
    matcher = get_matcher()

    assertion("Using multiple token_lists that touch at the end (an incredibly dense) with (cake that will)")
    token_list0_2 = VirtualBufferTokenList(0, get_tokens_from_sentence("an incredibly dense"))
    token_list3_5 = VirtualBufferTokenList(3, get_tokens_from_sentence("cake that will"))
    merged_token_list = matcher.merge_token_lists(token_list0_2, token_list3_5)
    assertion("    should have the token_list start at 0", merged_token_list.index == 0)
    assertion("    should have the token_list end at 2", merged_token_list.end_index == 5)
    assertion("    should start with 'an'", merged_token_list.tokens[0].phrase == "an")
    assertion("    should end with 'will'", merged_token_list.tokens[-1].phrase == "will")
    assertion("    should have six tokens", len(merged_token_list.tokens) == 6)

    assertion("Swapping these token_lists around should result in the same outcome")
    merged_token_list = matcher.merge_token_lists(token_list3_5, token_list0_2)
    assertion("    should have the token_list start at 0", merged_token_list.index == 0)
    assertion("    should have the token_list end at 2", merged_token_list.end_index == 5)
    assertion("    should start with 'an'", merged_token_list.tokens[0].phrase == "an")
    assertion("    should end with 'will'", merged_token_list.tokens[-1].phrase == "will")
    assertion("    should have six tokens", len(merged_token_list.tokens) == 6)

def test_merge_token_lists_overlapping_token_lists_end(assertion):
    matcher = get_matcher()

    assertion("Using multiple token_lists that completely envelop one another (an incredibly dense) with (dense)")
    token_list0_2 = VirtualBufferTokenList(0, get_tokens_from_sentence("an incredibly dense"))
    token_list2_2 = VirtualBufferTokenList(2, get_tokens_from_sentence("dense"))
    merged_token_list = matcher.merge_token_lists(token_list0_2, token_list2_2)
    assertion("    should have the token_list start at 0", merged_token_list.index == 0)
    assertion("    should have the token_list end at 2", merged_token_list.end_index == 2)
    assertion("    should start with 'an'", merged_token_list.tokens[0].phrase == "an")
    assertion("    should end with 'dense'", merged_token_list.tokens[-1].phrase == "dense")
    assertion("    should have three tokens", len(merged_token_list.tokens) == 3)

    assertion("Swapping these token_lists around should result in the same outcome")
    merged_token_list = matcher.merge_token_lists(token_list2_2, token_list0_2)
    assertion("    should have the token_list start at 0", merged_token_list.index == 0)
    assertion("    should have the token_list end at 2", merged_token_list.end_index == 2)
    assertion("    should start with 'an'", merged_token_list.tokens[0].phrase == "an")
    assertion("    should end with 'dense'", merged_token_list.tokens[-1].phrase == "dense")
    assertion("    should have three tokens", len(merged_token_list.tokens) == 3)

def test_merge_token_lists_overlapping_token_lists_start(assertion):
    matcher = get_matcher()

    assertion("Using multiple token_lists that completely envelop one another (an incredibly dense) with (an)")
    token_list0_2 = VirtualBufferTokenList(0, get_tokens_from_sentence("an incredibly dense"))
    token_list0_0 = VirtualBufferTokenList(0, get_tokens_from_sentence("an"))
    merged_token_list = matcher.merge_token_lists(token_list0_2, token_list0_0)
    assertion("    should have the token_list start at 0", merged_token_list.index == 0)
    assertion("    should have the token_list end at 2", merged_token_list.end_index == 2)
    assertion("    should start with 'an'", merged_token_list.tokens[0].phrase == "an")
    assertion("    should end with 'dense'", merged_token_list.tokens[-1].phrase == "dense")
    assertion("    should have three tokens", len(merged_token_list.tokens) == 3)

    assertion("Swapping these token_lists around should result in the same outcome")
    merged_token_list = matcher.merge_token_lists(token_list0_0, token_list0_2)
    assertion("    should have the token_list start at 0", merged_token_list.index == 0)
    assertion("    should have the token_list end at 2", merged_token_list.end_index == 2)
    assertion("    should start with 'an'", merged_token_list.tokens[0].phrase == "an")
    assertion("    should end with 'dense'", merged_token_list.tokens[-1].phrase == "dense")
    assertion("    should have three tokens", len(merged_token_list.tokens) == 3)

def test_merge_token_lists_overlapping_token_lists_middle(assertion):
    matcher = get_matcher()

    assertion("Using multiple token_lists that completely envelop one another (an incredibly dense) with (an)")
    token_list0_2 = VirtualBufferTokenList(0, get_tokens_from_sentence("an incredibly dense"))
    token_list1_1 = VirtualBufferTokenList(0, get_tokens_from_sentence("incredibly"))
    merged_token_list = matcher.merge_token_lists(token_list0_2, token_list1_1)
    assertion("    should have the token_list start at 0", merged_token_list.index == 0)
    assertion("    should have the token_list end at 2", merged_token_list.end_index == 2)
    assertion("    should start with 'an'", merged_token_list.tokens[0].phrase == "an")
    assertion("    should end with 'dense'", merged_token_list.tokens[-1].phrase == "dense")
    assertion("    should have three tokens", len(merged_token_list.tokens) == 3)

    assertion("Swapping these token_lists around should result in the same outcome")
    merged_token_list = matcher.merge_token_lists(token_list1_1, token_list0_2)
    assertion("    should have the token_list start at 0", merged_token_list.index == 0)
    assertion("    should have the token_list end at 2", merged_token_list.end_index == 2)
    assertion("    should start with 'an'", merged_token_list.tokens[0].phrase == "an")
    assertion("    should end with 'dense'", merged_token_list.tokens[-1].phrase == "dense")
    assertion("    should have three tokens", len(merged_token_list.tokens) == 3)

def test_translate_sub_token_list_index_to_token_list_index(assertion):
    assertion("Translating a resulting index of a sub token_list back to a token_list index")
    token_list0_2 = VirtualBufferTokenList(0, get_tokens_from_sentence("an incredibly dense"))
    assertion("    0 should be 0 when the token_list start at 0", token_list0_2.to_global_index(0) == 0)
    assertion("    1 should be 1 when the token_list start at 0", token_list0_2.to_global_index(1) == 1)
    assertion("    2 should be 2 when the token_list start at 0", token_list0_2.to_global_index(2) == 2)
    token_list1_2 = VirtualBufferTokenList(1, get_tokens_from_sentence("an incredibly dense"))
    assertion("    0 should be 1 when the token_list start at 0", token_list1_2.to_global_index(0) == 1)
    assertion("    1 should be 2 when the token_list start at 0", token_list1_2.to_global_index(1) == 2)
    assertion("    2 should be 3 when the token_list start at 0", token_list1_2.to_global_index(2) == 3)
    token_list99_2 = VirtualBufferTokenList(99, get_tokens_from_sentence("an incredibly dense"))
    assertion("    0 should be 99 when the token_list start at 99", token_list99_2.to_global_index(0) == 99)
    assertion("    1 should be 100 when the token_list start at 99", token_list99_2.to_global_index(1) == 100)
    assertion("    2 should be 101 when the token_list start at 99", token_list99_2.to_global_index(2) == 101)

token_list0_2 = VirtualBufferTokenList(0, get_tokens_from_sentence("an incredibly dense"))
token_list3_5 = VirtualBufferTokenList(3, get_tokens_from_sentence("piece of cake"))
token_list6_8 = VirtualBufferTokenList(6, get_tokens_from_sentence("that, upon inspection,"))
token_list9_9 = VirtualBufferTokenList(9, get_tokens_from_sentence("cannot"))
token_list10_10 = VirtualBufferTokenList(10, get_tokens_from_sentence("even"))    
token_list11_12 = VirtualBufferTokenList(11, get_tokens_from_sentence("decompose naturally"))
sublist_list = [token_list0_2, token_list3_5, token_list6_8, token_list9_9, token_list10_10, token_list11_12]

def test_split_token_lists_at_start(assertion):
    matcher = get_matcher()
    assertion("Splitting a list of 6 sublists at the start on the first token")
    split = matcher.split_sublists_by_cursor_position(sublist_list, 0, 0)
    assertion("    should not have sublists before the cursor", len(split[0]) == 0)
    assertion("    should have one sublist in the current list", len(split[1]) == 1)
    assertion("    should have 5 sublists in the after list", len(split[2]) == 5)

    assertion("Splitting a list of 6 sublists at the start on the first five tokens")
    split = matcher.split_sublists_by_cursor_position(sublist_list, 0, 4)
    assertion("    should not have sublists before the cursor", len(split[0]) == 0)
    assertion("    should have 2 sublists in the current list", len(split[1]) == 2)
    assertion("    should have 4 sublists in the after list", len(split[2]) == 4)

def test_split_token_lists_at_end(assertion):
    matcher = get_matcher()
    assertion("Splitting a list of 6 sublists at the end on the first token")
    split = matcher.split_sublists_by_cursor_position(sublist_list, 12, 12)
    assertion("    should have 5 sublists before the cursor", len(split[0]) == 5)
    assertion("    should have one sublist in the current list", len(split[1]) == 1)
    assertion("    should not have sublists in the after list", len(split[2]) == 0)
    assertion("    should sort the before list in reverse order", split[0][0].end_index > split[0][-1].end_index)

    assertion("Splitting a list of 6 sublists at the end on the last four tokens")
    split = matcher.split_sublists_by_cursor_position(sublist_list, 9, 12)
    assertion("    should have 3 sublists before the cursor", len(split[0]) == 3)
    assertion("    should have 3 sublists in the current list", len(split[1]) == 3)
    assertion("    should not have sublists in the after list", len(split[2]) == 0)
    assertion("    should sort the before list in reverse order", split[0][0].end_index > split[0][-1].end_index)

def test_split_token_lists_in_the_middle(assertion):
    matcher = get_matcher()
    assertion("Splitting a list of 6 sublists at the middle on the middle token")
    split = matcher.split_sublists_by_cursor_position(sublist_list, 6, 6)
    assertion("    should have 2 sublists before the cursor", len(split[0]) == 2)
    assertion("    should have one sublist in the current list", len(split[1]) == 1)
    assertion("    should have 3 sublists in the after list", len(split[2]) == 3)
    assertion("    should sort the before list in reverse order", split[0][0].end_index > split[0][-1].end_index)

    assertion("Splitting a list of 6 sublists at the middle on the middle four tokens")
    split = matcher.split_sublists_by_cursor_position(sublist_list, 6, 9)
    assertion("    should have 2 sublists before the cursor", len(split[0]) == 2)
    assertion("    should have 2 sublists in the current list", len(split[1]) == 2)
    assertion("    should have 2 sublists in the after list", len(split[2]) == 2)
    assertion("    should sort the before list in reverse order", split[0][0].end_index > split[0][-1].end_index)


suite = create_test_suite("Virtual buffer matcher token_list gathering")
suite.add_test(test_empty_potential_sublists)
suite.add_test(test_single_potential_sublists)
suite.add_test(test_can_merge_token_lists)
suite.add_test(test_merge_token_lists)
suite.add_test(test_merge_token_lists_at_end)
suite.add_test(test_merge_token_lists_overlapping_token_lists_end)
suite.add_test(test_merge_token_lists_overlapping_token_lists_start)
suite.add_test(test_merge_token_lists_overlapping_token_lists_middle)
suite.add_test(test_translate_sub_token_list_index_to_token_list_index)

splitting_suite = create_test_suite("Virtual buffer matcher token_list splitting")
splitting_suite.add_test(test_split_token_lists_at_start)
splitting_suite.add_test(test_split_token_lists_at_end)
splitting_suite.add_test(test_split_token_lists_in_the_middle)