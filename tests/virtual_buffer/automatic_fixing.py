from ...virtual_buffer.input_fixer import InputFixer
from ..test import create_test_suite

def get_input_fixer():
    return InputFixer("en", "test", None, 0, testing=True)

def test_empty_fixer(assertion):
    input_fixer = get_input_fixer()
    assertion( "Using an empty input fixer")
    assertion( "    Inserting 'want too make'...")
    text = input_fixer.automatic_fix("too", "want", "make")
    assertion( "        Should not change the text because it has no fixes", text == "too")
    fixed_word_list = input_fixer.automatic_fix_list(["want", "too", "make"], "", "")
    assertion( "        Should not change the list because it has no fixes", fixed_word_list == ["want", "too", "make"])

def test_single_no_context_word_fixer(assertion):
    input_fixer = get_input_fixer()
    input_fixer.add_fix("drab", "trap", "", "", 10)
    assertion( "Using a single to single word input fixer")
    assertion( "    Inserting 'It is a drab'...")
    text = input_fixer.automatic_fix("drab", "a", "")
    assertion( "        Should not change the text from 'drab' to 'trap'", text == "trap")
    fixed_word_list = input_fixer.automatic_fix_list(["is", "a", "drab"], "it", "")
    assertion( "        Should change the text automatically because it has a fix for 'drab' to 'trap'", fixed_word_list == ["is", "a", "trap"])
    assertion( "    Inserting 'want too make'...")
    text = input_fixer.automatic_fix("too", "want", "make")
    assertion( "        Should not change the text because it has no fixes for these words", text == "too")
    fixed_word_list = input_fixer.automatic_fix_list(["want", "too", "make"], "", "")
    assertion( "        Should not change the list because it has no fixes for these words", fixed_word_list == ["want", "too", "make"])    

def test_single_word_half_context_word_fixer(assertion):
    input_fixer = get_input_fixer()
    input_fixer.add_fix("to", "too", "late", "", 5)
    input_fixer.add_fix("too", "to", "", "late", 5)
    assertion( "Using a single to single word input fixer with half context")
    assertion( "    Inserting 'I want it too'...")
    text = input_fixer.automatic_fix("too", "it", "")
    assertion( "        Should not change the text from 'too' to 'to' because it has insufficient matching context", text == "too")
    fixed_word_list = input_fixer.automatic_fix_list(["want", "it", "too"], "I", "")
    assertion( "        Should not change the list either", fixed_word_list == ["want", "it", "too"])
    assertion( "    Inserting 'It is too late'...")
    text = input_fixer.automatic_fix("too", "is", "late")
    assertion( "        Should change the text from 'too' to 'to' because it has matching context", text == "to")
    fixed_word_list = input_fixer.automatic_fix_list(["is", "too", "late"], "it", "")
    assertion( "        Should change the list as well", fixed_word_list == ["is", "to", "late"])

def test_single_word_full_context_word_fixer(assertion):
    input_fixer = get_input_fixer()
    input_fixer.add_fix("too", "to", "far", "late", 2)
    assertion( "Using a single to single word input fixer with full context")
    assertion( "    Inserting 'I want it too'...")
    text = input_fixer.automatic_fix("too", "it", "")
    assertion( "        Should not change the text from 'too' to 'to' because it has insufficient matching context", text == "too")
    fixed_word_list = input_fixer.automatic_fix_list(["want", "it", "too"], "I", "")
    assertion( "        Should not change the list either", fixed_word_list == ["want", "it", "too"])
    assertion( "    Inserting 'It is too late'...")
    text = input_fixer.automatic_fix("too", "is", "late")
    assertion( "        Should not change the text from 'too' to 'to' because it has no matching context", text == "too")
    fixed_word_list = input_fixer.automatic_fix_list(["is", "too", "late"], "it", "")
    assertion( "        Should not change the list either", fixed_word_list == ["is", "too", "late"])
    assertion( "    Inserting 'It is far too late'...")
    text = input_fixer.automatic_fix("too", "far", "late")
    assertion( "        Should change the text from 'too' to 'to' because it has matching context", text == "to")
    fixed_word_list = input_fixer.automatic_fix_list(["is", "far", "too", "late"], "it", "")
    assertion( "        Should change the list as well", fixed_word_list == ["is", "far", "to", "late"])

def test_single_word_to_double_word_no_context_fixer(assertion):
    input_fixer = get_input_fixer()
    input_fixer.add_fix("allots", "a lot", "", "", 10)
    assertion( "Using a single to multiple word input fixer")
    assertion( "    Inserting 'It is allots'...")
    text = input_fixer.automatic_fix("allots", "is", "")
    assertion( "        Should change the text from 'allots' to 'a lot'", text == "a lot")
    fixed_word_list = input_fixer.automatic_fix_list(["is", "allots"], "it", "")
    assertion( "        Should change the text automatically because it has a fix for 'allots' to 'a lot'", fixed_word_list == ["is", "a", "lot"])

def test_double_word_to_single_word_no_context_fixer(assertion):
    input_fixer = get_input_fixer()
    input_fixer.add_fix("and sure", "ensure", "", "", 10)
    assertion( "Using a double to single word input fixer")
    assertion( "    Inserting 'And sure the place'...")
    text = input_fixer.automatic_fix("and sure", "", "the")
    assertion( "        Should change the text from 'and sure' to 'ensure'", text == "ensure")
    fixed_word_list = input_fixer.automatic_fix_list(["and", "sure", "the", "place"], "", "")
    assertion( "        Should change the text automatically because it has a fix for 'and sure' to 'ensure'", fixed_word_list == ["ensure", "the", "place"])

suite = create_test_suite("Automatically fixing input")
suite.add_test(test_empty_fixer)
suite.add_test(test_single_no_context_word_fixer)
suite.add_test(test_single_word_half_context_word_fixer)
suite.add_test(test_single_word_full_context_word_fixer)
suite.add_test(test_single_word_to_double_word_no_context_fixer)
suite.add_test(test_double_word_to_single_word_no_context_fixer)