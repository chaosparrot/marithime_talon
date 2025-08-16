from ...formatters.languages.dutch import dutchLanguage
from ...formatters.languages.english import englishLanguage
from ..test import create_test_suite

def test_dutch_detector(assertion):
    detector = dutchLanguage

    assertion( "Test dutch detector" )
    assertion( "    should mark 'test' as undetermined", detector.detect_likeliness("test") <= 0)
    assertion( "    should mark '' as undetermined", detector.detect_likeliness("") <= 0.0)
    assertion( "    should mark '1' as undetermined", detector.detect_likeliness("1") <= 0.0)
    assertion( "    should mark '1?' as undetermined", detector.detect_likeliness("1?") <= 0.0)
    assertion( "    should mark '.test.' as undetermined", detector.detect_likeliness(".test.") <= 0.0)
    assertion( "    should mark 'Dit is een probleem' as likely dutch", detector.detect_likeliness("Dit is een probleem.") > 0.0)
    assertion( "    should mark 'Kan ik hier nog iets mee' as likely dutch", detector.detect_likeliness("Kan ik hier nog iets mee?") > 0.0)
    assertion( "    should mark 'Het museum is vaak vol' as likely dutch", detector.detect_likeliness("Het museum is vaak vol") > 0.0)
    assertion( "    should mark 'Maar dat hoeft niet zo te zijn' as likely dutch", detector.detect_likeliness("Maar dat hoeft niet zo te zijn") > 0.0)    

def test_english_detector(assertion):
    detector = englishLanguage

    assertion( "Test english detector" )
    assertion( "    should mark 'test' as undetermined", detector.detect_likeliness("test") <= 0)
    assertion( "    should mark '' as undetermined", detector.detect_likeliness("") <= 0.0)
    assertion( "    should mark '1' as undetermined", detector.detect_likeliness("1") <= 0.0)
    assertion( "    should mark '1?' as undetermined", detector.detect_likeliness("1?") <= 0.0)
    assertion( "    should mark '.test.' as undetermined", detector.detect_likeliness(".test.") <= 0.0)
    assertion( "    should mark 'This is a problem' as likely english", detector.detect_likeliness("This is a problem.") > 0.0)
    assertion( "    should mark 'Can I even do something with this' as likely english", detector.detect_likeliness("Can I even do something with this?") > 0.0)
    assertion( "    should mark 'Often the museum is full' as likely english", detector.detect_likeliness("Often the museum is full") > 0.0)
    assertion( "    should mark 'But it doesn't have to be' as likely english", detector.detect_likeliness("But it doesn't have to be") > 0.0)    

suite = create_test_suite("Language detector")
suite.add_test(test_dutch_detector)
suite.add_test(test_english_detector)