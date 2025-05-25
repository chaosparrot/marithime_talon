from ...virtual_buffer.input_fixer import InputFixer
from ..test import create_test_suite
from ...phonetics.phonetics import PhoneticSearch

def get_phonetic_search() -> PhoneticSearch:
    phonetic_search = PhoneticSearch()
    phonetic_search.set_homophones("""to,too,two
where,wear,ware""")
    phonetic_search.set_phonetic_similiarities("")
    phonetic_search.set_semantic_similarities("")
    return phonetic_search

def get_input_fixer():
    fixer = InputFixer("en", "test", None, 0, testing=True)
    fixer.phonetic_search = get_phonetic_search()
    return fixer

def test_cycle_through_no_fixes(assertion):
    input_fixer = get_input_fixer()

    assertion( "Using an empty input fixer")
    fixed_text, amount = input_fixer.cycle_through_fixes("because the", 1)
    assertion( "    Cycling through 'because the'...")
    assertion( "        Should not increase the cycle amount", amount <= 1)
    assertion( "        Should change the text being repeated", fixed_text == "because the")
    assertion( "    Cycling through 'because the' again...")
    fixed_text, amount = input_fixer.cycle_through_fixes("because the", amount)
    assertion( "        Should not increase the cycle amount", amount <= 1)
    assertion( "        Should change the text being repeated", fixed_text == "because the")

def test_cycle_through_single_word_fix(assertion):
    input_fixer = get_input_fixer()

    assertion( "Using an empty input fixer")
    fixed_text, amount = input_fixer.cycle_through_fixes("to", 1)
    assertion( "    Cycling through 'to'...")
    assertion( "        Should increase the cycle amount by 1", amount == 1)
    assertion( "        Should change the text being repeated to 'too'", fixed_text == "too")
    fixed_text, amount = input_fixer.cycle_through_fixes("to", amount + 1)
    assertion( "    Cycling through 'to' again...")
    assertion( "        Should increase the cycle amount by 1", amount == 2)
    assertion( "        Should change the text being repeated to 'two'", fixed_text == "two")
    fixed_text, amount = input_fixer.cycle_through_fixes("to", amount + 1)
    assertion( "    Cycling through 'to' another time...")
    assertion( "        Should set the cycle amount to 0 again", amount == 0)
    assertion( "        Should change the text being repeated to 'to'", fixed_text == "to")    

def test_cycle_through_single_word_fix_at_the_start(assertion):
    input_fixer = get_input_fixer()

    assertion( "Using an empty input fixer")
    fixed_text, amount = input_fixer.cycle_through_fixes("to the", 1)
    assertion( "    Cycling through 'to the'...")
    assertion( "        Should increase the cycle amount by 1", amount == 1)
    assertion( "        Should change the text being repeated to 'too the'", fixed_text == "too the")
    fixed_text, amount = input_fixer.cycle_through_fixes("to the", amount + 1)
    assertion( "    Cycling through 'to the' again...")
    assertion( "        Should increase the cycle amount by 1", amount == 2)
    assertion( "        Should change the text being repeated to 'two the'", fixed_text == "two the")
    fixed_text, amount = input_fixer.cycle_through_fixes("to the", amount + 1)
    assertion( "    Cycling through 'to the' another time...")
    assertion( "        Should set the cycle amount to 0 again", amount == 0)
    assertion( "        Should change the text being repeated to 'to the'", fixed_text == "to the")

def test_cycle_through_single_word_fix_at_the_end(assertion):
    input_fixer = get_input_fixer()

    assertion( "Using an empty input fixer")
    fixed_text, amount = input_fixer.cycle_through_fixes("the to", 1)
    assertion( "    Cycling through 'the to'...")
    assertion( "        Should increase the cycle amount by 1", amount == 1)
    assertion( "        Should change the text being repeated to 'the too'", fixed_text == "the too")
    fixed_text, amount = input_fixer.cycle_through_fixes("the to", amount + 1)
    assertion( "    Cycling through 'the to' again...")
    assertion( "        Should increase the cycle amount by 1", amount == 2)
    assertion( "        Should change the text being repeated to 'the two'", fixed_text == "the two")
    fixed_text, amount = input_fixer.cycle_through_fixes("the to", amount + 1)
    assertion( "    Cycling through 'the to' another time...")
    assertion( "        Should set the cycle amount to 0 again", amount == 0)
    assertion( "        Should change the text being repeated to 'the to'", fixed_text == "the to")

def test_cycle_through_multiple_consecutive_word_fixes(assertion):
    input_fixer = get_input_fixer()

    assertion( "Using an empty input fixer")
    fixed_text, amount = input_fixer.cycle_through_fixes("to where", 1)
    assertion( "    Cycling through 'to where'...")
    assertion( "        Should increase the cycle amount by 1", amount == 1)
    assertion( "        Should change the text being repeated to 'to where'", fixed_text == "to wear")
    fixed_text, amount = input_fixer.cycle_through_fixes("to where", amount + 1)
    assertion( "    Cycling through 'to where' a second time...")
    assertion( "        Should increase the cycle amount by 1", amount == 2)
    assertion( "        Should change the text being repeated to 'to where'", fixed_text == "to ware")
    fixed_text, amount = input_fixer.cycle_through_fixes("to where", amount + 1)
    assertion( "    Cycling through 'to where' a third time...")
    assertion( "        Should increase the cycle amount by 1", amount == 3)
    assertion( "        Should change the text being repeated to 'too where'", fixed_text == "too where")
    fixed_text, amount = input_fixer.cycle_through_fixes("to where", amount + 1)
    assertion( "    Cycling through 'to where' a fourth time...")
    assertion( "        Should increase the cycle amount by 1", amount == 4)
    assertion( "        Should change the text being repeated to 'two where'", fixed_text == "two where")
    fixed_text, amount = input_fixer.cycle_through_fixes("to where", amount + 1)
    assertion( "    Cycling through 'to where' a fifth time...")
    assertion( "        Should set the cycle amount to 0 again", amount == 0)
    assertion( "        Should change the text being repeated to 'to where'", fixed_text == "to where")    

def test_cycle_through_the_same_multiple_consecutive_word_fixes(assertion):
    input_fixer = get_input_fixer()

    assertion( "Using an empty input fixer")
    fixed_text, amount = input_fixer.cycle_through_fixes("to to", 1)
    assertion( "    Cycling through 'to to'...")
    assertion( "        Should increase the cycle amount by 1", amount == 1)
    assertion( "        Should change the text being repeated to 'to too'", fixed_text == "to too")
    fixed_text, amount = input_fixer.cycle_through_fixes("to to", amount + 1)
    assertion( "    Cycling through 'to to' a second time...")
    assertion( "        Should increase the cycle amount by 1", amount == 2)
    assertion( "        Should change the text being repeated to 'to two'", fixed_text == "to two")
    fixed_text, amount = input_fixer.cycle_through_fixes("to to", amount + 1)
    assertion( "    Cycling through 'to to' a third time...")
    assertion( "        Should increase the cycle amount by 1", amount == 3)
    assertion( "        Should change the text being repeated to 'too to'", fixed_text == "too to")
    fixed_text, amount = input_fixer.cycle_through_fixes("to to", amount + 1)
    assertion( "    Cycling through 'to to' a fourth time...")
    assertion( "        Should increase the cycle amount by 1", amount == 4)
    assertion( "        Should change the text being repeated to 'two to'", fixed_text == "two to")
    fixed_text, amount = input_fixer.cycle_through_fixes("to to", amount + 1)
    assertion( "    Cycling through 'to to' a fifth time...")
    assertion( "        Should set the cycle amount to 0 again", amount == 0)
    assertion( "        Should change the text being repeated to 'to to'", fixed_text == "to to")    


def test_cycle_through_multiple_word_fixes_with_a_gap(assertion):
    input_fixer = get_input_fixer()

    assertion( "Using an empty input fixer")
    fixed_text, amount = input_fixer.cycle_through_fixes("to big where", 1)
    assertion( "    Cycling through 'to big where'...")
    assertion( "        Should increase the cycle amount by 1", amount == 1)
    assertion( "        Should change the text being repeated to 'to big wear'", fixed_text == "to big wear")
    fixed_text, amount = input_fixer.cycle_through_fixes("to big where", amount + 1)
    assertion( "    Cycling through 'to big where' a second time ...")
    assertion( "        Should increase the cycle amount by 1", amount == 2)
    assertion( "        Should change the text being repeated to 'to big ware'", fixed_text == "to big ware")
    fixed_text, amount = input_fixer.cycle_through_fixes("to big where", amount + 1)
    assertion( "    Cycling through 'to big where' a third time ...")
    assertion( "        Should increase the cycle amount by 1", amount == 3)
    assertion( "        Should change the text being repeated to 'too big where'", fixed_text == "too big where")
    fixed_text, amount = input_fixer.cycle_through_fixes("to big where", amount + 1)
    assertion( "    Cycling through 'to big where' a fourth time ...")
    assertion( "        Should increase the cycle amount by 1", amount == 4)
    assertion( "        Should change the text being repeated to 'two big where'", fixed_text == "two big where")
    fixed_text, amount = input_fixer.cycle_through_fixes("to big where", amount + 1)
    assertion( "    Cycling through 'to big where' a fifth time ...")
    assertion( "        Should set the cycle amount to 0 again", amount == 0)
    assertion( "        Should change the text being repeated to 'to big where'", fixed_text == "to big where")

suite = create_test_suite("Cycle through phonetic fixes when they are repeated")
suite.add_test(test_cycle_through_no_fixes)
suite.add_test(test_cycle_through_single_word_fix)
suite.add_test(test_cycle_through_single_word_fix_at_the_start)
suite.add_test(test_cycle_through_single_word_fix_at_the_end)
suite.add_test(test_cycle_through_multiple_consecutive_word_fixes)
suite.add_test(test_cycle_through_the_same_multiple_consecutive_word_fixes)
suite.add_test(test_cycle_through_multiple_word_fixes_with_a_gap)