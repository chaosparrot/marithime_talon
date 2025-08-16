from ...virtual_buffer.indexer import VirtualBufferIndexer
from ..test import create_test_suite

input_indexer = VirtualBufferIndexer()

def test_index_single_english_sentence(assertion):
    sentence_tokens = input_indexer.index_text("This is a test.")
    assertion( "Indexing the sentence 'This is a test.'...")
    assertion("    should consist of 4 virtual buffer tokens", len(sentence_tokens) == 4)
    assertion("    should all be considered english dictation tokens", len([token.format for token in sentence_tokens if token.format == "english"]) == 4)

def test_index_single_dutch_sentence(assertion):
    sentence_tokens = input_indexer.index_text("Dit is een test.")
    assertion( "Indexing the sentence 'Dit is een test.'...")
    assertion("    should consist of 4 virtual buffer tokens", len(sentence_tokens) == 4)
    assertion("    should all be considered dutch dictation tokens", len([token.format for token in sentence_tokens if token.format == "dutch"]) == 4)

def test_index_snakecase_text(assertion):
    sentence_tokens = input_indexer.index_text("change_place")
    assertion( "Indexing the words 'change_place'...")
    assertion("    should consist of 2 virtual buffer tokens", len(sentence_tokens) == 2)
    assertion("    should all be considered snakecase tokens", len([token.format for token in sentence_tokens if token.format == "snakecase"]) == 2)

def test_index_camelcase_text(assertion):
    sentence_tokens = input_indexer.index_text("changePlace")
    assertion( "Indexing the words 'changePlace'...")
    assertion("    should consist of 2 virtual buffer tokens", len(sentence_tokens) == 2)
    assertion("    should all be considered camelcase tokens", len([token.format for token in sentence_tokens if token.format == "camelcase"]) == 2)

def test_index_snakecase_and_camelcase_test(assertion):
    sentence_tokens = input_indexer.index_text("changePlace change_place")
    assertion( "Indexing the words 'changePlace change_place'...")
    assertion("    should consist of 2 virtual buffer tokens", len(sentence_tokens) == 4)
    assertion("    should considered the first two tokens to be camelcase", len([token.format for token in sentence_tokens[:-2] if token.format == "camelcase"]) == 2)
    assertion("    should considered the last two tokens to be snakecase", len([token.format for token in sentence_tokens[-2:] if token.format == "snakecase"]) == 2)

def test_index_snakecase_and_camelcase_with_dot_test(assertion):
    sentence_tokens = input_indexer.index_text("changePlace.change_place")
    assertion( "Indexing the words 'changePlace'...")
    assertion("    should consist of 2 virtual buffer tokens", len(sentence_tokens) == 4)
    assertion("    should considered the first two tokens to be camelcase", len([token.format for token in sentence_tokens[:-2] if token.format == "camelcase"]) == 2)
    assertion("    should considered the last two tokens to be snakecase", len([token.format for token in sentence_tokens[-2:] if token.format == "snakecase"]) == 2)

suite = create_test_suite("Automatic formatter detection")
suite.add_test(test_index_snakecase_text)
suite.add_test(test_index_camelcase_text)
suite.add_test(test_index_snakecase_and_camelcase_test)
suite.add_test(test_index_snakecase_and_camelcase_with_dot_test)
suite.add_test(test_index_single_english_sentence)
suite.add_test(test_index_single_dutch_sentence)