from ...formatters.programming_detector import ProgrammingFormatterDetector
from ..test import create_test_suite

def test_lower_case_formatting(assertion):
    detector = ProgrammingFormatterDetector()

    assertion( "Test lower case formatting" )
    assertion( "    should mark 'test' as undetermined", detector.detect("test") == None)
    assertion( "    should mark '' as undetermined", detector.detect("") == None)
    assertion( "    should mark '1' as undetermined", detector.detect("1") == None)
    assertion( "    should mark '1?' as undetermined", detector.detect("1?") == None)
    assertion( "    should mark '.test.' as undetermined", detector.detect(".test.") == None)
    assertion( "    should mark 'test test' as undetermined", detector.detect("test test") == None)    
    assertion( "    should mark 'test-test' as kebab case", detector.detect("test-test") != None and detector.detect("test-test").name == "kebabcase")    
    assertion( "    should mark 'test_test' as snake case", detector.detect("test_test") != None and detector.detect("test_test").name == "snakecase")

def test_upper_case_formatting(assertion):
    detector = ProgrammingFormatterDetector()

    assertion( "Test upper case formatting" )
    assertion( "    should mark 'TEST' as all caps", detector.detect("TEST") != None and detector.detect("TEST").name == "all_caps")
    assertion( "    should mark 'TEST9' as all caps", detector.detect("TEST9") != None and detector.detect("TEST9").name == "all_caps")    
    assertion( "    should mark 'TEST_TEST' as constant", detector.detect("TEST_TEST") != None and detector.detect("TEST_TEST").name == "constant")    

def test_mixed_casing(assertion):
    detector = ProgrammingFormatterDetector()

    assertion( "Test mixed case formatting" )
    assertion( "    should mark 'testTest' as camel case", detector.detect("testTest") != None and detector.detect("testTest").name == "camelcase")
    assertion( "    should mark 'TestTest' as pascal case", detector.detect("TestTest") != None and detector.detect("TestTest").name == "pascalcase")
    assertion( "    should mark 'Test' as title case", detector.detect("Test") != None and detector.detect("Test").name == "title")

suite = create_test_suite("Programming formatter detection")
suite.add_test(test_lower_case_formatting)
suite.add_test(test_upper_case_formatting)
suite.add_test(test_mixed_casing)