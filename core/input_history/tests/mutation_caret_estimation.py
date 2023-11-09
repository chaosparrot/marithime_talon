from ..input_indexer import InputIndexer
from ...utils.test import create_test_suite

def test_inserting_to_single_line(assertion):
    input_indexer = InputIndexer()
    assertion("Adding the text 'test' to 'This is a '")
    location = input_indexer.determine_diverges_from('This is a ', 'This is a test', 'test')
    assertion("    should give line 0, 0 characters from end upon inspection", location == (0, 0))
    assertion("Adding the text 'already' in between 'This is a '")
    location = input_indexer.determine_diverges_from('This is a ', 'This is already a ', 'already ')
    assertion(location)
    assertion("    should give line 0, 2 characters from end upon inspection", location == (0, 2))
    assertion("Adding the text 'But' before ' this is a '")
    location = input_indexer.determine_diverges_from('this is a ', 'But this is a ', 'But ')
    assertion(location)
    assertion("    should give line 0, 10 characters from end upon inspection", location == (0, 10))
    assertion("Adding the text 'n't' within ' this is a '")
    location = input_indexer.determine_diverges_from('This is a ', "This isn't a ", "n't")
    assertion("    should give line 0, 3 characters from end upon inspection", location == (0, 3))
    assertion(location)
    assertion("Adding a new line after 'This is a test.'")
    location = input_indexer.determine_diverges_from('This is a test.', """This is a test.
""", """
""")
    assertion("    should give line 1, 0 characters from end upon inspection", location == (1, 0))

def test_inserting_to_multiline(assertion):
    input_indexer = InputIndexer()
    multiline_haystack = """This is a sentence.
This adds to the sentence and turns it into a small paragraph."""

    multiline_add_very = """This is a sentence.
This adds to the sentence and turns it into a very small paragraph."""

    multiline_add_and = """This is a sentence. And
This adds to the sentence and turns it into a small paragraph."""

    multiline_add_but = """This is a sentence.
This adds to the sentence and turns it into a small paragraph. But"""

    assertion("Within the sentence 'This is a sentence.' followed by 'This adds to the sentence and turns it into a small paragraph.'...")
    location = input_indexer.determine_diverges_from(multiline_haystack, multiline_add_and, " And")
    assertion("    Adding the text ' And' to the end of the first sentence")
    assertion("        should give line 0, 0 characters from end upon inspection", location == (0, 0))
    location = input_indexer.determine_diverges_from(multiline_haystack, multiline_add_but, " But")
    assertion("    Adding the text ' But' to the end of the second sentence")
    assertion("        should give line 1, 0 characters from end upon inspection", location == (1, 0))
    location = input_indexer.determine_diverges_from(multiline_haystack, multiline_add_very, "very ")
    assertion("    Adding the text 'very ' in between the second sentence")
    assertion("        should give line 1, 16 characters from end upon inspection", location == (1, 16))
    assertion( location )

def test_replacing_within_single_line(assertion):
    input_indexer = InputIndexer()
    assertion("Replacing the word 'a' with 'the' in 'This is a test'")
    location = input_indexer.determine_diverges_from('This is a test', 'This is the test', "the")
    assertion("    should give line 0, 5 characters from end upon inspection", location == (0, 5))
    assertion("Replacing the words 'is a ' with 'was the ' in 'This is a test'")    
    location = input_indexer.determine_diverges_from('This is a test', 'This was the test', "was the")
    assertion("    should give line 0, 5 characters from end upon inspection", location == (0, 5))
    assertion("Replacing the words 'is a ' with 'was ' in 'This is a test'")    
    location = input_indexer.determine_diverges_from('This is a test', 'This was test', "was")
    assertion("    should give line 0, 5 characters from end upon inspection", location == (0, 5))
    assertion("Replacing the word 'This' with 'That' in 'This is a test'", "That")
    location = input_indexer.determine_diverges_from('This is a test', 'That is a test', "That")
    assertion("    should give line 0, 10 characters from end upon inspection", location == (0, 10))
    assertion("Replacing the word 'test.' with 'sentence.<newline>' in  'This is a test.'", """sentence.
""")
    location = input_indexer.determine_diverges_from('This is a test.', """This is a sentence.
""", "sentence.\n")
    assertion("    should give line 1, 0 characters from end upon inspection", location == (1, 0))

def test_deleting_within_single_line(assertion):
    input_indexer = InputIndexer()
    assertion("Removing the word 'This' from 'This is a test'")
    location = input_indexer.determine_diverges_from('This is a test', 'is a test')
    assertion("    should give line 0, 9 characters from end upon inspection", location == (0, 9))
    assertion("Removing the word 'a ' from 'This is a test'")
    location = input_indexer.determine_diverges_from('This is a test', 'This is test')
    assertion("    should give line 0, 4 characters from end upon inspection", location == (0, 4))
    assertion("Removing the word 'test' from 'This is a test'")
    location = input_indexer.determine_diverges_from('This is a test', "This is a")
    assertion("    should give line 0, 0 characters from end upon inspection", location == (0, 0))
    assertion("Removing the words 'is a test' from 'This is a test'")
    location = input_indexer.determine_diverges_from('This is a test', "This ")
    assertion("    should give line 0, 0 characters from end upon inspection", location == (0, 0))
    assertion("Removing the characters 'is ' from 'This is a test'")
    location = input_indexer.determine_diverges_from('This is a test', "This a test")
    assertion("    should give line 0, but have the character location as undefined", location == (0, -1))

def test_deleting_within_multiline(assertion):
    input_indexer = InputIndexer()
    multiline_haystack = """This is a sentence.
This adds to the sentence and turns it into a small paragraph."""

    multiline_remove_first_this = """is a sentence.
This adds to the sentence and turns it into a small paragraph."""

    multiline_remove_second_this = """This is a sentence.
adds to the sentence and turns it into a small paragraph."""

    multiline_remove_paragraph = """This is a sentence.
This adds to the sentence and turns it into a small """

    multiline_remove_to_the_sentence = """This is a sentence.
This adds and turns it into a small paragraph."""

    multiline_remove_linebreak = """This is a sentence.This adds to the sentence and turns it into a small paragraph."""
    assertion("Within the sentence 'This is a sentence.' followed by 'This adds to the sentence and turns it into a small paragraph.'...")
    assertion("    Removing the first word 'This'")
    location = input_indexer.determine_diverges_from(multiline_haystack, multiline_remove_first_this)
    assertion("        should give line 0, 14 characters from end upon inspection", location == (0, 14))
    assertion("    Removing the second word 'This'")
    location = input_indexer.determine_diverges_from(multiline_haystack, multiline_remove_second_this)
    assertion("        should give line 1, 42 characters from end upon inspection", location == (1, 57))
    assertion( multiline_remove_second_this[-location[1]:])
    assertion( location )
    assertion("    Removing the words 'to the sentence' from the second line")
    location = input_indexer.determine_diverges_from(multiline_haystack, multiline_remove_to_the_sentence)
    assertion( multiline_remove_to_the_sentence[-location[1]:])
    assertion("        should give line 1, 36 characters from end upon inspection", location == (1, 36))
    assertion("    Removing the word 'paragraph.'")
    location = input_indexer.determine_diverges_from(multiline_haystack, multiline_remove_paragraph)
    assertion("        should give line 1, 0 characters from end upon inspection", location == (1, 0))
    assertion("    Removing the linebreak")
    location = input_indexer.determine_diverges_from(multiline_haystack, multiline_remove_linebreak)
    assertion("        should give line 0, 62 characters from end upon inspection", location == (0, 62))


suite = create_test_suite("Caret position estimation based on new insertions, replacements or deletions")
suite.add_test(test_inserting_to_single_line)
suite.add_test(test_inserting_to_multiline)
suite.add_test(test_replacing_within_single_line)
suite.add_test(test_deleting_within_single_line)
suite.add_test(test_deleting_within_multiline)
suite.run()