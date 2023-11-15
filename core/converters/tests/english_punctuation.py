from ..english_punctuation import PunctuationConverter
from ...utils.test import create_test_suite

def test_english_punctuation_replacement(assertion):
    converter = PunctuationConverter()
    assertion( "One to one punctuation replacement")
    assertion( "    should replace point to '.'", converter.convert_words(["this", "is", "weird", "point"], "", "") == ["this", "is", "weird", "."])
    assertion( "    should replace period to .", converter.convert_words(["this", "should", "stop", "period"], "", "") == ["this","should","stop","."])
    assertion( "    should replace comma to ,", converter.convert_words(["I", "want", "to", "comma", "but"], "", "") == ["I", "want", "to", ",", "but"])
    assertion( "    should replace coma to ,", converter.convert_words(["I", "want", "to", "coma", "but"], "", "") == ["I", "want", "to", ",", "but"])
    assertion( "    should replace space to ' '", converter.convert_words(["air", "space", "bat"], "", "") == ["air", " ", "bat"])
    assertion( "    should replace question mark to '?'", converter.convert_words(["what", "are", "you", "doing", "question", "mark"], "", "") == ["what", "are", "you", "doing", "?"])
    assertion( "    should replace exclamation mark to '!'", converter.convert_words(["You're", "doing", "it", "wrong", "exclamation", "mark"], "", "") == ["You're", "doing", "it", "wrong", "!"])

def test_complex_english_punctuation_replacement(assertion):
    converter = PunctuationConverter()
    assertion( "Punctuation replacement")
    assertion( "    should not replace a point in time to 'a . in time'", converter.convert_words(["a", "point", "in", "time"], "", "") == ["a", "point", "in", "time"])
    assertion( "    should not replace a point in time to 'a . in time'", converter.convert_words(["point", "in", "time"], "a", "") == ["point", "in", "time"])
    assertion( "    should not replace a period in which to 'a . in which'", converter.convert_words(["a", "period", "in", "which"], "", "") == ["a", "period", "in", "which"])
    assertion( "    should not replace a period of to 'a period of'", converter.convert_words(["period"], "a", "of") == ["period"])
    assertion( "    should not replace I want some space to 'I want some  '", converter.convert_words(["want", "some", "space"], "I", "") == ["want", "some", "space"])

suite = create_test_suite("English punctuation")
suite.add_test(test_english_punctuation_replacement)
suite.add_test(test_complex_english_punctuation_replacement)