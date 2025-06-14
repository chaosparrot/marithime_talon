from ...virtual_buffer.indexer import VirtualBufferIndexer
from ...virtual_buffer.caret_tracker import _CARET_MARKER
from ..test import create_test_suite

def test_exact_same_content(assertion):
    input_indexer = VirtualBufferIndexer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"    
    tokens = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "This is a test.")
    assertion("Comparing the sentence 'This is a test.' with 'This is a test.'")
    assertion("    Should not result in more tokens than those that we started with", len(tokens) == len(starting_tokens))
    assertion("    Should not result in a reindexation and clearing of the format of the tokens", tokens[0].format == "testingformat")

def test_simple_appending(assertion):
    input_indexer = VirtualBufferIndexer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    tokens = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "This is a test. To make new")
    assertion("Comparing the sentence 'This is a test.' with 'This is a test. To make new'")
    assertion("    Should result in more tokens than those that we started with", len(tokens) > len(starting_tokens))
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should result in a reindexation", tokens[0].index_from_line_end != starting_tokens[0].index_from_line_end)
    assertion("    Should have the text ' To make new' at the end of the newly added tokens", "".join([token.text for token in tokens]).endswith(" To make new"))

def test_simple_prepending(assertion):
    input_indexer = VirtualBufferIndexer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"    
    tokens = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "To test previous tokens. This is a test.")
    assertion("Comparing the sentence 'This is a test.' with 'To test previous tokens. This is a test.'")
    assertion("    Should result in more tokens than those that we started with", len(tokens) > len(starting_tokens))
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[-1].format == "testingformat")
    assertion("    Should result in a reindexation", tokens[0].index_from_line_end != starting_tokens[0].index_from_line_end)
    assertion("    Should have the text 'To test previous tokens.' at the start of the newly added tokens", "".join([token.text for token in tokens]).startswith("To test previous tokens."))

def test_simple_insertion_in_the_middle(assertion):
    input_indexer = VirtualBufferIndexer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    starting_tokens_length = len(starting_tokens)
    tokens = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "This is a wonderful " + _CARET_MARKER + "test.")
    assertion("Comparing the sentence 'This is a test.' with 'This is a wonderful test.'")
    assertion("    Should result in more tokens than those that we started with", len(tokens) > starting_tokens_length)
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat" and tokens[-1].format == "testingformat")
    assertion("    Should have the text 'wonderful' in the newly added tokens", "wonderful " in "".join([token.text for token in tokens]))

def test_simple_removal_at_end(assertion):
    input_indexer = VirtualBufferIndexer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    starting_tokens_length = len(starting_tokens)
    tokens = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "This is ")
    assertion("Comparing the sentence 'This is a test.' with 'This is '")
    assertion("    Should result in less tokens than those that we started with", len(tokens) < starting_tokens_length)
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should result in a reindexation", tokens[0].index_from_line_end != starting_tokens[0].index_from_line_end)
    assertion("    Should not have the text 'a test.' in the newly added tokens", "a test." not in "".join([token.text for token in tokens]))

def test_simple_removal_at_start(assertion):
    input_indexer = VirtualBufferIndexer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    starting_tokens_length = len(starting_tokens)
    tokens = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "a test.")
    assertion("Comparing the sentence 'This is a test.' with 'a test.'")
    assertion("    Should result in less tokens than those that we started with", len(tokens) < starting_tokens_length)
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[-1].format == "testingformat")
    assertion("    Should not have the text 'This is' in the newly added tokens", "This is" not in "".join([token.text for token in tokens]))

def test_simple_removal_in_the_middle(assertion):
    input_indexer = VirtualBufferIndexer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    starting_tokens_length = len(starting_tokens)
    tokens = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "This is " + _CARET_MARKER + "test.")
    assertion("Comparing the sentence 'This is a test.' with 'This is test.'")
    assertion("    Should result in less tokens than those that we started with", len(tokens) < starting_tokens_length)
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat" and tokens[-1].format == "testingformat")
    assertion("    Should not have the text 'a' in the newly added tokens", "a " not in "".join([token.text for token in tokens]))


suite = create_test_suite("Partial indexation with simple cases of appending, removing and keeping the same")
suite.add_test(test_exact_same_content)
suite.add_test(test_simple_appending)
suite.add_test(test_simple_prepending)
suite.add_test(test_simple_insertion_in_the_middle)
suite.add_test(test_simple_removal_at_end)
suite.add_test(test_simple_removal_at_start)
suite.add_test(test_simple_removal_in_the_middle)