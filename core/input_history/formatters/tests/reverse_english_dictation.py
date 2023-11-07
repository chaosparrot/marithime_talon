from ..dictation_formatter import DICTATION_FORMATTERS
from ....utils.test import create_test_suite

def test_english_dictation(assertion):
    formatter = DICTATION_FORMATTERS['EN']
    assertion( "    'This is a sentence', should return a list of lowercase words", formatter.format_to_words('This is a sentence') == ['this', 'is', 'a', 'sentence'])
    assertion( "    'Is this a sentence', should return a list of lowercase words", formatter.format_to_words('Is this a sentence') == ['is', 'this', 'a', 'sentence'])
    assertion( "    '. This is a sentence', should return a list of lowercase words and punctuation", formatter.format_to_words('. This is a sentence') == ['.', 'this', 'is', 'a', 'sentence'])
    assertion( "    'This is a sentence! ', should return a list of lowercase words and punctuation", formatter.format_to_words('This is a sentence!') == ['this', 'is', 'a', 'sentence', '!'])
    assertion( "    'This is a sentence, but this isn't', should return a list of lowercase words and punctuation", formatter.format_to_words('This is a sentence, but this isn\'t') == ['this', 'is', 'a', 'sentence', ',', 'but', 'this', 'isn\'t'])
    assertion( formatter.format_to_words('This is a sentence!') )

suite = create_test_suite("Reverse english dictation dictation")
suite.add_test(test_english_dictation)