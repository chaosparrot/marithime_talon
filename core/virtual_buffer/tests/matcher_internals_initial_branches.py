from ..matcher import VirtualBufferMatcher
from ...phonetics.phonetics import PhoneticSearch
from ..indexer import text_to_virtual_buffer_tokens
from ..typing import VirtualBufferMatchCalculation
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

def get_single_branches(calculation: VirtualBufferMatchCalculation) -> List[List[int]]:
    return [branch for branch in calculation.get_possible_branches() if len(branch) == 1]

def get_double_branches(calculation: VirtualBufferMatchCalculation) -> List[List[int]]:
    return [branch for branch in calculation.get_possible_branches() if len(branch) > 1]

def test_generate_single_match_calculation(assertion):
    matcher = get_matcher()

    assertion("Using the single syllable words 'This is good'")
    calculation = matcher.generate_match_calculation(["This", "is", "good"], 1)
    assertion("    should have weights adding up to 1", 1 - sum(calculation.weights) < 0.0001)
    assertion("    should have balanced weights", 0.333 - calculation.weights[0] < 0.001)    
    assertion("    should return three possible single branches", len(get_single_branches(calculation)) == 3)
    assertion("    should not alter the single branch sorting", get_single_branches(calculation) == [[0], [1], [2]])
    assertion("    should return two possible double branches", len(get_double_branches(calculation)) == 2)

def test_generate_double_match_calculation(assertion):
    matcher = get_matcher()

    assertion("Using the mixed syllable words 'Checkens running afoul'")
    calculation = matcher.generate_match_calculation(["Chickens", "running", "afoul"], 1)
    assertion("    should have weights adding up to 1", 1 - sum(calculation.weights) < 0.0001)
    assertion("    should have balanced weights",  0.333 - calculation.weights[0] < 0.001)
    assertion("    should return three possible branches", len(get_single_branches(calculation)) == 3)
    assertion("    should not alter the sorting", get_single_branches(calculation) == [[0], [1], [2]])
    assertion("    should return two possible double branches", len(get_double_branches(calculation)) == 2)    

def test_generate_mixed_match_calculation(assertion):
    matcher = get_matcher()

    assertion("Using the mixed syllable words 'Amazing display of crowing'")
    calculation = matcher.generate_match_calculation(["Amazing", "display", "of", "crowing"], 1)
    assertion("    should have weights adding up to 1", 1 - sum(calculation.weights) < 0.0001)
    assertion("    should give more weights to the first word", 0.375 - calculation.weights[0] < 0.001)
    assertion("    should give less weights to the third word", 0.125 - calculation.weights[2] < 0.001)
    assertion("    should return four possible branches", len(get_single_branches(calculation)) == 4)
    assertion("    should alter the sorting based on word length", get_single_branches(calculation) == [[0], [1], [3], [2]])
    assertion("    should return three possible double branches", len(get_double_branches(calculation)) == 3)    

def test_filtered_mixed_match_calculation(assertion):
    matcher = get_matcher()

    assertion("Using the mixed syllable words 'An incredible'")
    calculation = matcher.generate_match_calculation(["an", "incredible"], 1)
    assertion("    should have weights adding up to 1", 1 - sum(calculation.weights) < 0.0001)
    assertion("    should give less weights to the first word", 0.2 - calculation.weights[0] < 0.001)
    assertion("    should give more weights to the third word", 0.8 - calculation.weights[1] < 0.001)
    assertion("    should return one possible branches", len(get_single_branches(calculation)) == 1)
    assertion("    should alter the sorting based on word length", get_single_branches(calculation)[0] == [1])
    assertion("    should return one possible double branch", len(get_double_branches(calculation)) == 1)
    assertion("    should have the sorting based on word length", calculation.get_possible_branches() == [[0, 1], [1]])

suite = create_test_suite("Virtual buffer matcher initial branches calculation")
suite.add_test(test_generate_single_match_calculation)
suite.add_test(test_generate_double_match_calculation)
suite.add_test(test_generate_mixed_match_calculation)
suite.add_test(test_filtered_mixed_match_calculation)