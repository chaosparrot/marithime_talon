from ..input_fixer import InputFixer
from ...phonetics.phonetics import PhoneticSearch
from ...utils.test import create_test_suite

def get_input_fixer() -> InputFixer:
    input_fixer = InputFixer("en", "test", None)
    search = PhoneticSearch()
    search.set_homophones("")
    search.set_phonetic_similiarities("")
    input_fixer.phonetic_search = search
    return input_fixer

def test_single_token_replacement(assertion):
    input_fixer = get_input_fixer()
    assertion( "Single token to single token test")
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

def test_multiple_token_replacement(assertion):
    input_fixer = get_input_fixer()
    assertion( "Multiple token to single token test")
    input_fixer.track_fix("I like it allots", "I like it a lot", "", "")
    assertion( "    Tracking a fix for a one word to two words 'I like it allots' -> 'I like it a lot'")
    assertion( "        Should have 'allots' -> 'a lot' saved as a full context fix", "allots" in input_fixer.known_fixes)
    input_fixer.track_fix("And sure the biggest customer is paying", "Ensure the biggest customer is paying", "", "")
    assertion( "    Tracking a fix for two words to one word 'And sure the biggest customer is paying' -> 'Ensure the biggest customer is paying'")
    assertion( "        Should have 'and sure' -> 'ensure' saved as a full context fix", "and sure" in input_fixer.known_fixes)

suite = create_test_suite("Using an empty input fixer and phonetic search")
suite.add_test(test_single_token_replacement)
suite.add_test(test_multiple_token_replacement)