from ..detection import syllable_count
from ...utils.test import create_test_suite

def test_single_syllables(assertion):
    assertion("Single syllable detection")
    words = ["test", "bird", "tray", "hay", "though", "foe", "go", "air", "bear", "cat", "chat", "drag", "you", "hue", "eye"]

    for word in words:
        assertion("    should find one syllable for " + word, syllable_count(word) == 1)

def test_double_syllables(assertion):
    assertion("Double syllable detection")
    words = ["hammer", "table", "astray", "granted", "struggled", "notes", "breaking", "youthfull", "gaudy", "paintbrush"]

    for word in words:
        assertion("    should find two syllables for " + word, syllable_count(word) == 2)

def test_triple_syllables(assertion):
    assertion("Triple syllable detection")
    words = ["hammering", "racketeer", "unhelpfull", "disregard", "anthropic", "failures", "violence", "playfully"]

    for word in words:
        assertion("    should find three syllables for " + word, syllable_count(word) == 3)


suite = create_test_suite("Syllable count")
suite.add_test(test_single_syllables)
suite.add_test(test_double_syllables)
suite.add_test(test_triple_syllables)