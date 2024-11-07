from talon import cron
from typing import List, Callable, Module, settings
import time

mod = Module()
mod.setting("marithyme_testing", type=int, desc="Whether to run marithyme tests", default=0)

class TestSuite:
    intro_text: str
    tests: List[Callable[[str, bool], None]] = []
    assertions = []

    def assertion(self, text: str, assertion: bool = None):
        self.assertions.append([text, assertion])

    def verbose_assertion(self, text: str, assertion: bool = None):
        self.assertion(text, assertion)
        print( text, "" if assertion == None else assertion[1])

    def __init__(self, intro_text: str):
        self.intro_text = intro_text
        self.tests = []
        self.assertions = []

    def add_test(self, test: Callable[[str, bool], None]):
        self.tests.append(test)

    def run(self, verbosity: int = 1) -> List[bool]:
        self.assertions = []
        assertion_index = 0

        assertions_to_print = []
        for test in self.tests:
            if verbosity <= 1:
                test(self.assertion)
            else:
                test(self.verbose_assertion)

            for index in range(assertion_index, len(self.assertions)):
                if index < len(self.assertions) and self.assertions[index][1] == False:
                    assertions_to_print.extend(self.assertions[assertion_index:])
                    break
            assertion_index = len(self.assertions)
        
        results_string = ""
        for assertion in self.assertions:
            if assertion[1] == True:
                results_string += "✔"
            elif assertion[1] != True and assertion[1] is not None:
                results_string += "x"
        
        if verbosity > 0:
            print( "Test: " + self.intro_text + ": " + results_string)
        
        if verbosity == 1:
            for assertion in assertions_to_print:
                print( assertion[0], "" if assertion[1] == None else assertion[1] == True)
        
        #print( self.assertions )
        return [assertion[1] == True for assertion in self.assertions if assertion[1] is not None]

class TestSuiteCollection:
    name: str = ""
    test_suites: List[TestSuite] = None
    running_cron = None

    def __init__(self, name: str):
        self.name = name
        self.test_suites = []

    def add_test_suite(self, test_suite: TestSuite):
        found_index = -1
        for test_suite_index, known_suite in enumerate(self.test_suites):
            if known_suite.intro_text == test_suite.intro_text:
                found_index = test_suite_index
                break
        
        if found_index > -1:
            self.test_suites[found_index] = test_suite
        else:
            self.test_suites.append(test_suite)
        
        cron.cancel(self.running_cron)
        self.running_cron = cron.after("500ms", lambda: self.run(0))

    def run(self, verbosity = 0):
        # Only run tests if marithyme testing is turned on
        if settings.get("user.marithyme_testing") == 0:
            return
        start_time = time.perf_counter()
        total_results = []
        suite_results = []
        if verbosity > 0:
            print( "=============================================" )

        for test_suite in self.test_suites:
            try:
                results = test_suite.run(verbosity)
                suite_results.append([test_suite.intro_text, results])
                total_results.extend(results)
            except:
                print( "Test suite '" + test_suite.intro_text + "' crashes and could not run!" )
        print( "=============================================" )
        for suite_result in suite_results:
            if any(suite_result != True for suite_result in suite_result[1]):
                print( " - '" + suite_result[0] + "' contains " + str(len(suite_result[1]) - suite_result[1].count(True)) + " errors")
        
        print( "" + self.name + " " + str(len([result for result in total_results if result == True])) + "/" + str(len(total_results)) + " assertions succeeded")
        end_time = time.perf_counter()
        print( "" + str(round((end_time - start_time) * 1000) / 1000) + " seconds run time")
        print( "=============================================" )
        
        cron.cancel(self.running_cron)
        self.running_cron = None

test_suite_collection = TestSuiteCollection("Test cases")

def create_test_suite(intro_text: str) -> TestSuite:
    suite = TestSuite(intro_text)
    test_suite_collection.add_test_suite(suite)
    return suite

def run_tests():
    test_suite_collection.run(1)