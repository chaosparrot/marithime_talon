from ..buffer import VirtualBuffer
from ..indexer import text_to_virtual_buffer_tokens
from ...utils.test import create_test_suite
import time

vb = VirtualBuffer()

def fill_vb():
    tokens = []
    for x in range(2000):
        tokens.extend(text_to_virtual_buffer_tokens("Insert ", "insert"))
        tokens.extend(text_to_virtual_buffer_tokens("a ", "a"))
        tokens.extend(text_to_virtual_buffer_tokens("new ", "new"))
        tokens.extend(text_to_virtual_buffer_tokens("sentence.", "sentence"))
    vb.insert_tokens(tokens)

def test_selection_performance_no_match(assertion):
    assertion( "    Starting from the end of a large document and searching for text that isn't in the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["testing"])
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < 0.05
    assertion( "        Should be done in less than 50 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str(end_time - start_time), made_performance_check)

def test_selection_performance_single_match(assertion):
    assertion( "    Starting from the end of a large document and searching for a word that is in the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["insert"])
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < 0.1
    assertion( "        Should be done in less than 100 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str(end_time - start_time), made_performance_check)

def test_selection_performance_multiple_match(assertion):
    assertion( "    Starting from the end of a large document and searching for two words that are in the document'...")
    start_time = time.perf_counter()
    vb.select_phrases(["insert", "an"])
    end_time = time.perf_counter()
    made_performance_check = end_time - start_time < 0.2
    assertion( "        Should be done in less than 200 milliseconds", made_performance_check)
    assertion( "        Actual milliseconds: " + str(end_time - start_time), made_performance_check)

suite = create_test_suite("Testing the selection performance on a large document")
#suite.add_test(test_selection_performance_no_match)
#suite.add_test(test_selection_performance_single_match)
#suite.add_test(test_selection_performance_multiple_match)
#suite.run()