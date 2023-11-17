from ..input_fixer import InputFixer
from ...phonetics.phonetics import PhoneticSearch
from ...utils.test import create_test_suite

def get_input_fixer() -> InputFixer:
    input_fixer = InputFixer("en", "test", None, 0)
    search = PhoneticSearch()
    search.set_homophones("")
    search.set_phonetic_similiarities("")
    input_fixer.phonetic_search = search
    return input_fixer

def test_single_token_full_context_replacement(assertion):
    input_fixer = get_input_fixer()
    assertion( "Single token to single token test full-context replacement")
    assertion( "    Tracking a fix for a single word 'the night in shining armour' -> 'the knight in shining armour'")
    input_fixer.track_fix("night in shining armour", "knight in shining armour", "the", "")
    assertion( "        Should add the homophone 'night' and 'knight' because of the similarity", len(input_fixer.phonetic_search.find_homophones("night")) >= 0)
    assertion( "        Should track the fix from night and knight in the input fixer", input_fixer.get_key("night", "knight") in input_fixer.done_fixes)
    assertion( "    Tracking a fix for a single word 'the night in black armour' -> 'the knight in black armour'")
    input_fixer.track_fix("night in black armour", "knight in black armour", "the", "")
    assertion( "        Should have 'night' saved as a full context fix", "night" in input_fixer.known_fixes)
    assertion( "    Inserting 'the night in dark armour'...")
    assertion( "        Should automatically fix 'night' to 'knight'", input_fixer.automatic_fix("night", "the", "in") == "knight")
    assertion( "    Inserting 'a night in March'...")
    assertion( "        Should not change 'night'", input_fixer.automatic_fix("night", "a", "in") == "night")

def test_single_token_half_context_replacement(assertion):
    input_fixer = get_input_fixer()
    assertion( "Single token to single token test half-context replacement")
    assertion( "    Tracking in-context fixes for a single word 'that's' -> 'that'")
    input_fixer.track_fix("that's is not mine", "that is not mine", "", "")
    input_fixer.track_fix("is that's not mine", "is that not mine", "", "")
    input_fixer.track_fix("that's is not fair", "that is not fair", "", "")
    input_fixer.track_fix("that's isn't easy", "that isn't easy", "", "")
    input_fixer.track_fix("that's is barely fair", "that is barely fair", "", "")
    assertion( "        Should track the fix from 'that's' -> 'that' in the input fixer", input_fixer.find_fix("that's", "in", "is") is not None and input_fixer.find_fix("that's", "in", "is").to_text == "that")
    assertion( "    Inserting 'that's is not his'...")
    assertion( "        Should automatically fix 'that's' to 'that'", input_fixer.automatic_fix("that's", "", "is") == "that")
    assertion( "        Should fix a list of 'that's' to 'that' as well", input_fixer.automatic_fix_list(["that's", "is", "not", "his"], "", "") == ["that", "is", "not", "his"])
    assertion( "    Inserting 'is that's not'...")
    assertion( "        Should not change 'that's' because it hasn't been replaced enough times", input_fixer.automatic_fix("that's", "is", "not") == "that's")
    assertion( "        Should fix a list either", input_fixer.automatic_fix_list(["is", "that's", "not", "his"], "", "") == ["is", "that's", "not", "his"])

def test_single_to_double_token_no_context_replacement(assertion):
    input_fixer = get_input_fixer()
    assertion( "Single token to double token test no-context replacement")
    assertion( "    Tracking fixes for a single word 'allots' -> 'a lot'")
    input_fixer.track_fix("allots of things", "a lot of things", "", "")
    input_fixer.track_fix("I want it allots", "I want it a lot", "", "")
    input_fixer.track_fix("allots more than we", "a lot more than we", "", "")
    input_fixer.track_fix("having allots of", "having a lot of", "", "")
    input_fixer.track_fix("doing allots for", "doing a lot for", "", "")
    input_fixer.track_fix("in allots of ways", "in a lot of ways", "", "")        
    assertion( "        Should track the fix from 'allots' -> 'a lot' in the input fixer", input_fixer.find_fix("allots", "in", "of") is not None and input_fixer.find_fix("allots", "in", "of").to_text == "a lot")
    assertion( "    Inserting 'allots less of a problem'...")
    assertion( "        Should automatically fix 'allots' to 'a lot'", input_fixer.automatic_fix("allots", "", "less") == "a lot")
    assertion( "        Should fix a list of 'allots' to 'a lot' as well", input_fixer.automatic_fix_list(["allots", "less", "of"], "", "a") == ["a", "lot", "less", "of"])

def test_double_to_single_token_no_context_replacement(assertion):
    input_fixer = get_input_fixer()
    assertion( "Double token to single token test no-context replacement")
    assertion( "    Tracking fixes for double words 'and sure' -> 'ensure'")
    input_fixer.track_fix("and sure this car", "ensure this car", "", "")
    input_fixer.track_fix("to and sure these", "to ensure these", "", "")
    input_fixer.track_fix("want to and sure", "want to ensure", "", "")
    input_fixer.track_fix("I and sure you", "I ensure you", "", "")
    input_fixer.track_fix("we should and sure them", "we should ensure them", "", "")
    input_fixer.track_fix("he must and sure that", "he must ensure that", "", "")        
    assertion( "        Should track the fix from 'and sure' -> 'ensure' in the input fixer", input_fixer.find_fix("and sure", "", "") is not None and input_fixer.find_fix("and sure", "", "").to_text == "ensure")
    assertion( "    Inserting 'they and sure us that'...")
    assertion( "        Should automatically fix 'and sure' to 'ensure'", input_fixer.automatic_fix("and sure", "they", "us") == "ensure")
    assertion( "        Should fix a list of 'and sure' to 'ensure' as well", input_fixer.automatic_fix_list(["they", "and", "sure", "us"], "", "") == ["they", "ensure", "us"])

suite = create_test_suite("Tracking fixes from text replacements")
suite.add_test(test_single_token_full_context_replacement)
suite.add_test(test_single_token_half_context_replacement)
suite.add_test(test_single_to_double_token_no_context_replacement)
suite.add_test(test_double_to_single_token_no_context_replacement)