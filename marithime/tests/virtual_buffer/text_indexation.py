from ...virtual_buffer.indexer import VirtualBufferIndexer
from ..test import create_test_suite

input_indexer = VirtualBufferIndexer()

def test_index_single_sentence(assertion):
    sentence_tokens = input_indexer.index_text("This is a test.")
    assertion( "Indexing the sentence 'This is a test.'...")
    assertion("    should consist of 4 virtual buffer tokens", len(sentence_tokens) == 4)
    assertion("    should only be on one line", len([token for token in sentence_tokens if token.line_index == 0]) == len(sentence_tokens))
    assertion("    The first token should be 'This '", sentence_tokens[0].text == 'This ')
    assertion("    The first token should be be 10 characters from the end on 'This is a test.'", sentence_tokens[0].index_from_line_end == 10)
    assertion("    The second token should be 'is '", sentence_tokens[1].text == 'is ')
    assertion("    The second token should be be 7 characters from the end on 'This is a test.'", sentence_tokens[1].index_from_line_end == 7)
    assertion("    The third token should be 'a '", sentence_tokens[2].text == 'a ')
    assertion("    The third token should be be 5 characters from the end on 'This is a test.'", sentence_tokens[2].index_from_line_end == 5)
    assertion("    The last token should be 'test.'", sentence_tokens[3].text == 'test.')
    assertion("    The last token should be be 0 characters from the end on 'This is a test.'", sentence_tokens[3].index_from_line_end == 0)

def test_index_multiple_sentences(assertion):
    sentence_tokens = input_indexer.index_text("""This is the first sentence.
And this is a second sentence!""")
    assertion( "Indexing the sentence 'This is the first sentence.' followed by 'And this is a second sentence!'...")
    assertion("    should consist of 11 virtual buffer tokens", len(sentence_tokens) == 11)
    assertion("    should have 4 tokens on the first line", len([token for token in sentence_tokens if token.line_index == 0]) == 5)
    assertion("    should have 7 tokens on the second line", len([token for token in sentence_tokens if token.line_index == 1]) == 6)
    assertion("    the first word of the second line should be capitalized", [token for token in sentence_tokens if token.line_index == 1][0].text == "And ")    

def test_index_sentence_with_unorthodox_spacing(assertion):
    sentence_tokens = input_indexer.index_text("this  is  the  first  sentence  . ")
    assertion( "Indexing the sentence 'this  is  the  first  sentence  . '")
    assertion("    should consist of 5 virtual buffer tokens", len(sentence_tokens) == 5)
    assertion("    should have 5 tokens on the first line", len([token for token in sentence_tokens if token.line_index == 0]) == 5)
    assertion("    the first word of the first line shouldn't be capitalized", [token for token in sentence_tokens if token.line_index == 0][0].text == "this  ")
    assertion("    the last word of the first line should contain the dot", [token for token in sentence_tokens if token.line_index == 0][-1].text == "sentence  . ")

suite = create_test_suite("Text indexation")
suite.add_test(test_index_single_sentence)
suite.add_test(test_index_multiple_sentences)
suite.add_test(test_index_sentence_with_unorthodox_spacing)