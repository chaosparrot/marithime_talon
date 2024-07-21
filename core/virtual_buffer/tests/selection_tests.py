from ..buffer import VirtualBuffer
from ..indexer import text_to_virtual_buffer_tokens
from ...utils.test import create_test_suite
import csv
import os 
from ..typing import SELECTION_THRESHOLD, CORRECTION_THRESHOLD
from time import perf_counter
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
    vb.select_phrases([x.phrase for x in query_tokens], SELECTION_THRESHOLD, verbose=buffer.startswith("###"))
    if result != "":
        is_valid = vb.caret_tracker.get_selection_text().strip() == result.strip()
    else:
        is_valid = vb.caret_tracker.selecting_text == False 

    #if not is_valid:
    #    assertion("    Starting with the text '" + buffer + "' and searching for '" + query + "'...")
    #    assertion("        Should result in the selection '" + result.strip() + "'", is_valid)
    #    assertion("        Found '" + vb.caret_tracker.get_selection_text().strip() + "' instead")
    #else:
    #    assertion("    Searching for '" + query + "' finds '" + result.strip() + "'", is_valid)
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
    invalid = []
    with open(os.path.join(test_path, "testcase_selection.csv"), 'r', newline='') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";", quotechar='"')
        for row in reader:
            rows += 1

            invalid_query = row["query"] != ""
            pass_highlight = (highlight_only and row["buffer"].startswith("#!"))
            pass_skip_known_invalid = (not highlight_only and (not skip_known_invalid or not row["buffer"].startswith("#")))
            
            if invalid_query and (pass_highlight or pass_skip_known_invalid):
                result, actual = test_selection(assertion, row["buffer"], row["query"], row["result"])
                #print( str(rows) + ": queried '" + row["query"] + "', expected '" + row["result"] + "' -> '" + actual + "'")
                if result:
                    valid += 1
                    if row["buffer"].startswith("#"):
                        improvements.append(row)
                else:
                    row["actual"] = actual
                    invalid.append(row)
                    if not row["buffer"].startswith("#"):
                        regressions.append(row)

    return [rows, valid, improvements, regressions, invalid] 

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
    total_results = {}
    for invalid_result in selection_results[4]:
        key = str(len(invalid_result["query"].split())) + "-" + str(len(invalid_result["result"].split())) + "-" + str(len(invalid_result["actual"].split()))
        if key not in total_results:
            total_results[key] = 0
        total_results[key] += 1

        assertion(invalid_result["buffer"] + " searching '" + invalid_result["query"] + "' does not yield '" + invalid_result["result"] + "' but '" + invalid_result["actual"] + "'", False)

    # Last check before algo change
    # 118 / 196 = 60% = Expected result, got NOTHING
    # 43 / 196 = 21% = Expected NOTHING, got result!
    # 1 query = 13
    # 2 query = 54
    # 3 query = 91
    # 4 query = 26
    # 5 query = 3
    # 6 query = 1

    # After using new selection algorithm for single word selection
    # 1 query = 5, improved from 13
    
    # After including impossible branches
    # 130 / 152 = 85% = Expected result, got NOTHING
    # 12 / 152 = 8% = Expected NOTHING, got result!
    # 2 query = 49, improved from 54
    # 3 query = 73, improved from 91
    # 4 query = 22, improved from 26
    # 5 query = 2, improved from 3
    # This clearly hints at improper estimation of impossible branches

    # After removing first branch performance 'improvements'
    # 146 errors rather than 152 - Improved by 6

    # After fixing the selection threshold
    # 127 errors rather than 146 - Improved by 19
    # 6 / 127 = 5% = Expected result, got NOTHING
    # 87 / 127 = 68% = Expected NOTHING, got result!
    # 1 query = 13
    # 2 query = 36
    # 3 query = 56
    # 4 query = 18
    # 5 query = 3
    # 6 query = 1

    # After fixing the submatrix simplification
    # 105 errors rather than 127 - Improved by 22
    # 7 / 105 = 7% = Expected result, got NOTHING
    # 76 / 105 = 72% = Expected NOTHING, got result!
    # 1 query = 13
    # 2 query = 36
    # 3 query = 40
    # 4 query = 10
    # 5 query = 2
    # 6 query = 0
    # Missing 4 errors above, doesn't really matter for the result

    # After fixing the search space for branch roots within submatrices
    # 99 errors rather than 105 - Improved by 6
    # 2 / 99 = 2% = Expected result, got NOTHING
    # 80 / 99 = 81% = Expected NOTHING, got result!
    # 1 query = 13
    # 2 query = 34
    # 3 query = 38
    # 4 query = 11
    # 5 query = 2
    # 6 query = 0

    # After improving combined buffer skip logic ( disallowing expanding with more syllables, checking if skip outperforms double combination )
    # 90 errors rather than 99 - Improved by 9
    # 2 / 90 = 2% = Expected result, got NOTHING
    # 71 / 90 = 78% = Expected NOTHING, got result!
    # 1 query = 13
    # 2 query = 33
    # 3 query = 31
    # 4 query = 11
    # 5 query = 2
    # 6 query = 0

    # After tapering threshold for length of query ( single phrase queries need more stringent checks than 3 phrase words )
    # 65 errors rather than 90 - Improved by 25
    # 3 / 65 = 5% = Expected result, got NOTHING
    # 46 / 65 = 71% = Expected NOTHING, got result!
    # 1 query = 2
    # 2 query = 19
    # 3 query = 31
    # 4 query = 11
    # 5 query = 2
    # 6 query = 0

    # After adding no consecutive low score rule + no skip rule for queries shorter than 3 words
    # 55 errors, rather than 65 - Improved by 10
    # 2 / 55 = 4% = Expected result, got NOTHING
    # 42 / 55 = 76% = Expected NOTHING, got result
    # 1 query = 2
    # 2 query = 15
    # 3 query = 27
    # 4 query = 9
    # 5 query = 2

    # After vowel homophone tweaks and making thresholds slightly more forgiving
    # 52 errors, rather than 55 - Improved by 3
    # 0 / 52 = 0% = Expected result, got NOTHING
    # 29 / 52 = 55% = Expected NOTHING, got result
    # 1 query = 0
    # 2 query = 15
    # 3 query = 26
    # 4 query = 8
    # 5 query = 2

    # After tweaking the low score rule to be less forgiving for fewer words
    # 45 errors, rather than 52 - Improved by 7
    # 2 / 45 = 4% = Expected result, got NOTHING
    # 31 / 45 = 69% = Expected NOTHING, got result
    # 1 query = 0
    # 2 query = 8
    # 3 query = 19
    # 4 query = 8
    # 5 query = 2

    #for regression in selection_results[3]:
        #key = str(len(regression["query"].split())) + "-" + str(len(regression["result"].split()))
    #    if key not in total_results:
    #        total_results[key] = 0
    #    total_results[key] += 1
    #    assertion(regression["buffer"] + " searching '" + regression["query"] + "' does not yield '" + regression["result"] + "' but '" + regression["actual"] + "'")
    print( total_results )
    #selection_tests(assertion, False, True)

suite = create_test_suite("Selecting whole phrases inside of a selection") 
#suite.add_test(selection_tests)
#suite.add_test(correction_tests)
#suite.add_test(selfrepair_tests)
suite.add_test(percentage_tests)
suite.run()