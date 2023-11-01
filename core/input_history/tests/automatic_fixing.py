from ..input_fixer import InputFixer
from ...utils.test import create_test_suite

def get_input_fixer():
    return InputFixer("en", "test", None)

def test_empty_fixer(assertion):
    input_fixer = get_input_fixer()
    assertion( "Using an empty input fixer")
    assertion( "    Inserting 'want too make'...")
    text = input_fixer.automatic_fix("too", "want", "make")
    assertion( "        Should not change the text automatically because it has no fixes", text == "too")
    assertion( "    Adding a single fix for 'want too make' and inserting it again...")
    input_fixer.add_fix("too", "to", "want", "make")
    text = input_fixer.automatic_fix("too", "want", "make")
    assertion( "        Should change the text automatically because the automatic fixes are persisted", text == "to")
    assertion( "    Inserting 'want too make' again should give 'want to make'")
    text = input_fixer.automatic_fix("too", "want", "make")
    assertion( "        Should change the text automatically", text == "to")

def test_evolving_automatic_fix(assertion):
    input_fixer = get_input_fixer()
    assertion( "Using an input fixer with the word 'period' as a known no-context fix to be '.'")
    input_fixer.add_fix("period", ".", "", "", 6)
    assertion( "    Inserting 'a period of'...")
    text = input_fixer.automatic_fix("period", "a", "of")
    assertion( "        Should change the text automatically because the zero-context fix is to change period to .", text == ".")
    assertion( "    Adding a single fix for 'a . of' and inserting it again...")
    input_fixer.add_fix(".", "period", "a", "of")
    text = input_fixer.automatic_fix("period", "a", "of")
    assertion( "        Should change the text automatically because the automatic fixes with more context are persisted", text == "period")
    assertion( "    Inserting 'a period that'...")
    text = input_fixer.automatic_fix("period", "a", "that")
    assertion( "         Should also keep the word 'period' because it has matching previous context...", text == "period")
    assertion( "    Inserting 'the period of'...")
    text = input_fixer.automatic_fix("period", "the", "of")
    assertion( "         Should also keep the word 'period' because it has matching next context...", text == "period")
    assertion( "    Inserting 'birds period and'...")
    text = input_fixer.automatic_fix("period", "birds", "and")
    assertion( "         Should keep using . as a fix because no known fixes have been made with the given context", text == ".")

suite = create_test_suite("Automatically fixing input")
suite.add_test(test_empty_fixer)
suite.add_test(test_evolving_automatic_fix)