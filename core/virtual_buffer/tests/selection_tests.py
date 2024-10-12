from ..buffer import VirtualBuffer
from ..indexer import text_to_virtual_buffer_tokens
from ...utils.test import create_test_suite
from ...phonetics.phonetics import PhoneticSearch
import csv
import os 
from ..typing import SELECTION_THRESHOLD, CORRECTION_THRESHOLD
from time import perf_counter
from talon import resource
test_path = os.path.dirname(os.path.realpath(__file__))

resource.open(os.path.join(test_path, "testcase_selfrepair.csv"))
resource.open(os.path.join(test_path, "testcase_correction.csv"))
resource.open(os.path.join(test_path, "testcase_selection.csv"))

def get_uncached_virtual_buffer():
    vb = VirtualBuffer()

    # Reset the phonetic search to make sure there is no influence from user settings    
    vb.matcher.phonetic_search = PhoneticSearch()
    vb.matcher.phonetic_search.set_homophones("")
    vb.matcher.phonetic_search.set_phonetic_similiarities("")

    return vb

def test_selection(assertion, buffer: str, query: str, result: str = "") -> (bool, str, float):
    vb = get_uncached_virtual_buffer()

    text_tokens = buffer.split(" ")
    tokens = []
    for index, text_token in enumerate(text_tokens):
        if not text_token.startswith("#"):
            tokens.extend(text_to_virtual_buffer_tokens(text_token + (" " if index < len(text_tokens) - 1 else "")))

    query_text_tokens = query.split(" ")
    query_tokens = []
    for index, query_token in enumerate(query_text_tokens):
        query_tokens.extend(text_to_virtual_buffer_tokens(query_token + (" " if index < len(query_text_tokens) - 1 else "")))

    vb.set_tokens(tokens, True)
    vb.select_phrases([x.phrase for x in query_tokens], SELECTION_THRESHOLD, verbose=buffer.startswith("###"))
    duplicates = sum([value - 1 for value in vb.matcher.checked_comparisons.values() if value > 1])
    total = sum(vb.matcher.checked_comparisons.values())

    if buffer.startswith("###"):
        print("TOTAL CHECKS", total, "DUPLICATE CHECKS", duplicates)
        print("CHECKS", vb.matcher.checked_comparisons)

    if result != "":
        is_valid = vb.caret_tracker.get_selection_text().strip() == result.strip()
    else:
        is_valid = vb.caret_tracker.selecting_text == False

    #if not is_valid:
    #    assertion("    Starting with the text '" + buffer + "' and searching for '" + query + "'...")
    #    assertion("        Should result in the selection '" + result.strip() + "'", is_valid)
    #    assertion("        Found '" + vb.caret_tracker.get_selection_text().strip() + "' instead", is_valid)
    #else:
    #    assertion("    Searching for '" + query + "' finds '" + result.strip() + "'", is_valid)
    return is_valid, vb.caret_tracker.get_selection_text().strip(), round(duplicates / total * 100)

def test_correction(assertion, buffer: str, query: str, result: str = "") -> (bool, str, float):
    vb = get_uncached_virtual_buffer()

    text_tokens = buffer.split(" ")
    tokens = []
    for index, text_token in enumerate(text_tokens):
        if not text_token.startswith("#"):
            tokens.extend(text_to_virtual_buffer_tokens(text_token + (" " if index < len(text_tokens) - 1 else "")))

    query_text_tokens = query.split(" ")
    query_tokens = []
    for index, query_token in enumerate(query_text_tokens):
        query_tokens.extend(text_to_virtual_buffer_tokens(query_token + (" " if index < len(query_text_tokens) - 1 else "")))

    vb.set_tokens(tokens, True)
    vb.select_phrases([x.phrase for x in query_tokens], CORRECTION_THRESHOLD, for_correction=True, verbose=buffer.startswith("###"))
    duplicates = sum([value - 1 for value in vb.matcher.checked_comparisons.values() if value > 1])
    total = sum(vb.matcher.checked_comparisons.values())

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
    return is_valid, vb.caret_tracker.get_selection_text().strip(), round(duplicates / total * 100)

def test_selfrepair(assertion, buffer: str, query: str, result: str = "") -> (bool, str, float):
    vb = get_uncached_virtual_buffer()

    text_tokens = buffer.split(" ")
    tokens = []
    for index, text_token in enumerate(text_tokens):
        if not text_token.startswith("#"):
            tokens.extend(text_to_virtual_buffer_tokens(text_token + (" " if index < len(text_tokens) - 1 else "")))

    query_text_tokens = query.split(" ")
    query_tokens = []
    for index, query_token in enumerate(query_text_tokens):
        query_tokens.extend(text_to_virtual_buffer_tokens(query_token + (" " if index < len(query_text_tokens) - 1 else "")))

    vb.set_tokens(tokens, True)
    match = vb.find_self_repair([x.phrase if x.phrase != "" else x.text for x in query_tokens], verbose = buffer.startswith("###"))
    duplicates = sum([value - 1 for value in vb.matcher.checked_comparisons.values() if value > 1])
    total = sum(vb.matcher.checked_comparisons.values())
    buffer_tokens = [] if match is None else vb.tokens[match.buffer_indices[0][0]:(match.buffer_indices[-1][-1] + 1)]
    if result != "":
        is_valid = match is not None and " ".join([token.text for token in buffer_tokens]).replace("  ", " ").strip() == result.strip()
    else:
        is_valid = match is None

    if not is_valid:
        assertion("    Selfrepairing '" + buffer + "' with '" + query.strip() + "' does not works as expected", is_valid)
        found_result = "" if match is None else " ".join([token.text for token in buffer_tokens]).replace("  ", " ")
        assertion("        Selected '" + found_result + "' but expected '" + result.strip() + "'")
    else:
        assertion("    Selfrepairing '" + buffer + "' with '" + query.strip() + "' works as expected", is_valid)
    return is_valid, "" if match is None else " ".join([token.text for token in buffer_tokens]).replace("  ", " ").strip(), 0 if total == 0 else round(duplicates / total * 100)

def selection_tests(assertion, skip_known_invalid = True, highlight_only = False) -> [int, int, [], [], []]:
    rows = 0
    valid = 0
    regressions = []
    improvements = []
    invalid = []
    total_duplicate_percents = []
    with open(os.path.join(test_path, "testcase_selection.csv"), 'r', newline='') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";", quotechar='"')
        for row in reader:
            rows += 1

            invalid_query = row["query"] != ""
            pass_highlight = (highlight_only and row["buffer"].startswith("#!"))
            pass_skip_known_invalid = (not highlight_only and (not skip_known_invalid or not row["buffer"].startswith("#")))
            
            if invalid_query and (pass_highlight or pass_skip_known_invalid):
                result, actual, duplicate_percent = test_selection(assertion, row["buffer"], row["query"], row["result"])
                total_duplicate_percents.append(duplicate_percent)                
                if result:
                    valid += 1
                    if row["buffer"].startswith("#"):
                        improvements.append(row)
                else:
                    row["actual"] = actual
                    invalid.append(row)
                    if not row["buffer"].startswith("#"):
                        regressions.append(row)

    print( "TOTAL SELECTION PERCENTAGE DUPLICATES", sum(total_duplicate_percents) / len(total_duplicate_percents))
    return [rows, valid, improvements, regressions, invalid] 

def correction_tests(assertion, skip_known_invalid = True) -> [int, int, [], [], []]:
    rows = 0
    valid = 0
    regressions = []
    improvements = []
    invalid = []
    total_duplicate_percents = []
    with open(os.path.join(test_path, "testcase_correction.csv"), 'r', newline='') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";", quotechar='"')
        for row in reader:
            rows += 1
            if row["correction"] != "" and (not skip_known_invalid or not row["buffer"].startswith("#")):
                result, actual, duplicate_percent = test_correction(assertion, row["buffer"], row["correction"], row["result"])
                total_duplicate_percents.append(duplicate_percent)
                if result:
                    valid += 1
                    if row["buffer"].startswith("#"):
                        improvements.append(row)
                else:
                    row["actual"] = actual
                    invalid.append(row)
                    if not row["buffer"].startswith("#"):
                        regressions.append(row)

    print( "TOTAL CORRECTION PERCENTAGE DUPLICATES", sum(total_duplicate_percents) / len(total_duplicate_percents))
    return [rows, valid, improvements, regressions, invalid]

def selfrepair_tests(assertion, skip_known_invalid = True) -> [int, int, [], [], []]:
    rows = 0
    valid = 0
    regressions = []
    improvements = []
    invalid = []
    total_duplicate_percents = []
    with open(os.path.join(test_path, "testcase_selfrepair.csv"), 'r', newline='') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";", quotechar='"')
        for row in reader:
            rows += 1
            if row["inserted"] != "" and (not skip_known_invalid or not row["buffer"].startswith("#")):
                result, actual, duplicate_percent = test_selfrepair(assertion, row["buffer"], row["inserted"], row["selfrepaired"])
                total_duplicate_percents.append(duplicate_percent)                
                if result:
                    valid += 1
                    if row["buffer"].startswith("#"):
                        improvements.append(row)
                else:
                    row["actual"] = actual
                    invalid.append(row)
                    if not row["buffer"].startswith("#"):
                        regressions.append(row)

    print( "TOTAL SELF-REPAIR PERCENTAGE DUPLICATES", sum(total_duplicate_percents) / len(total_duplicate_percents))
    return [rows, valid, improvements, regressions, invalid]
    
def noop_assertion(_, _2 = False):
    pass

def noop_assertion_with_highlights(assertion):
    return lambda buffer, is_valid = False, assertion=assertion: assertion(buffer, is_valid) if is_valid == False and "#!" in buffer else noop_assertion(buffer, is_valid)

def percentage_tests(assertion, selection = True, correction = True, selfrepair = True, desired_threshold = 1):
    selection_results = selection_tests(noop_assertion_with_highlights(assertion), False) if selection else [0, 0, [], [], []]
    correction_results = correction_tests(noop_assertion_with_highlights(assertion), False) if correction else [0, 0, [], [], []]
    selfrepair_results = selfrepair_tests(noop_assertion_with_highlights(assertion), False) if selfrepair else [0, 0, [], [], []]
    
    total = selfrepair_results[0] + correction_results[0] + selection_results[0]
    valid = selfrepair_results[1] + correction_results[1] + selection_results[1]
    improvement_count = len(selfrepair_results[2]) + len(selection_results[2]) + len(correction_results[2])
    regression_count = len(selfrepair_results[3]) + len(selection_results[3]) + len(correction_results[3])
    
    percentage = round((valid / total) * 1000) / 10
    reg = "Regressions: " + str(regression_count) + ", improvements: " + str(improvement_count) + ", invalid: " + str(total - valid)
    assertion("Percentage of valid queries: " + str(percentage) + "%, " + reg, valid / total >= desired_threshold)
    #for improvement in selection_results[2]:
    #    assertion(improvement["buffer"] + " searching '" + improvement["query"] + "' correctly yields '" + improvement["result"] + "'")
    total_results = {}
    for invalid_result in selection_results[4]:
        key = str(len(invalid_result["query"].split())) + "-" + str(len(invalid_result["result"].split())) + "-" + str(len(invalid_result["actual"].split()))
        if key not in total_results:
            total_results[key] = 0
        total_results[key] += 1
        #assertion(invalid_result["buffer"] + " selecting '" + invalid_result["query"] + "' does not yield '" + invalid_result["result"] + "' but '" + invalid_result["actual"] + "'", False)

    for invalid_result in correction_results[4]:
        key = str(len(invalid_result["correction"].split())) + "-" + str(len(invalid_result["result"].split())) + "-" + str(len(invalid_result["actual"].split()))
        if key not in total_results:
            total_results[key] = 0
        total_results[key] += 1
        assertion(invalid_result["buffer"] + " correcting '" + invalid_result["correction"] + "' does not yield '" + invalid_result["result"] + "' but '" + invalid_result["actual"] + "'", False)

    for invalid_result in selfrepair_results[4]:
        key = str(len(invalid_result["inserted"].split())) + "-" + str(len(invalid_result["selfrepaired"].split())) + "-" + str(len(invalid_result["actual"].split()))
        if key not in total_results:
            total_results[key] = 0
        total_results[key] += 1
        assertion(invalid_result["buffer"] + " correcting '" + invalid_result["inserted"] + "' does not yield '" + invalid_result["selfrepaired"] + "' but '" + invalid_result["actual"] + "'", False)

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
    # 3 query = 27
    # 4 query = 8
    # 5 query = 2

    # Distribution of correct results of the current algorithm
    # 109 - Expected nothing, got nothing!
    # 1 query = 48 = 100% positive rate
    # 2 query = 137 = 94.5% positive rate
    # 3 query = 207 = 89% positive rate
    # 4 query = 57 = 88% positive rate
    # 5 query = 4 = 66% positive rate ( Low sample size )
    # 6 query = 1 = 100% positive rate ( Low sample size )

    # After changing the skip rule to check the syllable count of the skipped word
    # 37 errors, rather than 45 - Improved by 8
    # 5 / 37 = 14% = Expected result, got NOTHING
    # 27 / 37 = 73% = Expected NOTHING, got result
    # 1 query = 0
    # 2 query = 8
    # 3 query = 22
    # 4 query = 5
    # 5 query = 2

    # After fixing the bug where skips were checked for lowest consecutive score
    # 41 errors, up from 37
    # 4 / 41 = 10% = Expected result, got NOTHING
    # 31 / 41 = 75% = Expected NOTHING, got result
    # 1 query = 0
    # 2 query = 11
    # 3 query = 22
    # 4 query = 5
    # 5 query = 2

    # After some result fixes, the errors were back down at 37
    # 19 of 37 errors ( 51% ) are because of faulty skips, or a skip being included
    # Meaning we can fix a lot of bugs if we find a logical ruleset for skips being allowed or not

    # After adding a constant penalty for a skipped word
    # 35 errors / down from 37
    # 0 / 35 = 0% = Expected result, got NOTHING
    # 35 = 100% = Expected NOTHING, got result
    # 1 query = 0
    # 2 query = 9
    # 3 query = 18
    # 4 query = 6
    # 5 query = 2

    # After not allowing skips with words that are longer than the surrounding words
    # 31 errors / Down from 35
    # 6 / 31 = 20% = Expected result, got NOTHING
    # 21 / 31 = 68% = Expected NOTHING, got result
    # 1 query = 0
    # 2 query = 7
    # 3 query = 18
    # 4 query = 5
    # 5 query = 0
    # 6 query = 1

    # After increasing the max mismatch score to be 0.25
    # 25 errors / Down from 31
    # 5 / 25 = 20% = Expected result, got NOTHING
    # 20 / 25 = 80% = Expected NOTHING, got result
    # 1 query = 0
    # 2 query = 9
    # 3 query = 14
    # 4 query = 1
    # 5 query = 1
    # 6 query = 0

    # After adding max mismatch score for combined words ( 0.5 ) and disallowing 0 scores at the start or end
    # 20 errors / Down from 20
    # 8 / 20 = 40% = Expected result, got NOTHING
    # 11 / 20 = 55% = Expected NOTHING, got result
    # 1 query = 0
    # 2 query = 8
    # 3 query = 9
    # 4 query = 2
    # 5 query = 1
    # 6 query = 0

    # Satisfied with 96% accuracy - Starting improvements for correction

    # Correction results from the above changes - 57.8% accuracy
    # 211 errors counted
    # 191 / 211 = 90% = Expected result, got NOTHING
    # 1 / 211 = <1% = Expected NOTHING, got result
    # 1 correction = 8
    # 2 correction = 25
    # 3 correction = 63
    # 4 correction = 51
    # 5 correction = 38
    # 6 correction = 10
    # 7 correction = 7

    # After removing skip protection
    # 176 errors / down from 211 - 64.8% accuracy
    # 152 / 176 = 86% = Expected result, got NOTHING
    # 1 / 176 = <1% = Expected NOTHING, got result
    # 1 correction = 8
    # 2 correction = 22
    # 3 correction = 55
    # 4 correction = 43
    # 5 correction = 33
    # 6 correction = 10
    # 7 correction = 5

    # After using the correct correction threshold ( doh )
    # 66 errors / down from 176 - 86.8%

    # After fixing some invalid results in the test set
    # 54 errors / down from 66 - 89.2%
    # 10 / 54 = 19% = Expected result, got NOTHING
    # 12 / 54 = 22% = Expected NOTHING, got result
    # Unexpected results = 59%
    # 1 correction = 3
    # 2 correction = 8
    # 3 correction = 18
    # 4 correction = 9
    # 5 correciton = 8
    # 6 correction = 2
    # 7 correction = 2
    # Missed a couple

    # TODO - Discourage combination with punctuations?
    # TODO - Add boost for starting syllable?

    # Tweaked controversial results and added some small changes
    # 95% accuracy for correction
    # I'm fine with 94%+
    # Final tweaks for correction and selection differences
    # 26 errors / down from 54
    # 1 / 26 = 4% = Expected result, got NOTHING
    # 14 / 26 = 54% = Expected NOTHING, got result
    # Unexpected results = 42%
    # 1 correction = 0
    # 2 correction = 3
    # 3 correction = 17
    # 4 correction = 5
    # 5 correction = 3
    # 6 correction = 1
    # 7 correction = 0

    # After fixing unit tests and reconnecting self-repair to the new algorithm
    # 73.4% accuracy - 133 errors
    # 106 = 80% = Expected result, got NOTHING
    # 22 = 17% = Expected NOTHING, got result
    # Unexpected results = 3%
    # 1 correction = 2
    # 2 correction = 7
    # 3 correction = 32
    # 4 correction = 25
    # 5 correction = 25
    # 6 correction = 19
    # 7 correction = 9
    # 8 correction = 6
    # 9 correction = 3
    # 10 correction = 1
    # 11 correction = 3
    # 12 correction = 1

    # After changing the first match requirement to be over the correction threshold
    # 83% accuracy - 85 errors - Down from 133
    # 46 = 54% = Expected result, got NOTHING
    # 29 = 34% = Expected NOTHING, got result
    # Unexpected results = 12%
    # 1 correction = 0
    # 2 correction = 3
    # 3 correction = 23
    # 4 correction = 16
    # 5 correction = 15
    # 6 correction = 14
    # 7 correction = 5
    # 8 correction = 5
    # 9 correction = 2
    # 10 correction = 0
    # 11 correction = 1
    # 12 correction = 1

    # After adding an exception for first match not being good but the rest being excellent
    # 88.8% accuracy - 56 errors - Down from 85
    # 12 = 21% = Expected result, got NOTHING
    # 29 = 52% = Expected NOTHING, got result
    # Unexpected results = 27%
    # 1 correction = 0
    # 2 correction = 2
    # 3 correction = 19
    # 4 correction = 7
    # 5 correction = 11
    # 6 correction = 10
    # 7 correction = 2
    # 8 correction = 2
    # 9 correction = 0
    # 10 correction = 0
    # 11 correction = 1
    # 12 correction = 1

    # TODO IMPLEMENT PUNCTUATION WITHIN QUERY CHECK
    # After correcting some mistakes in the test set
    # 90.4% accuracy

    # Performance benchmarks
    # For selection, 36.2% were unnecessary duplicate checks
    # For correction, 56.0% were unnecessary duplicate checks
    # For self-repair, 68.4% were unnecessary duplicate checks

    # After improving running performance the following accuracy has been observed
    # 90.6 % for selection - Down from 94%
    # 81.8 % for correction - Down from 87.8%
    # 85.6 % for self-repair - Down from 89.8%

    # After adding dynamic threshold selection based on initial branches
    # And only doing skip branching at the start
    # 94% for selection
    # 87.4% for correction
    # 89.8% for self-repair

    # After adding branch scoring for initial branches
    # No clue why that would affect performance lol
    # 94.8% for selection
    # 89.2% for correction
    # 90% for self-repair

    # After improving the performance of self-repair matching
    # The speed-up went from 10 seconds to 1.5 seconds for the self-repair tests
    # Which makes the trade-off worth it
    # 94.6% for selection
    # 88.6% for correction
    # 74.8% for self-repair

    # 82.8% after changing the sorting for self repair and fixing the punctuation and fixing an error in the test set
    # After looking through the 86 error results, these were the types of errors I could find
    # Expected NOTHING, but got SOMETHING: 16 times
    # First item should be replaced: 25 times
    # Single item that should be replaced: 6 times
    # Should append before: 1 time
    # Incorrect punctuation filter: 5 times
    # Post punctuation long match: 1 time
    # Deeper selection than expected: 22 times

    # Thoughts: Maybe I can reweigh the scores based on the buffer instead of the query to make 'of the ...' not match as aggressively to fix the 16 nothing errors
    # I should also not only check the first tokens for matches in case I need to replace or append items to fix 26 errors
    # And re-evaluate what single word matches should be so I don't match 'to' and 'do', but do match other items
    # Punctuation filtering needs to be fixed properly to fix the 6 errors
    # Also, the sorting needs to be improved so that not always longer items are approved if better matches are found
    # to fix the deeper than expected errors
    # Fixing these well would fix 68 out of 86 errors, leaving us with 18 errors, or a 96%+ success rate

    # After adding a score difference check for self repair sorting
    # 70 errors, down from 86 - accuracy 86.2%
    # Correction accuracy 87.6%
    # Selection accuracy 94.4%
    # 65 errors after punctuation fix - accuracy 87.2%
    # Correction accuracy 86.8% - Unsure why these changes affect correction
    # Selection accuracy 93.8% - Unsure why these changes affect selection
    
    # For some reason, running tests from one category affects the other category, unsure why
    # Because correction then fluctuates from 89% to 87% without a solid explanation
    # 89.6% correction - Run 1
    # 89.2% correction - Run 2
    # 88.2% correction - Run 3
    # After fixing the tokens containing # in front of them
    # 95% selection - No fluctuatoin
    # 89.6% correction - Fluctuates between 89.8 and 89.6 percent still
    # 87.4% self repair - No fluctuation

    # Investigating correction ( 51 errors ), the following could be found
    # Incorrect because better find is found further away: 6
    # Expected nothing, matched with something: 9
    # Could not find match: 9
    # More than expected: 10
    # Less than exected: 9
    # Incorrect but middle was exact: 3
    # Multiple repeats: 4
    # Multiple skips: 1
    # Swapped word: 1
    # Thoughts: Clearly there's room to be gained both in the sorting department to match with better matches ( 6 times )
    # And with the proper expanding of the selection, seeing as they were almost correct ( 19 times )
    # There's also a lot of issues with short queries matching / not matching properly that needs to be looked at

    # After changing self repair sorting to match most direct matches before matching by score
    # 88.2% self repair
    # Investigating self repair matches, I'm seeing a lot of matches that could have started earlier because there was no exact match with the first
    # After adding starting branches on the second token combinations
    # 90.4% self repair accuracy
    # After still seeing some ineffective checks for non-direct match firsts and adding a check for high secondary matches
    # 91.2% self repair accuracy
    # After adding direct continuation checks ( feast ... -> feasting )
    # 91.8% self repair accuracy
    # TODO Skip query match for self repair / correction ? Seems to be at least one that happens because of that
    # After changing sorting again by adding a penalty for longer bad score matches at the start of self repair
    # 92% self repair accuracy
    # TODO Rescore based on buffer weights
    # After rebalancing based on proper weights
    # 91.2% self repair accuracy
    # After fixing sort bug
    # 91.6% self repair accuracy
    # Amount of skipped additional query words: 4
    # A bunch of longer words at the end as well that do not match properly
    # After adding a bad ending match check and moving the first token continuation check
    # 92.6% self repair accuracy
    # After tweaking starting requirement for words longer than 2 syllables
    # 92.8% self repair accuracy

    #for regression in selection_results[3]:
        #key = str(len(regression["query"].split())) + "-" + str(len(regression["result"].split()))
    #    if key not in total_results:
    #        total_results[key] = 0
    #    total_results[key] += 1
    #    assertion(regression["buffer"] + " searching '" + regression["query"] + "' does not yield '" + regression["result"] + "' but '" + regression["actual"] + "'")
    #print( total_results )
    #selection_tests(assertion, False, True)

def percentage_test_selection(assertion):
    percentage_tests(assertion, True, False, False, 0.94)

def percentage_test_correction(assertion):
    percentage_tests(assertion, False, True, False, 0.9)

def percentage_test_selfrepair(assertion):
    percentage_tests(assertion, False, False, True, 0.95)

suite = create_test_suite("Selecting whole phrases inside of a selection")
#suite.add_test(percentage_test_selection)
#suite.add_test(percentage_test_correction)
suite.add_test(percentage_test_selfrepair)
#suite.add_test(percentage_tests)
suite.run() 