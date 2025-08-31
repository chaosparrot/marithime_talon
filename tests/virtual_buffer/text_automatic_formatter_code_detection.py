from ...virtual_buffer.indexer import VirtualBufferIndexer
from ..test import create_test_suite

input_indexer = VirtualBufferIndexer()
input_indexer.detector.languages = ['EN', 'NL']

def test_index_python_code(assertion):
    sentence_tokens = input_indexer.index_text("    def change_place(test: str) -> False:")
    assertion( "Indexing the line '    def change_place(test: str) -> False:'...")
    assertion("    should consist of 6 virtual buffer tokens", len(sentence_tokens) == 6)
    assertion("    should considered the second two tokens to be snakecase", len([token.format for token in sentence_tokens[1:3] if token.format == "snakecase"]) == 2)

def test_index_java_code(assertion):
    sentence_tokens = input_indexer.index_text("    public static THIS_MACRO = 2;")
    assertion( "Indexing the words 'public static THIS_MACRO = 2;'...")
    assertion("    should consist of 5 virtual buffer tokens", len(sentence_tokens) == 6)
    assertion("    should considered the third two tokens to be constant", len([token.format for token in sentence_tokens[2:4] if token.format == "constant"]) == 2)

    sentence_tokens = input_indexer.index_text("public class VirtualBufferIndexer extends VirtualBufferIndexerInterface {")
    assertion( "Indexing the words 'public class VirtualBufferIndexer extends VirtualBufferIndexerInterface {")
    assertion("    should consist of 10 virtual buffer tokens", len(sentence_tokens) == 10)
    assertion("    should considered the third three tokens to be pascal case", len([token.format for token in sentence_tokens[2:5] if token.format == "pascalcase"]) == 3)
    assertion("    should considered the last four tokens to be pascal case", len([token.format for token in sentence_tokens[-4:] if token.format == "pascalcase"]) == 4)

def test_index_php_code(assertion):
    sentence_tokens = input_indexer.index_text("    public function sleep(float|int $seconds): void")
    assertion( "Indexing the line '    public function sleep(float|int $seconds): void'...")
    assertion("    should consist of 7 virtual buffer tokens", len(sentence_tokens) == 7)

def test_index_javascript_code(assertion):
    sentence_tokens = input_indexer.index_text("window.localStorage.getItem(\"talon-practice-challengemode\") == \"true\";")
    assertion( "Indexing the line 'window.localStorage.getItem(\"talon-practice-challengemode\") == \"true\";'...")
    assertion("    should consist of 9 virtual buffer tokens", len(sentence_tokens) == 9)

suite = create_test_suite("Automatic code formatter detection")
#suite.add_test(test_index_python_code)
#suite.add_test(test_index_java_code)
#suite.add_test(test_index_php_code)
#suite.add_test(test_index_javascript_code)
#suite.run()