from ..buffer import VirtualBuffer
from ..indexer import text_to_virtual_buffer_tokens
from ...utils.test import create_test_suite
import time

token_1 = text_to_virtual_buffer_tokens("Insert ", "insert")
token_2 = text_to_virtual_buffer_tokens("a ", "a")
token_3 = text_to_virtual_buffer_tokens("new ", "new")
token_4 = text_to_virtual_buffer_tokens("sentence.", "sentence")

tokens = []
for x in range(2000):
    tokens.extend(token_1)
    tokens.extend(token_2)
    tokens.extend(token_3)
    tokens.extend(token_4)

def test_selection_performance_no_match(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(tokens, True)
    vb.reformat_tokens()

    assertion( "    Starting from the end of a large document and searching for text that isn't in the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["testing"])
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < 0.05
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str(end_time - start_time), made_performance_check)

def test_selection_performance_single_match(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(tokens, True)

    assertion( "    Starting from the end of a large document and searching for a word that is in the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["insert"])
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < 0.05
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str((end_time - start_time) * 1000), made_performance_check)

def test_selection_performance_multiple_match(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(tokens, True)

    assertion( "    Starting from the end of a large document and searching for two words that are exactly in the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["insert", "a"], verbose=False)
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < 0.05
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str((end_time - start_time) * 1000), made_performance_check)

def test_selection_performance_multiple_no_matches(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(tokens, True)

    assertion( "    Starting from the end of a large document and searching for text that isn't in the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["testing", "the", "biggest"])
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < 0.05
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str((end_time - start_time) * 1000), made_performance_check)

def test_selection_performance_single_fuzzy_match(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(tokens, True)

    assertion( "    Starting from the end of a large document and searching for one word that is fuzzy within the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["inserted"], verbose=False)
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < 0.05
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str((end_time - start_time) * 1000), made_performance_check)

def test_selection_performance_multiple_fuzzy_match(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(tokens, True)

    assertion( "    Starting from the end of a large document and searching for two words that are fuzzy within the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["inserted", "an"], verbose=False)
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < 0.05
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str((end_time - start_time) * 1000), made_performance_check)

def test_selection_performance_four_fuzzy_matches(assertion):
    vb = VirtualBuffer()
    vb.set_tokens(tokens, True)

    assertion( "    Starting from the end of a large document and searching for four words that are fuzzy within the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["inserted", "an", "new", "sentence"], verbose=False)
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < 0.05
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str((end_time - start_time) * 1000), made_performance_check)

#suite = create_test_suite("Testing the selection performance on a large document")
#suite.add_test(test_selection_performance_no_match)
#suite.add_test(test_selection_performance_single_match)
#suite.add_test(test_selection_performance_multiple_match)
#suite.add_test(test_selection_performance_multiple_no_matches)
#suite.add_test(test_selection_performance_single_fuzzy_match)
#suite.add_test(test_selection_performance_multiple_fuzzy_match)
#suite.add_test(test_selection_performance_four_fuzzy_matches)
#suite.run()

# TODO FIX PERFORMANCE FOR NO-MATCHES
# TODO FIX PERFORMANCE FOR SHORT FUZZY MATCHES