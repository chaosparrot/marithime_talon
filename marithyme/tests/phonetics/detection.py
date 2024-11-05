from ...phonetics.detection import detect_phonetic_fix_type
from ..test import create_test_suite

def test_homophone_detection(assertion):
    assertion("Homophone detection")
    assertion("    should not match if we change apples with oranges", detect_phonetic_fix_type("apples", "oranges") != "homophone")
    assertion("    should not match if we replace apple with apply", detect_phonetic_fix_type("apple", "apply") != "homophone")
    assertion("    should not match if we replace add with at", detect_phonetic_fix_type("add", "at") != "homophone")
    assertion("    should not match if we replace bear with pear", detect_phonetic_fix_type("bear", "pear") != "homophone")
    assertion("    should not match if we replace chase with pace", detect_phonetic_fix_type("chase", "pace") != "homophone")
    assertion("    should not match if we replace trash with trace", detect_phonetic_fix_type("thrash", "trace") != "homophone")
    assertion("    should match if we replace add with ad", detect_phonetic_fix_type("add", "ad") == "homophone")

def test_phonetic_similarity_detection(assertion):
    assertion("Phonetic similarity detection")
    assertion("    should not match if we change apples with oranges", detect_phonetic_fix_type("apples", "oranges") != "phonetic")
    assertion("    should match if we replace apple with apply", detect_phonetic_fix_type("apple", "apply") == "phonetic")
    assertion("    should match if we replace add with at", detect_phonetic_fix_type("add", "at") == "phonetic")
    assertion("    should match if we replace bear with pear", detect_phonetic_fix_type("bear", "pear") == "phonetic")
    assertion("    should match if we replace chase with pace", detect_phonetic_fix_type("chase", "pace") == "phonetic")
    assertion("    should match if we replace that's with that", detect_phonetic_fix_type("that's", "that") == "phonetic")

suite = create_test_suite("Phonetic detection")
suite.add_test(test_homophone_detection)
suite.add_test(test_phonetic_similarity_detection)