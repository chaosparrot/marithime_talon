from ..matcher import VirtualBufferMatcher
from ...phonetics.phonetics import PhoneticSearch
#from ..indexer import text_to_virtual_buffer_tokens
from ..typing import VirtualBufferMatchCalculation
from ...utils.test import create_test_suite

def get_matcher() -> VirtualBufferMatcher:
    homophone_contents = "where,wear,ware"
    phonetic_contents = "where,we're,were"
    phonetic_search = PhoneticSearch()
    phonetic_search.set_homophones(homophone_contents)
    phonetic_search.set_phonetic_similiarities(phonetic_contents)
    return VirtualBufferMatcher(phonetic_search)

def test_generate_single_match_calculation(assertion):
    matcher = get_matcher()

    assertion("Using the single syllable words 'This is good'")
    calculation = matcher.generate_match_calculation(["This", "is", "good"], 1)
    assertion("    should have weights adding up to 1", 1 - sum(calculation.weights) < 0.0001)
    assertion("    should have balanced weights", 0.333 - calculation.weights[0] < 0.001)    
    assertion("    should return three possible branches", len(calculation.get_possible_branches()) == 3)
    assertion("    should not alter the sorting", calculation.get_possible_branches() == [0, 1, 2])

def test_generate_double_match_calculation(assertion):
    matcher = get_matcher()

    assertion("Using the mixed syllable words 'Checkens running afoul'")
    calculation = matcher.generate_match_calculation(["Chickens", "running", "afoul"], 1)
    assertion("    should have weights adding up to 1", 1 - sum(calculation.weights) < 0.0001)
    assertion("    should have balanced weights",  0.333 - calculation.weights[0] < 0.001)
    assertion("    should return three possible branches", len(calculation.get_possible_branches()) == 3)
    assertion("    should not alter the sorting", calculation.get_possible_branches() == [0, 1, 2])

def test_generate_mixed_match_calculation(assertion):
    matcher = get_matcher()

    assertion("Using the mixed syllable words 'Amazing display of crowing'")
    calculation = matcher.generate_match_calculation(["Amazing", "display", "of", "crowing"], 1)
    assertion("    should have weights adding up to 1", 1 - sum(calculation.weights) < 0.0001)
    assertion("    should give more weights to the first word", 0.375 - calculation.weights[0] < 0.001)
    assertion("    should give less weights to the third word", 0.125 - calculation.weights[2] < 0.001)
    assertion("    should return four possible branches", len(calculation.get_possible_branches()) == 4)
    assertion("    should alter the sorting based on word length", calculation.get_possible_branches() == [0, 1, 3, 2])

def test_filtered_mixed_match_calculation(assertion):
    matcher = get_matcher()

    assertion("Using the mixed syllable words 'An incredible'")
    calculation = matcher.generate_match_calculation(["an", "incredible"], 1)
    assertion("    should have weights adding up to 1", 1 - sum(calculation.weights) < 0.0001)
    assertion("    should give less weights to the first word", 0.2 - calculation.weights[0] < 0.001)
    assertion("    should give more weights to the third word", 0.8 - calculation.weights[1] < 0.001)
    assertion("    should return one possible branches", len(calculation.get_possible_branches()) == 1)
    assertion("    should alter the sorting based on word length", calculation.get_possible_branches()[0] == 1)

suite = create_test_suite("Virtual buffer matcher internal calculations")
suite.add_test(test_generate_single_match_calculation)
suite.add_test(test_generate_double_match_calculation)
suite.add_test(test_generate_mixed_match_calculation)
suite.add_test(test_filtered_mixed_match_calculation)