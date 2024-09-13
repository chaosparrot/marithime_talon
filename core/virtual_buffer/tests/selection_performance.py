from ..buffer import VirtualBuffer
from ..indexer import text_to_virtual_buffer_tokens
from ...utils.test import create_test_suite
from ..indexer import text_to_virtual_buffer_tokens
import time
import os

token_1 = text_to_virtual_buffer_tokens("Insert ", "insert")
token_2 = text_to_virtual_buffer_tokens("a ", "a")
token_3 = text_to_virtual_buffer_tokens("new ", "new")
token_4 = text_to_virtual_buffer_tokens("sentence.", "sentence")

milliseconds_50 = 0.00

lorum_tokens = []
def fill_lorum_tokens():
    global lorum_tokens
    test_path = os.path.dirname(os.path.realpath(__file__))
    if len(lorum_tokens) == 0:
        with open(os.path.join(test_path, "testcase_LorumIpsum8k.txt"), "r") as file:
            lorum_tokens = text_to_virtual_buffer_tokens(file.read())
    return lorum_tokens

def fill_tokens():
    global tokens
    if len(tokens) == 0:
        for x in range(2000):
            tokens.extend(token_1)
            tokens.extend(token_2)
            tokens.extend(token_3)
            tokens.extend(token_4)
    return tokens

tokens = []

def test_selection_performance_no_match(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(fill_tokens(), True)
    vb.reformat_tokens()

    assertion( "    Starting from the end of a large document and searching for text that isn't in the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["testing"])
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < milliseconds_50
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str((end_time - start_time) * 1000), made_performance_check)

def test_selection_performance_no_match_lorum(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(fill_lorum_tokens(), True)
    vb.reformat_tokens()

    assertion( "    Starting from the end of a large document without a lot of duplicates and searching for text that isn't in the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["thisisabigkindoftext"])
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < milliseconds_50
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str((end_time - start_time) * 1000), made_performance_check)

def test_selection_performance_single_match(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(fill_tokens(), True)

    assertion( "    Starting from the end of a large document and searching for a word that is in the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["insert"])
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < milliseconds_50
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str((end_time - start_time) * 1000), made_performance_check)

def test_selection_performance_multiple_match(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(fill_tokens(), True)

    assertion( "    Starting from the end of a large document and searching for two words that are exactly in the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["insert", "a"], verbose=False)
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < milliseconds_50
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str((end_time - start_time) * 1000), made_performance_check)
    
def test_selection_performance_multiple_no_matches(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(fill_tokens(), True)

    assertion( "    Starting from the end of a large document and searching for text that isn't in the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["testing", "the", "biggest"], verbose=False)
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < milliseconds_50
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str((end_time - start_time) * 1000), made_performance_check)

def test_selection_performance_single_fuzzy_match(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(fill_tokens(), True)

    assertion( "    Starting from the end of a large document and searching for one word that is fuzzy within the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["inserted"], verbose=False)
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < milliseconds_50
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str((end_time - start_time) * 1000), made_performance_check)

def test_selection_performance_multiple_fuzzy_match(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(fill_tokens(), True)

    assertion( "    Starting from the end of a large document and searching for two words that are fuzzy within the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["inserted", "an"], verbose=False)
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < milliseconds_50
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str((end_time - start_time) * 1000), made_performance_check)

def test_selection_performance_four_fuzzy_matches(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(fill_tokens(), True)

    assertion( "    Starting from the end of a large document and searching for four words that are fuzzy within the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["inserted", "an", "new", "sentence"], verbose=False)
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < 0.05
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str((end_time - start_time) * 1000), made_performance_check)

def test_selection_performance_four_fuzzy_matches_lorum(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(fill_lorum_tokens(), True)

    assertion( "    Starting from the end of a large document without a lot of duplicates and searching for four words that are fuzzy within the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["inserted", "an", "new", "sentence"], verbose=False)
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < 0.05
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str((end_time - start_time) * 1000), made_performance_check)

suite = create_test_suite("Testing the selection performance on a large document")

# Performance measurements
# Without cache | + Submatrix skip cache | + Branch skipping cache
#suite.add_test(test_selection_performance_no_match) # 46 ms | 88 ms | 45 ms
#suite.add_test(test_selection_performance_single_match) # 6 ms | 10 ms | 6 ms
#suite.add_test(test_selection_performance_multiple_match) # 7 ms | 10 ms | 8 ms
#suite.add_test(test_selection_performance_multiple_no_matches) # 2196 ms | 19 ms | 21 ms
#suite.add_test(test_selection_performance_single_fuzzy_match) # 43 ms | 49 ms | 49 ms
#suite.add_test(test_selection_performance_multiple_fuzzy_match) # 287 ms | 354 ms | 335 ms
#suite.add_test(test_selection_performance_four_fuzzy_matches) # 88 ms | 108 ms | 155 ms
#suite.add_test(test_selection_performance_no_match_lorum)
#suite.add_test(test_selection_performance_four_fuzzy_matches_lorum)
#suite.run()

# TODO FIX PERFORMANCE FOR FUZZY MATCHES

# Duplicate visits without branch skipping
# Select  : 36.274
# Correct : 56.076
# Self-r  : 68.444

# Duplicate visits with branch skipping
# Select  : 33.353
# Correct : 44.004
# Self-r  : 59.858

# For a single select check with 13 words and 4 query words
# 482 checks - 253 at the start, 68 of which are duplicates ( but might be due to a word appearing multiple times ) - 228 duplicates in total
# 41 results out of 253 starts
# ((4+3+2) * 13) + ( (13 + 12 + 11 ) * 4) = 261 for a full scan of 13 x 4 options
# That includes all single, double and triple combinations together