from ..buffer import VirtualBuffer
from ..indexer import text_to_virtual_buffer_tokens
from ..typing import VirtualBufferToken
from ...utils.test import create_test_suite

def get_empty_vb() -> VirtualBuffer:
    return VirtualBuffer()

def get_filled_vb() -> VirtualBuffer:
    vb = get_empty_vb()
    vb.insert_tokens(text_to_virtual_buffer_tokens("This ", "This"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("is ", "is"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("a ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("test", "test"))
    vb.insert_tokens(text_to_virtual_buffer_tokens(".or", "or"))
    return vb

def test_detect_merge_in_between_tokens(assertion):
    assertion( "Detecting merge strategies for inserting tokens in between tokens" )
    previous_no_merge = get_filled_vb().detect_merge_strategy(0, 0, VirtualBufferToken("Ask ", "ask", ""))
    assertion( "    Should always append before the first token if the token cannot be merged", previous_no_merge == (0, -1, -1))
    previous_no_merge_middle = get_filled_vb().detect_merge_strategy(1, 0, VirtualBufferToken("ask ", "ask", ""))
    assertion( "    Should always append before the second token if the token cannot be merged", previous_no_merge_middle == (0, -1, -1))
    current_append_after = get_filled_vb().detect_merge_strategy(0, 5, VirtualBufferToken("ask ", "ask", ""))
    assertion( "    Should always append after the first token if the token cannot be merged", current_append_after == (-1, 0, -1))
    current_middle_append_after = get_filled_vb().detect_merge_strategy(1, 3, VirtualBufferToken("ask ", "ask", ""))
    assertion( "    Should merge append after the second token if the token cannot be merged", current_middle_append_after == (-1, 0, -1))

    current_first_merge = get_filled_vb().detect_merge_strategy(0, 0, VirtualBufferToken("Ask", "ask", ""))
    assertion( "    Should merge with the first token if the token can be merged at the start", current_first_merge == (-1, 1, -1))
    second_first_merge = get_filled_vb().detect_merge_strategy(1, 0, VirtualBufferToken("Ask", "ask", ""))
    assertion( "    Should merge with the second token if the token can be merged at the start", second_first_merge == (-1, 1, -1))
    fourth_first_merge = get_filled_vb().detect_merge_strategy(3, 0, VirtualBufferToken("Ask", "ask", ""))
    assertion( "    Should merge with the current token if the token can be merged at the start", fourth_first_merge == (-1, 1, -1))
    third_last_merge = get_filled_vb().detect_merge_strategy(2, 2, VirtualBufferToken("Ask", "ask", ""))
    assertion( "    Should merge with the final token if the token can be merged at the end of the current token", third_last_merge == (-1, -1, 1))
    fourth_last_merge = get_filled_vb().detect_merge_strategy(3, 5, VirtualBufferToken("Ask", "ask", ""))
    assertion( "    Should merge with the current token if the token can be merged at the end", fourth_last_merge == (-1, 1, -1))
    final_last_merge = get_filled_vb().detect_merge_strategy(4, 3, VirtualBufferToken("Ask", "ask", ""))
    assertion( "    Should merge with the final token if the token can be merged at the end", final_last_merge == (-1, 1, -1)) 

def test_detect_merge_in_middle_of_tokens(assertion):
    assertion( "Detecting merge strategies for inserting tokens in the middle of tokens" )
    first_merge_middle = get_filled_vb().detect_merge_strategy(0, 1, VirtualBufferToken("ask", "ask", ""))
    assertion( "    Should merge with the first token if the token can be merged from both sides", first_merge_middle == (-1, 1, -1))
    current_merge_middle = get_filled_vb().detect_merge_strategy(1, 1, VirtualBufferToken("ask", "ask", ""))
    assertion( "    Should merge with the current token if the token can be merged from both sides", current_merge_middle == (-1, 1, -1))
    final_merge_middle = get_filled_vb().detect_merge_strategy(4, 2, VirtualBufferToken("ask", "ask", ""))
    assertion( "    Should merge with the final token if the token can be merged from both sides", final_merge_middle == (-1, 1, -1))
    first_split_left = get_filled_vb().detect_merge_strategy(0, 1, VirtualBufferToken(" ask", "ask", ""))
    assertion( "    Should split left of the first token if the token can only be merged from the right", first_split_left == (-1, 2, -1))
    current_split_left = get_filled_vb().detect_merge_strategy(1, 1, VirtualBufferToken(" ask", "ask", ""))
    assertion( "    Should split left of the current token if the token can only be merged from the right", current_split_left == (-1, 2, -1))
    final_split_left = get_filled_vb().detect_merge_strategy(4, 1, VirtualBufferToken(" ask", "ask", ""))
    assertion( "    Should split left of the final token if the token can only be merged from the right", final_split_left == (-1, 2, -1))
    first_split_right = get_filled_vb().detect_merge_strategy(0, 1, VirtualBufferToken("ask ", "ask", ""))
    assertion( "    Should split right of the first token if the token can only be merged from the left", first_split_right == (-1, 3, -1))
    current_split_right = get_filled_vb().detect_merge_strategy(1, 1, VirtualBufferToken("ask ", "ask", ""))
    assertion( "    Should split right of the current token if the token can only be merged from the left", current_split_right == (-1, 3, -1))
    final_split_right = get_filled_vb().detect_merge_strategy(4, 2, VirtualBufferToken("ask ", "ask", ""))
    assertion( "    Should split right of the final token if the token can only be merged from the left", final_split_right == (-1, 3, -1))
    first_split_both = get_filled_vb().detect_merge_strategy(0, 1, VirtualBufferToken(" ask ", "ask", ""))
    assertion( "    Should split on both sides of the first token if the token cannot be merged", first_split_both == (-1, 4, -1))
    current_split_both = get_filled_vb().detect_merge_strategy(1, 1, VirtualBufferToken(" ask ", "ask", ""))
    assertion( "    Should split on both sides of the current token if the token cannot be merged", current_split_both == (-1, 4, -1))
    final_split_both = get_filled_vb().detect_merge_strategy(4, 1, VirtualBufferToken(" ask ", "ask", ""))
    assertion( "    Should split on both sides of the final token if the token cannot be merged", final_split_both == (-1, 4, -1))

suite = create_test_suite("Merge and split detection")
suite.add_test(test_detect_merge_in_between_tokens)
suite.add_test(test_detect_merge_in_middle_of_tokens)