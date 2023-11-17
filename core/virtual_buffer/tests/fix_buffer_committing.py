from ..input_fixer import InputFixer
from ...phonetics.phonetics import PhoneticSearch
from ...utils.test import create_test_suite
import time

def get_input_fixer() -> InputFixer:
    input_fixer = InputFixer("en", "test", None, 0)
    search = PhoneticSearch()
    search.set_homophones("")
    search.set_phonetic_similiarities("")
    input_fixer.phonetic_search = search
    return input_fixer

def test_track_insertions_only(assertion):
    input_fixer = get_input_fixer()
    input_fixer.add_to_buffer("This ")
    input_fixer.add_to_buffer("is ")
    input_fixer.add_to_buffer("a ")
    input_fixer.add_to_buffer("test.")
    detected_fixes = input_fixer.commit_buffer(time.time())

    assertion( "Inserting text only")
    assertion( "    Should give us an empty buffer after we commit it to changes", len(input_fixer.buffer) == 0)
    assertion( "    Should not track any fixes because nothing has been replaced", len(detected_fixes) == 0)

def test_track_deletions_only(assertion):
    input_fixer = get_input_fixer()
    input_fixer.add_to_buffer(deletion="This ")
    input_fixer.add_to_buffer(deletion="is ")
    input_fixer.add_to_buffer(deletion="a ")
    input_fixer.add_to_buffer(deletion="test.")
    detected_fixes = input_fixer.commit_buffer(time.time())

    assertion( "Deleting text only")
    assertion( "    Should give us an empty buffer after we commit it to changes", len(input_fixer.buffer) == 0)
    assertion( "    Should not track any fixes because nothing has been replaced", len(detected_fixes) == 0)

def test_substitution(assertion):
    input_fixer = get_input_fixer()
    input_fixer.add_to_buffer(insertion="This is a fix ", deletion="This is affix ")
    detected_fixes = input_fixer.commit_buffer(time.time())

    assertion( "Substituting text")
    assertion( "    Should give us an empty buffer after we commit it to changes", len(input_fixer.buffer) == 0)
    assertion( "    Should track a single fix because 'affix' has been replaced with 'a fix'", len(detected_fixes) > 0)
    assertion( "    Should have the 'affix' to 'a fix' change detected", len([fix for fix in detected_fixes if fix.key == "affix-->a fix"]) > 0)

def test_substitution_deletion(assertion):
    input_fixer = get_input_fixer()
    input_fixer.add_to_buffer(insertion="This is a fix ", deletion="This is affix ")
    input_fixer.add_to_buffer(deletion="This is a fix ")
    detected_fixes = input_fixer.commit_buffer(time.time())

    assertion( "Deleting text after substitution")
    assertion( "    Should give us an empty buffer after we commit it to changes", len(input_fixer.buffer) == 0)
    assertion( "    Should not track any fixes because the previous substitution has been removed", len(detected_fixes) == 0)

suite = create_test_suite("Tracking fixes from text insertions, substitutions and deletions")
suite.add_test(test_track_insertions_only)
suite.add_test(test_track_deletions_only)
suite.add_test(test_substitution)
suite.add_test(test_substitution_deletion)