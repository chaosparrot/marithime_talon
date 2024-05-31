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

def test_translate_sub_matrix_index_to_matrix_index(assertion):
    assertion("Translating a resulting index of a sub matrix back to a matrix index")
    matrix0_2 = VirtualBufferMatchMatrix(0, get_tokens_from_sentence("an incredibly dense"))
    assertion("    0 should be 0 when the matrix start at 0", matrix0_2.to_global_index(0) == 0)
    assertion("    1 should be 1 when the matrix start at 0", matrix0_2.to_global_index(1) == 1)
    assertion("    2 should be 2 when the matrix start at 0", matrix0_2.to_global_index(2) == 2)
    matrix1_2 = VirtualBufferMatchMatrix(1, get_tokens_from_sentence("an incredibly dense"))
    assertion("    0 should be 1 when the matrix start at 0", matrix1_2.to_global_index(0) == 1)
    assertion("    1 should be 2 when the matrix start at 0", matrix1_2.to_global_index(1) == 2)
    assertion("    2 should be 3 when the matrix start at 0", matrix1_2.to_global_index(2) == 3)
    matrix99_2 = VirtualBufferMatchMatrix(99, get_tokens_from_sentence("an incredibly dense"))
    assertion("    0 should be 99 when the matrix start at 99", matrix99_2.to_global_index(0) == 99)
    assertion("    1 should be 100 when the matrix start at 99", matrix99_2.to_global_index(1) == 100)
    assertion("    2 should be 101 when the matrix start at 99", matrix99_2.to_global_index(2) == 101)

suite = create_test_suite("Virtual buffer matcher matrix gathering")
suite.add_test(test_empty_potential_submatrices)
suite.add_test(test_single_potential_submatrices)
suite.add_test(test_can_merge_matrices)
suite.add_test(test_merge_matrices)
suite.add_test(test_merge_matrices_at_end)
suite.add_test(test_merge_matrices_overlapping_matrices_end)
suite.add_test(test_merge_matrices_overlapping_matrices_start)
suite.add_test(test_merge_matrices_overlapping_matrices_middle)
suite.add_test(test_translate_sub_matrix_index_to_matrix_index)