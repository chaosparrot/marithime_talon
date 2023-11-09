from ..input_indexer import InputIndexer
from ...utils.test import create_test_suite

def test_inserting_to_single_line(assertion):
    input_indexer = InputIndexer()
    assertion("Adding the text 'test' to 'This is a '")
    location = input_indexer.determine_diverges_from('This is a ', 'This is a test', 'test')
    assertion("    should give line 0, 0 characters from end upon inspection", location == (0, 0))
    assertion("Adding the text 'already' in between 'This is a '")
    location = input_indexer.determine_diverges_from('This is a ', 'This is already a ', 'already')
    assertion("    should give line 0, 2 characters from end upon inspection", location == (0, 2))
    assertion("Adding the text 'But' before ' this is a '")
    location = input_indexer.determine_diverges_from('this is a ', 'But this is a ', 'But')
    assertion("    should give line 0, 10 characters from end upon inspection", location == (0, 10))
    assertion("Adding the text 'n't' within ' this is a '")
    location = input_indexer.determine_diverges_from('This is a ', "This isn't a ", "n't")
    assertion("    should give line 0, 3 characters from end upon inspection", location == (0, 3))
    assertion("Adding a new line after 'This is a test.'")
    location = input_indexer.determine_diverges_from('This is a test.', """This is a test.
""", """
""")
    assertion("    should give line 1, 0 characters from end upon inspection", location == (1, 0))

def test_replacing_within_single_line(assertion):
    input_indexer = InputIndexer()
    assertion("Replacing the word 'a' with 'the' in 'This is a test'")
    location = input_indexer.determine_diverges_from('This is a test', 'This is the test', "the")
    assertion("    should give line 0, 5 characters from end upon inspection", location == (0, 5))
    assertion("Replacing the word 'This' with 'That' in 'This is a test'", "That")
    location = input_indexer.determine_diverges_from('This is a test', 'That is a test')
    assertion("    should give line 0, 10 characters from end upon inspection", location == (0, 10))
    assertion("Replacing the word 'test.' with 'sentence.<newline>' in  'This is a test.'", """sentence.
""")
    location = input_indexer.determine_diverges_from('This is a test.', """This is a sentence.
""")
    assertion("    should give line 1, 0 characters from end upon inspection", location == (1, 0))

def test_deleting_within_single_line(assertion):
    input_indexer = InputIndexer()
    assertion("Removing the word 'This' from 'This is a test'")
    location = input_indexer.determine_diverges_from('This is a test', 'is a test')
    assertion("    should give line 0, 9 characters from end upon inspection", location == (0, 9))
    assertion("Removing the word 'a ' from 'This is a test'")
    location = input_indexer.determine_diverges_from('This is a test', 'This is test')
    assertion( location )
    assertion("    should give line 0, 4 characters from end upon inspection", location == (0, 4))
    assertion("Removing the word 'test' from 'This is a test'")
    location = input_indexer.determine_diverges_from('This is a test', "This is a")
    assertion("    should give line 0, 0 characters from end upon inspection", location == (0, 0))
    assertion("Removing the words 'is a test' from 'This is a test'")
    location = input_indexer.determine_diverges_from('This is a test', "This ")
    assertion("    should give line 0, 0 characters from end upon inspection", location == (0, 0))

suite = create_test_suite("Caret position estimation based on new insertions, replacements or deletions")
#suite.add_test(test_inserting_to_single_line)
#suite.add_test(test_replacing_within_single_line)
suite.add_test(test_deleting_within_single_line)
suite.run()