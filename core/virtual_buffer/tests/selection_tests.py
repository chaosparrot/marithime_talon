from ..buffer import VirtualBuffer
from ..indexer import text_to_virtual_buffer_tokens
from ...utils.test import create_test_suite
import csv
import os 
from talon import resource
test_path = os.path.dirname(os.path.realpath(__file__))

resource.open(os.path.join(test_path, "testcase_selfrepair.csv"))
resource.open(os.path.join(test_path, "testcase_correction.csv"))
resource.open(os.path.join(test_path, "testcase_selection.csv"))

def test_selection(assertion, buffer: str, query: str, result: str = "") -> (bool, str):
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
    vb.select_phrases([x.phrase for x in query_tokens], 1, verbose=("#!" in buffer))
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
    return is_valid, vb.caret_tracker.get_selection_text().strip()

def test_correction(assertion, buffer: str, query: str, result: str = "") -> (bool, str):
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
    vb.select_phrases([x.phrase for x in query_tokens], 1, for_correction=True)
    if result != "":
        is_valid = vb.caret_tracker.get_selection_text().strip() == result.strip()
    else:
        is_valid = vb.caret_tracker.selecting_text == False 

    if not is_valid:
        assertion("    Starting with the text '" + buffer + "' and correcting with '" + query + "'...")
        assertion("        Should result in the selection '" + result.strip() + "'", is_valid)
        assertion("        Found '" + vb.caret_tracker.get_selection_text().strip() + "' instead")
    else:
        assertion("    Correcting with '" + query + "' finds '" + result.strip() + "'", is_valid)
    return is_valid, vb.caret_tracker.get_selection_text().strip()

def test_selfrepair(assertion, buffer: str, query: str, result: str = "") -> (bool, str):
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
    else:
        assertion("    Selfrepairing '" + buffer + "' with '" + query.strip() + "' works as expected", is_valid)
    return is_valid, "" if match is None else " ".join(match.comparisons[1]).replace("  ", " ").strip()

def selection_tests(assertion, skip_known_invalid = True, highlight_only = False) -> [int, int, [], []]:
    rows = 0
    valid = 0
    regressions = []
    improvements = []
    with open(os.path.join(test_path, "testcase_selection.csv"), 'r', newline='') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";", quotechar='"')
        for row in reader:
            rows += 1

            invalid_query = row["query"] != ""
            pass_highlight = (highlight_only and row["buffer"].startswith("#!"))
            pass_skip_known_invalid = (not highlight_only and (not skip_known_invalid or not row["buffer"].startswith("#")))
            
            if invalid_query and (pass_highlight or pass_skip_known_invalid):
                result, actual = test_selection(assertion, row["buffer"], row["query"], row["result"])
                if result:
                    valid += 1
                    if row["buffer"].startswith("#"):
                        improvements.append(row)
                else:
                    if not row["buffer"].startswith("#"):
                        row["actual"] = actual
                        regressions.append(row)

    return [rows, valid, improvements, regressions]

def correction_tests(assertion, skip_known_invalid = True) -> [int, int, [], []]:
    rows = 0
    valid = 0
    regressions = []
    improvements = []
    with open(os.path.join(test_path, "testcase_correction.csv"), 'r', newline='') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";", quotechar='"')
        for row in reader:
            rows += 1
            if row["correction"] != "" and (not skip_known_invalid or not row["buffer"].startswith("#")):
                result, actual = test_correction(assertion, row["buffer"], row["correction"], row["result"])
                if result:
                    valid += 1
                    if row["buffer"].startswith("#"):
                        improvements.append(row)
                else:
                    if not row["buffer"].startswith("#"):
                        row["actual"] = actual
                        regressions.append(row)

    return [rows, valid, improvements, regressions]

def selfrepair_tests(assertion, skip_known_invalid = True) -> [int, int, [], []]:
    rows = 0
    valid = 0
    regressions = []
    improvements = []
    with open(os.path.join(test_path, "testcase_selfrepair.csv"), 'r', newline='') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";", quotechar='"')
        for row in reader:
            rows += 1
            if row["inserted"] != "" and (not skip_known_invalid or not row["buffer"].startswith("#")):
                result, actual = test_selfrepair(assertion, row["buffer"], row["inserted"], row["selfrepaired"])
                if result:
                    valid += 1
                    if row["buffer"].startswith("#"):
                        improvements.append(row)
                else:
                    if not row["buffer"].startswith("#"):
                        row["actual"] = actual
                        regressions.append(row)

    return [rows, valid, improvements, regressions]
    
def noop_assertion(_, _2 = False):
    pass

def noop_assertion_with_highlights(assertion):
    return lambda buffer, is_valid = False, assertion=assertion: assertion(buffer, is_valid) if is_valid == False and "#!" in buffer else noop_assertion(buffer, is_valid)

def percentage_tests(assertion):
    selection_results = selection_tests(noop_assertion_with_highlights(assertion), False)
    #correction_results = correction_tests(noop_assertion_with_highlights(assertion), False)
    #selfrepair_results = selfrepair_tests(noop_assertion_with_highlights(assertion), False)
    
    total = selection_results[0]# + correction_results[0] + selfrepair_results[0]
    valid = selection_results[1]# + correction_results[1] + selfrepair_results[1]
    improvement_count = len(selection_results[2])# + len(correction_results[2]) + len(selfrepair_results[2])    
    regression_count = len(selection_results[3])# + len(correction_results[3]) + len(selfrepair_results[3])
    
    percentage = round((valid / total) * 1000) / 10
    reg = "Regressions: " + str(regression_count) + ", improvements: " + str(improvement_count) + ", invalid: " + str(total - valid)
    print( "Percentage of valid queries: " + str(percentage) + "%, " + reg )
    assertion("Percentage of valid queries: " + str(percentage) + "%, " + reg, valid / total >= 1)
    #for improvement in selection_results[2]:
    #    assertion(improvement["buffer"] + " searching '" + improvement["query"] + "' correctly yields '" + improvement["result"] + "'")
    for regression in selection_results[3]: 
        assertion(regression["buffer"] + " searching '" + regression["query"] + "' does not yield '" + regression["result"] + "' but '" + regression["actual"] + "'")

    #selection_tests(assertion, False, True)

# Tell me, Muse, of that man, so ready at need;for that weird;

suite = create_test_suite("Selecting whole phrases inside of a selection") 
#suite.add_test(selection_tests)
#suite.add_test(correction_tests)
#suite.add_test(selfrepair_tests)
#suite.add_test(percentage_tests)
#suite.run()