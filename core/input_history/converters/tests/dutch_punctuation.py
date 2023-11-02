from ..dutch_punctuation import PunctuationConverter
from ....utils.test import create_test_suite

def test_dutch_punctuation_replacement(assertion):
    converter = PunctuationConverter()
    assertion( "One to one dutch punctuation replacement")
    assertion( "    should replace punt to .", converter.convert_words(["dit", "kan", "wel", "punt"], "", "") == ["dit","kan","wel","."])
    assertion( "    should replace komma to ,", converter.convert_words(["ik", "wil", "komma", "heel", "soms"], "", "") == ["ik", "wil", ",", "heel", "soms"])
    assertion( "    should replace koma to ,", converter.convert_words(["ik", "wil", "koma", "heel", "soms"], "", "") == ["ik", "wil", ",", "heel", "soms"])
    assertion( "    should replace spatie to ' '", converter.convert_words(["welke", "spatie", "is"], "", "") == ["welke", " ", "is"])
    assertion( "    should replace vraag teken to '?'", converter.convert_words(["wat", "doe", "je", "nou", "vraag", "teken"], "", "") == ["wat", "doe", "je", "nou", "?"])
    assertion( "    should replace vraagteken to '?'", converter.convert_words(["wat", "doe", "je", "nou", "vraagteken"], "", "") == ["wat", "doe", "je", "nou", "?"])
    assertion( "    should replace uitroep teken to '!'", converter.convert_words(["doe", "nou", "niet", "uitroep", "teken"], "", "") == ["doe", "nou", "niet", "!"])
    assertion( "    should replace uitroepteken to '!'", converter.convert_words(["doe", "nou", "niet", "uitroepteken"], "", "") == ["doe", "nou", "niet", "!"])    

def test_complex_dutch_punctuation_replacement(assertion):
    converter = PunctuationConverter()
    assertion( "Dutch punctuation replacement")
    assertion( "    should not replace 'een punt die' to 'een . die'", converter.convert_words(["een", "punt", "die"], "", "") == ["een", "punt", "die"])
    assertion( "    should not replace 'het punt van aandacht' to '. van aandacht'", converter.convert_words(["punt", "van", "aandacht"], "het", "") == ["punt", "van", "aandacht"])
    assertion( "    should not replace 'een komma teken' to 'een , teken'", converter.convert_words(["een", "komma", "teken"], "", "") == ["een", "komma", "teken"])

suite = create_test_suite("Dutch punctuation")
suite.add_test(test_dutch_punctuation_replacement)
suite.add_test(test_complex_dutch_punctuation_replacement)