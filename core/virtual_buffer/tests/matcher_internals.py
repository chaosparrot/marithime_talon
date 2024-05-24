from ..matcher import VirtualBufferMatcher
from ...phonetics.phonetics import PhoneticSearch
from ..indexer import text_to_virtual_buffer_tokens
from ..typing import VirtualBufferMatchMatrix, VirtualBufferMatchCalculation
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

def test_empty_potential_submatrices(assertion):
    matcher = get_matcher()

    assertion("Using the mixed syllable words 'An incredible' and searching a matrix without a match for incredible")
    calculation = matcher.generate_match_calculation(["an", "incredible"], 1)
    matrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("this is a large test with a bunch of connections"))
    submatrices = matcher.find_potential_submatrices(calculation, matrix)
    assertion("    should not give a single possible submatrix", len(submatrices) == 0)

def test_single_potential_submatrices(assertion):
    matcher = get_matcher()

    assertion("Using the mixed syllable words 'An incredible' and searching a matrix with a match for incredible")
    calculation = matcher.generate_match_calculation(["an", "incredible"], 1)
    matrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("this is a large test with the incredibly good match that can"))
    submatrices = matcher.find_potential_submatrices(calculation, matrix)
    assertion("    should give a single possible submatrix", len(submatrices) == 1)
    assertion("    should start 4 indecis from the start", submatrices[0].index == 4)
    assertion("    should start 2 indecis from the end", submatrices[0].index + len(submatrices[0].tokens) == 10)

    assertion("Using the mixed syllable words 'An incredible' and searching a matrix with a match for incredible clipped at the end")
    second_matrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("this is a large test with the incredibly good"))
    submatrices = matcher.find_potential_submatrices(calculation, second_matrix)
    assertion("    should give a single possible submatrix", len(submatrices) == 1)
    assertion("    should start 4 indecis from the start", submatrices[0].index == 4)
    assertion("    should start 0 indecis from the end", submatrices[0].index + len(submatrices[0].tokens) == 9)

    assertion("Using the mixed syllable words 'An incredible' and searching a matrix with a match for incredible clipped at the start")
    second_matrix = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("the incredibly good match that can"))
    submatrices = matcher.find_potential_submatrices(calculation, second_matrix)
    assertion("    should give a single possible submatrix", len(submatrices) == 1)
    assertion("    should start 0 indecis from the start", submatrices[0].index == 0)
    assertion("    should start 2 indecis from the end", submatrices[0].index + len(submatrices[0].tokens) == 4)

def test_can_merge_matrices(assertion):
    matcher = get_matcher()

    assertion("Using multiple matrices that overlap")
    matrix0_2 = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("an incredibly dense"))
    matrix1_3 = VirtualBufferMatchMatrix(1, get_tokens_from_sentence("an incredibly dense"))
    matrix2_4 = VirtualBufferMatchMatrix(2, get_tokens_from_sentence("an incredibly dense"))
    matrix3_5 = VirtualBufferMatchMatrix(3, get_tokens_from_sentence("an incredibly dense"))    
    matrix100_102 = VirtualBufferMatchMatrix(100, get_tokens_from_sentence("an incredibly dense"))

    assertion("    should allow merges between 0_2 and 1_3", matcher.can_merge_matrices(matrix0_2, matrix1_3))
    assertion("    should allow merges between 0_2 and 2_4", matcher.can_merge_matrices(matrix0_2, matrix2_4))
    assertion("    should not allow merges between 0_2 and 3_5", not matcher.can_merge_matrices(matrix0_2, matrix3_5))    
    assertion("    should not allow merges between 0_2 and 100_103", not matcher.can_merge_matrices(matrix0_2, matrix100_102))
    assertion("    should allow merges between 1_3 and 0_2", matcher.can_merge_matrices(matrix1_3, matrix0_2))
    assertion("    should allow merges between 1_3 and 3_5", matcher.can_merge_matrices(matrix1_3, matrix3_5))
    assertion("    should not allow merges between 1_3 and 100_103", not matcher.can_merge_matrices(matrix1_3, matrix100_102))
    assertion("    should not allow merges between 100_102 and 0_2", not matcher.can_merge_matrices(matrix100_102, matrix0_2))
    assertion("    should not allow merges between 100_102 and 1_3", not matcher.can_merge_matrices(matrix100_102, matrix1_3))
    assertion("    should not allow merges between 100_102 and 2_4", not matcher.can_merge_matrices(matrix100_102, matrix2_4))
    assertion("    should not allow merges between 100_102 and 3_5", not matcher.can_merge_matrices(matrix100_102, matrix3_5)) 

def test_merge_matrices(assertion):
    matcher = get_matcher()

    assertion("Using multiple matrices that overlap (an incredibly dense) with (incredibly dense cake)")
    matrix0_2 = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("an incredibly dense"))
    matrix1_3 = VirtualBufferMatchMatrix(1, get_tokens_from_sentence("incredibly dense cake"))
    merged_matrix = matcher.merge_matrices(matrix0_2, matrix1_3)
    assertion("    should have the matrix start at 0", merged_matrix.index == 0)
    assertion("    should have the matrix end at 2", merged_matrix.end_index == 3)
    assertion("    should start with 'an'", merged_matrix.tokens[0].phrase == "an")
    assertion("    should end with 'cake'", merged_matrix.tokens[-1].phrase == "cake")
    assertion("    should have four tokens", len(merged_matrix.tokens) == 4)

    assertion("Swapping these matrices around should result in the same outcome")
    merged_matrix = matcher.merge_matrices(matrix1_3, matrix0_2)
    assertion("    should have the matrix start at 0", merged_matrix.index == 0)
    assertion("    should have the matrix end at 2", merged_matrix.end_index == 3)
    assertion("    should start with 'an'", merged_matrix.tokens[0].phrase == "an")
    assertion("    should end with 'cake'", merged_matrix.tokens[-1].phrase == "cake")
    assertion("    should have four tokens", len(merged_matrix.tokens) == 4)

def test_merge_matrices_at_end(assertion):
    matcher = get_matcher()

    assertion("Using multiple matrices that touch at the end (an incredibly dense) with (cake that will)")
    matrix0_2 = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("an incredibly dense"))
    matrix3_5 = VirtualBufferMatchMatrix(3, get_tokens_from_sentence("cake that will"))
    merged_matrix = matcher.merge_matrices(matrix0_2, matrix3_5)
    assertion("    should have the matrix start at 0", merged_matrix.index == 0)
    assertion("    should have the matrix end at 2", merged_matrix.end_index == 5)
    assertion("    should start with 'an'", merged_matrix.tokens[0].phrase == "an")
    assertion("    should end with 'will'", merged_matrix.tokens[-1].phrase == "will")
    assertion("    should have six tokens", len(merged_matrix.tokens) == 6)

    assertion("Swapping these matrices around should result in the same outcome")
    merged_matrix = matcher.merge_matrices(matrix3_5, matrix0_2)
    assertion("    should have the matrix start at 0", merged_matrix.index == 0)
    assertion("    should have the matrix end at 2", merged_matrix.end_index == 5)
    assertion("    should start with 'an'", merged_matrix.tokens[0].phrase == "an")
    assertion("    should end with 'will'", merged_matrix.tokens[-1].phrase == "will")
    assertion("    should have six tokens", len(merged_matrix.tokens) == 6)

def test_merge_matrices_overlapping_matrices_end(assertion):
    matcher = get_matcher()

    assertion("Using multiple matrices that completely envelop one another (an incredibly dense) with (dense)")
    matrix0_2 = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("an incredibly dense"))
    matrix2_2 = VirtualBufferMatchMatrix(2, get_tokens_from_sentence("dense"))
    merged_matrix = matcher.merge_matrices(matrix0_2, matrix2_2)
    assertion("    should have the matrix start at 0", merged_matrix.index == 0)
    assertion("    should have the matrix end at 2", merged_matrix.end_index == 2)
    assertion("    should start with 'an'", merged_matrix.tokens[0].phrase == "an")
    assertion("    should end with 'dense'", merged_matrix.tokens[-1].phrase == "dense")
    assertion("    should have three tokens", len(merged_matrix.tokens) == 3)

    assertion("Swapping these matrices around should result in the same outcome")
    merged_matrix = matcher.merge_matrices(matrix2_2, matrix0_2)
    assertion("    should have the matrix start at 0", merged_matrix.index == 0)
    assertion("    should have the matrix end at 2", merged_matrix.end_index == 2)
    assertion("    should start with 'an'", merged_matrix.tokens[0].phrase == "an")
    assertion("    should end with 'dense'", merged_matrix.tokens[-1].phrase == "dense")
    assertion("    should have three tokens", len(merged_matrix.tokens) == 3)

def test_merge_matrices_overlapping_matrices_start(assertion):
    matcher = get_matcher()

    assertion("Using multiple matrices that completely envelop one another (an incredibly dense) with (an)")
    matrix0_2 = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("an incredibly dense"))
    matrix0_0 = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("an"))
    merged_matrix = matcher.merge_matrices(matrix0_2, matrix0_0)
    assertion("    should have the matrix start at 0", merged_matrix.index == 0)
    assertion("    should have the matrix end at 2", merged_matrix.end_index == 2)
    assertion("    should start with 'an'", merged_matrix.tokens[0].phrase == "an")
    assertion("    should end with 'dense'", merged_matrix.tokens[-1].phrase == "dense")
    assertion("    should have three tokens", len(merged_matrix.tokens) == 3)

    assertion("Swapping these matrices around should result in the same outcome")
    merged_matrix = matcher.merge_matrices(matrix0_0, matrix0_2)
    assertion("    should have the matrix start at 0", merged_matrix.index == 0)
    assertion("    should have the matrix end at 2", merged_matrix.end_index == 2)
    assertion("    should start with 'an'", merged_matrix.tokens[0].phrase == "an")
    assertion("    should end with 'dense'", merged_matrix.tokens[-1].phrase == "dense")
    assertion("    should have three tokens", len(merged_matrix.tokens) == 3)

def test_merge_matrices_overlapping_matrices_middle(assertion):
    matcher = get_matcher()

    assertion("Using multiple matrices that completely envelop one another (an incredibly dense) with (an)")
    matrix0_2 = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("an incredibly dense"))
    matrix1_1 = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("incredibly"))
    merged_matrix = matcher.merge_matrices(matrix0_2, matrix1_1)
    assertion("    should have the matrix start at 0", merged_matrix.index == 0)
    assertion("    should have the matrix end at 2", merged_matrix.end_index == 2)
    assertion("    should start with 'an'", merged_matrix.tokens[0].phrase == "an")
    assertion("    should end with 'dense'", merged_matrix.tokens[-1].phrase == "dense")
    assertion("    should have three tokens", len(merged_matrix.tokens) == 3)

    assertion("Swapping these matrices around should result in the same outcome")
    merged_matrix = matcher.merge_matrices(matrix1_1, matrix0_2)
    assertion("    should have the matrix start at 0", merged_matrix.index == 0)
    assertion("    should have the matrix end at 2", merged_matrix.end_index == 2)
    assertion("    should start with 'an'", merged_matrix.tokens[0].phrase == "an")
    assertion("    should end with 'dense'", merged_matrix.tokens[-1].phrase == "dense")
    assertion("    should have three tokens", len(merged_matrix.tokens) == 3)

suite = create_test_suite("Virtual buffer matcher internal calculations")
suite.add_test(test_generate_single_match_calculation)
suite.add_test(test_generate_double_match_calculation)
suite.add_test(test_generate_mixed_match_calculation)
suite.add_test(test_filtered_mixed_match_calculation)
suite.add_test(test_empty_potential_submatrices)
suite.add_test(test_single_potential_submatrices)
suite.add_test(test_can_merge_matrices)
suite.add_test(test_merge_matrices)
suite.add_test(test_merge_matrices_at_end)
suite.add_test(test_merge_matrices_overlapping_matrices_end)
suite.add_test(test_merge_matrices_overlapping_matrices_start)
suite.add_test(test_merge_matrices_overlapping_matrices_middle)
suite.run()