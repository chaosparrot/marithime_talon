from ...virtual_buffer.input_fixer import InputFixer
from ..test import create_test_suite
from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ...virtual_buffer.settings import VirtualBufferSettings
from ...phonetics.phonetics import PhoneticSearch

def get_phonetic_search() -> PhoneticSearch:
    phonetic_search = PhoneticSearch()
    phonetic_search.set_homophones("""to,too,two
where,wear,ware""")
    phonetic_search.set_phonetic_similiarities("")
    phonetic_search.set_semantic_similarities("")
    return phonetic_search

def get_virtual_buffer() -> VirtualBuffer:
    settings = VirtualBufferSettings(live_checking=False)
    return VirtualBuffer(settings)

def get_filled_vb():
    vb = get_virtual_buffer()

    # Reset the phonetic search to make sure there is no influence from user settings
    vb.matcher.phonetic_search = get_phonetic_search()

    vb.insert_tokens(text_to_virtual_buffer_tokens("I ", "i"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("want ", "want"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("to ", "to"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("know ", "know"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("wear ", "wear"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("the ", "the"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("eyes ", "eyes"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("are ", "are"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("too", "too"))

    return vb

def get_input_fixer():
    fixer = InputFixer("en", "test", None, 0, testing=True)
    fixer.phonetic_search = get_phonetic_search()
    return fixer

def test_detect_no_fixes(assertion):
    input_fixer = get_input_fixer()
    vb = get_filled_vb()

    assertion( "Using an empty input fixer")
    buffer_tokens = []
    buffer_tokens.extend(text_to_virtual_buffer_tokens(" because", "because"))
    assertion( "    Inserting 'because'...")
    phonetic_fixes = input_fixer.determine_phonetic_fixes(vb, buffer_tokens)
    assertion( "        Should not find a fix to cycle through", len(phonetic_fixes) == 0)
    buffer_tokens.extend(text_to_virtual_buffer_tokens(" the", "the"))
    buffer_tokens.extend(text_to_virtual_buffer_tokens(" coldest", "coldest"))    
    assertion( "    Inserting 'because the coldest'...")
    phonetic_fixes = input_fixer.determine_phonetic_fixes(vb, buffer_tokens)
    assertion( "        Should not find a fix to cycle through", len(phonetic_fixes) == 0)

def test_detect_single_word_fixes(assertion):
    input_fixer = get_input_fixer()
    vb = get_filled_vb()

    assertion( "Using an empty input fixer")
    buffer_tokens = []
    buffer_tokens.extend(text_to_virtual_buffer_tokens(" to", "to"))
    assertion( "    Inserting 'to'...")
    phonetic_fixes = input_fixer.determine_phonetic_fixes(vb, buffer_tokens)
    assertion( "        Should determine that we have found a phonetic fix", len(phonetic_fixes) == 1)
    
    buffer_tokens.extend(text_to_virtual_buffer_tokens(" me", "me"))
    assertion( "    Inserting 'to me'...")
    phonetic_fixes = input_fixer.determine_phonetic_fixes(vb, buffer_tokens)
    assertion( "        Should determine that we have found a phonetic fix", len(phonetic_fixes) == 2)

    buffer_tokens = []
    buffer_tokens.extend(text_to_virtual_buffer_tokens(" me", "me"))
    buffer_tokens.extend(text_to_virtual_buffer_tokens(" two", "two"))
    assertion( "    Inserting 'me two'...")
    phonetic_fixes = input_fixer.determine_phonetic_fixes(vb, buffer_tokens)
    assertion( "        Should determine that we have found a phonetic fix", len(phonetic_fixes) == 2)

def test_detect_multiple_word_fixes(assertion):
    input_fixer = get_input_fixer()
    vb = get_filled_vb()

    assertion( "Using an empty input fixer")
    buffer_tokens = []
    buffer_tokens.extend(text_to_virtual_buffer_tokens(" to", "to"))
    buffer_tokens.extend(text_to_virtual_buffer_tokens(" where", "where"))
    assertion( "    Inserting 'to where'...")
    phonetic_fixes = input_fixer.determine_phonetic_fixes(vb, buffer_tokens)
    assertion( "        Should determine that we have found a phonetic fix", len(phonetic_fixes) == 2)
    
    buffer_tokens.extend(text_to_virtual_buffer_tokens(" the", "the"))
    assertion( "    Inserting 'to where the'...")
    phonetic_fixes = input_fixer.determine_phonetic_fixes(vb, buffer_tokens)
    assertion( "        Should determine that we have found a phonetic fix", len(phonetic_fixes) == 3)

    buffer_tokens.extend(text_to_virtual_buffer_tokens(" two", "two"))
    assertion( "    Inserting 'to where the two'...")
    phonetic_fixes = input_fixer.determine_phonetic_fixes(vb, buffer_tokens)
    assertion( "        Should determine that we have found a phonetic fix", len(phonetic_fixes) == 4)    

def test_determine_no_fixes(assertion):
    input_fixer = get_input_fixer()

    assertion( "Using an empty input fixer")
    assertion( "    Checking 'because'...")
    cycle_fixes = input_fixer.determine_cycles_for_words(["because"])
    assertion( "        Should find all the text inserted", len(cycle_fixes) == 1)
    assertion( "        Should not find a fix to cycle through", cycle_fixes[0][1] == 0)
    assertion( "    Checking 'because the'...")
    cycle_fixes = input_fixer.determine_cycles_for_words(["because", "the"])
    assertion( "        Should find all the text inserted", len(cycle_fixes) == 2)
    assertion( "        Should not find a fix to cycle through", (cycle_fixes[0][1] + cycle_fixes[1][1]) == 0)

def test_determine_single_word_fixes(assertion):
    input_fixer = get_input_fixer()
    vb = get_filled_vb()

    assertion( "Using an empty input fixer")
    assertion( "    Checking 'to'...")
    cycle_fixes = input_fixer.determine_cycles_for_words(["to"])
    assertion( "        Should find all the text inserted", len(cycle_fixes) == 1)
    assertion( "        Should find two fixes to cycle through", cycle_fixes[0][1] == 2)
    assertion( "    Checking 'to the'...")
    cycle_fixes = input_fixer.determine_cycles_for_words(["to", "the"])
    assertion( "        Should find all the text inserted", len(cycle_fixes) == 2)
    assertion( "        Should find two fixes to cycle through for the first word", cycle_fixes[0][1] == 2)
    assertion( "        Should not find more fixes to cycle thorugh for the second word", cycle_fixes[1][1] == 0)

def test_determine_multiple_word_fixes(assertion):
    input_fixer = get_input_fixer()

    assertion( "Using an empty input fixer")
    assertion( "    Checking 'to where'...")
    cycle_fixes = input_fixer.determine_cycles_for_words(["to", "where"])
    assertion( "        Should find all the text inserted", len(cycle_fixes) == 2)
    assertion( "        Should find two fixes to cycle through for the first word", cycle_fixes[0][1] == 2)
    assertion( "        Should find two fixes to cycle through for the second word", cycle_fixes[1][1] == 2)    
    assertion( "    Checking 'to that where'...")
    cycle_fixes = input_fixer.determine_cycles_for_words(["to", "that", "where"])
    assertion( "        Should find all the text inserted", len(cycle_fixes) == 3)
    assertion( "        Should find two fixes to cycle through for the first word", cycle_fixes[0][1] == 2)
    assertion( "        Should find no fixes to cycle through for the second word", cycle_fixes[1][1] == 0)    
    assertion( "        Should find two fixes to cycle through for the third word", cycle_fixes[2][1] == 2)

suite = create_test_suite("Finding phonetic fixes to cycle through")
suite.add_test(test_detect_no_fixes)
suite.add_test(test_detect_single_word_fixes)
suite.add_test(test_detect_multiple_word_fixes)
suite.add_test(test_determine_no_fixes)
suite.add_test(test_determine_single_word_fixes)
suite.add_test(test_determine_multiple_word_fixes)