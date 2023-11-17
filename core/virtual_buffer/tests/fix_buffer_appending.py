from ..input_fixer import InputFixer
from ...phonetics.phonetics import PhoneticSearch
from ...utils.test import create_test_suite
import time

def get_input_fixer() -> InputFixer:
    input_fixer = InputFixer("en", "test", None)
    search = PhoneticSearch()
    search.set_homophones("")
    search.set_phonetic_similiarities("")
    input_fixer.phonetic_search = search
    return input_fixer

def test_insertions_only(assertion):
    input_fixer = get_input_fixer()

    assertion( "Inserting text from an empty buffer")
    assertion( "    Inserting 'This '")
    input_fixer.add_to_buffer("This ")    
    assertion( "        Should increase the buffer by 1", len(input_fixer.buffer) == 1)
    assertion( "    Inserting 'is '")
    input_fixer.add_to_buffer("is ")    
    assertion( "        Should increase the buffer by 1 again", len(input_fixer.buffer) == 2)
    assertion( "    Inserting 'a test '")
    input_fixer.add_to_buffer("a test ")
    assertion( "        Should increase the buffer by 1 again", len(input_fixer.buffer) == 3)

def test_substitution_only(assertion):
    input_fixer = get_input_fixer()

    assertion( "Replacing text from an empty buffer")
    assertion( "    Replacing 'This ' with 'That '")
    input_fixer.add_to_buffer("This ", "That ")    
    assertion( "        Should increase the buffer by 1", len(input_fixer.buffer) == 1)
    assertion( "    Replacing 'is ' with 'is '")
    input_fixer.add_to_buffer("is ", "is ")    
    assertion( "        Should increase the buffer by 1 again", len(input_fixer.buffer) == 2)
    assertion( "    Replacing 'a test ' with 'a text '")
    input_fixer.add_to_buffer("a test ", "a text ")
    assertion( "        Should increase the buffer by 1 again", len(input_fixer.buffer) == 3)

def test_consecutive_separate_substitution(assertion):
    input_fixer = get_input_fixer()

    assertion( "Inserting text from an empty buffer")
    assertion( "    Inserting 'affix '")
    input_fixer.add_to_buffer("affix ")    
    assertion( "        Should increase the buffer by 1", len(input_fixer.buffer) == 1)
    assertion( "    Removing 'affix '")
    input_fixer.add_to_buffer("", "affix ")
    assertion( "        Should increase the buffer by 1", len(input_fixer.buffer) == 2)
    assertion( "    Inserting 'a fix '")
    input_fixer.add_to_buffer("a fix ")
    assertion( "        Should merge the buffer into one single item", len(input_fixer.buffer) == 1)

def test_consecutive_separate_substitution(assertion):
    input_fixer = get_input_fixer()

    assertion( "Inserting text from an empty buffer")
    assertion( "    Inserting 'affix '")
    input_fixer.add_to_buffer("affix ")    
    assertion( "        Should increase the buffer by 1", len(input_fixer.buffer) == 1)
    assertion( "    Removing 'affix '")
    input_fixer.add_to_buffer("", "affix ")
    assertion( "        Should increase the buffer by 1", len(input_fixer.buffer) == 2)
    assertion( "    Inserting 'a fix '")
    input_fixer.add_to_buffer("a fix ")
    assertion( "        Should merge the buffer into one single item", len(input_fixer.buffer) == 1)
    assertion( "        The buffer change should be 'affix ' to 'a fix '", input_fixer.buffer[0].insertion == 'a fix ' and input_fixer.buffer[0].deletion == 'affix ')

def test_consecutive_fixes_on_same_word(assertion):
    input_fixer = get_input_fixer()
    input_fixer.add_to_buffer("affix ")    
    input_fixer.add_to_buffer("", "affix ")
    input_fixer.add_to_buffer("a fix ")

    assertion( "Appending to a buffer with a word already marked as substituted")
    assertion( "    Replacing 'a fix ' with 'aphix '")
    input_fixer.add_to_buffer("aphix ", "a fix ")
    assertion( "        Should merge the buffer into one single item again", len(input_fixer.buffer) == 1)
    assertion( "        The buffer change should be 'affix ' to 'aphix '", input_fixer.buffer[0].insertion == 'aphix ' and input_fixer.buffer[0].deletion == 'affix ')    

def test_consecutive_fixes_on_same_word_separately(assertion):
    input_fixer = get_input_fixer()
    input_fixer.add_to_buffer("affix ")
    input_fixer.add_to_buffer("", "affix ")
    input_fixer.add_to_buffer("a fix ")

    assertion( "Appending to a buffer with a word already marked as substituted")
    assertion( "    Removing 'a fix '")
    input_fixer.add_to_buffer("", "a fix ")
    assertion( "        Should increase the buffer by 1", len(input_fixer.buffer) == 2)
    assertion( "    Inserting 'aphix ' after the removal")
    input_fixer.add_to_buffer("aphix ")
    assertion( "        Should merge the buffer into one single item again", len(input_fixer.buffer) == 1)
    assertion( "        The buffer change should be 'affix ' to 'aphix '", input_fixer.buffer[0].insertion == 'aphix ' and input_fixer.buffer[0].deletion == 'affix ')

suite = create_test_suite("Tracking buffer entries from insertions, substitutions and deletions")
suite.add_test(test_insertions_only)
suite.add_test(test_substitution_only)
suite.add_test(test_consecutive_separate_substitution)
suite.add_test(test_consecutive_fixes_on_same_word)
suite.add_test(test_consecutive_fixes_on_same_word_separately)