from ...virtual_buffer.indexer import VirtualBufferIndexer
from ..test import create_test_suite
from talon import settings

input_indexer = VirtualBufferIndexer()
input_indexer.detector.languages = ['EN', 'NL']

def test_index_python_code(assertion):
    sentence_tokens = input_indexer.index_text("    def change_place(test: str) -> False:")
    assertion( "Indexing the line '    def change_place(test: str) -> False:'...")
    assertion("    should consist of 9 virtual buffer tokens", len(sentence_tokens) == 9)
    assertion("    should considered the second two tokens to be snakecase", len([token.format for token in sentence_tokens[2:4] if token.format == "snakecase"]) == 2)

def test_index_ruby_code(assertion):
    sentence_tokens = input_indexer.index_text("    self.change_place(test:)")
    assertion( "Indexing the line '    self.change_place(test:)'...")
    assertion("    should consist of 5 virtual buffer tokens", len(sentence_tokens) == 5)
    assertion("    should considered the second two tokens to be snakecase", len([token.format for token in sentence_tokens[2:4] if token.format == "snakecase"]) == 2)

def test_index_java_code(assertion):
    sentence_tokens = input_indexer.index_text("    public static THIS_MACRO = 2;")
    assertion( sentence_tokens, False ) 
    assertion( "Indexing the words 'public static THIS_MACRO = 2;'...")
    assertion("    should consist of 7 virtual buffer tokens", len(sentence_tokens) == 7)
    assertion("    should considered the fourth two tokens to be constant", len([token.format for token in sentence_tokens[3:5] if token.format == "constant"]) == 2)

    sentence_tokens = input_indexer.index_text("public class VirtualBufferIndexer extends VirtualBufferIndexerInterface {")
    assertion( "Indexing the words 'public class VirtualBufferIndexer extends VirtualBufferIndexerInterface {")
    assertion("    should consist of 10 virtual buffer tokens", len(sentence_tokens) == 10)
    assertion("    should considered the third three tokens to be pascal case", len([token.format for token in sentence_tokens[2:5] if token.format == "pascalcase"]) == 3)
    assertion("    should considered the last four tokens to be pascal case", len([token.format for token in sentence_tokens[-4:] if token.format == "pascalcase"]) == 4)

def test_index_php_code(assertion):
    sentence_tokens = input_indexer.index_text("    public function sleep(float|int $seconds): void")
    assertion( "Indexing the line '    public function sleep(float|int $seconds): void'...")
    assertion("    should consist of 8 virtual buffer tokens", len(sentence_tokens) == 8)

def test_index_javascript_code(assertion):
    sentence_tokens = input_indexer.index_text("window.localStorage.getItem(\"talon-practice-challengemode\") == \"true\";")
    assertion( "Indexing the line 'window.localStorage.getItem(\"talon-practice-challengemode\") == \"true\";'...")
    assertion("    should consist of 9 virtual buffer tokens", len(sentence_tokens) == 9)
    assertion("    should considered the second four tokens to be camelcase", len([token.format for token in sentence_tokens[1:5] if token.format == "camelcase"]) == 4)
    assertion("    should considered the fifth three tokens to be kebabcase", len([token.format for token in sentence_tokens[5:8] if token.format == "kebabcase"]) == 3)

suite = create_test_suite("Automatic code formatter detection")
#suite.add_test(test_index_python_code)
suite.add_test(test_index_ruby_code)
#suite.add_test(test_index_java_code)
suite.add_test(test_index_php_code)
suite.add_test(test_index_javascript_code)
# TODO FIX INDEXING CHARACTERS -> not swallowing previous -
# TODO FIX MERGING ALL CAPS - CONSTANTS