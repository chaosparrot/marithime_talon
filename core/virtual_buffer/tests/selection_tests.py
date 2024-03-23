from ..buffer import VirtualBuffer
from ..indexer import text_to_virtual_buffer_tokens
from ...utils.test import create_test_suite
import csv
import os 
from talon import resource
test_path = os.path.dirname(os.path.realpath(__file__))

resource.open(os.path.join(test_path, "testcase_selfrepair.csv"))
resource.open(os.path.join(test_path, "testcase_selection.csv"))

def test_selection(assertion, buffer: str, query: str, result: str = ""):
    vb = VirtualBuffer()
    text_tokens = buffer.split(" ")
    tokens = []
    for index, text_token in enumerate(text_tokens):
        tokens.extend(text_to_virtual_buffer_tokens(text_token + (" " if index < len(text_tokens) - 1 else "")))

    query_text_tokens = query.split(" ")
    query_tokens = []
    for index, query_token in enumerate(query_text_tokens):
        query_tokens.extend(text_to_virtual_buffer_tokens(query_token + (" " if index < len(query_text_tokens) - 1 else "")))

    vb.insert_tokens(tokens)
    vb.select_phrases([x.phrase for x in query_tokens], 1)
    if result != "":
        is_valid = vb.caret_tracker.get_selection_text().strip() == result.strip()
    else:
        is_valid = vb.caret_tracker.selecting_text == False

    if not is_valid:
        assertion("    Starting with the text '" + buffer + "' and searching for '" + query + "'...")
        assertion("        Should result in the selection '" + result.strip() + "'", is_valid)
        assertion("        Found '" + vb.caret_tracker.get_selection_text().strip() + "' instead")
    else:
        assertion("    Searching for '" + query + "' finds '" + result.strip() + "'", is_valid)

def test_selfrepair(assertion, buffer: str, query: str, result: str = ""):
    vb = VirtualBuffer()
    text_tokens = buffer.split(" ")
    tokens = []
    for index, text_token in enumerate(text_tokens):
        tokens.extend(text_to_virtual_buffer_tokens(text_token + (" " if index < len(text_tokens) - 1 else "")))

    query_text_tokens = query.split(" ")
    query_tokens = []
    for index, query_token in enumerate(query_text_tokens):
        query_tokens.extend(text_to_virtual_buffer_tokens(query_token + (" " if index < len(query_text_tokens) - 1 else "")))

    vb.insert_tokens(tokens)
    match = vb.find_self_repair([x.phrase for x in query_tokens])
    if result != "":
        is_valid = match is not None and " ".join(match.comparisons[1]).replace("  ", " ").strip() == result.strip()
    else:
        is_valid = match is None

    if not is_valid:
        assertion("    Selfrepairing '" + buffer + "' with '" + query.strip() + "' does not works as expected", is_valid)
        found_result = "" if match is None else " ".join(match.comparisons[1]).replace("  ", " ")
        assertion("        Selected '" + found_result + "' but expected '" + result.strip() + "'")

    #else:
    #    assertion("    Selfrepairing '" + buffer + "' with '" + query.strip() + "' works as expected", is_valid)

def selection_tests(assertion):
    with open(os.path.join(test_path, "testcase_selection.csv"), 'r', newline='') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";", quotechar='"')
        for row in reader:
            if not row["buffer"].startswith("#"):
                test_selection(assertion, row["buffer"], row["query"], row["result"])

def selfrepair_tests(assertion): 
    with open(os.path.join(test_path, "testcase_selfrepair.csv"), 'r', newline='') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";", quotechar='"')
        for row in reader:
            if not row["buffer"].startswith("#"):
                test_selfrepair(assertion, row["buffer"], row["inserted"], row["selfrepaired"])

suite = create_test_suite("Selecting whole phrases inside of a selection") 
suite.add_test(selection_tests)
suite.add_test(selfrepair_tests)