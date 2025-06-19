from ...virtual_buffer.indexer import VirtualBufferIndexer
from ...virtual_buffer.caret_tracker import _CARET_MARKER
from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.settings import VirtualBufferSettings
from ..test import create_test_suite

def get_virtual_buffer() -> VirtualBuffer:
    settings = VirtualBufferSettings(live_checking=False)
    return VirtualBuffer(settings)

def test_appending_single_middle_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "This is a testing" + _CARET_MARKER + ".")
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'This is a testing.'")
    assertion("    Should result in the same amount of tokens than those that we started with", len(tokens) == len(starting_tokens))
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should result in a reindexation", tokens[0].index_from_line_end != starting_tokens[0].index_from_line_end)
    assertion("    Should have the text 'testing.' at the end of the newly added tokens", "".join([token.text for token in tokens]).endswith("testing."))

def test_appending_multiple_middle_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "This is a testing project" + _CARET_MARKER + ".")
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'This is a testing project.'")
    assertion("    Should result in more tokens than those that we started with", len(tokens) > len(starting_tokens))
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should result in a reindexation", tokens[0].index_from_line_end != starting_tokens[0].index_from_line_end)
    assertion("    Should have the text 'testing project.' at the end of the newly added tokens", "".join([token.text for token in tokens]).endswith("testing project."))
    assertion("    Should have 'project.' as the last token", tokens[-1].text == "project.")

def test_prepending_single_middle_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "Thisi" + _CARET_MARKER + "s is a test.")
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'Thisis is a test.'")
    assertion("    Should result in the same amount of tokens than those that we started with", len(tokens) == len(starting_tokens))
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should have the text 'Thisis' at the start of the newly added tokens", "".join([token.text for token in tokens]).startswith("Thisis"))

def test_prepending_multiple_middle_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "Thiseus walt" + _CARET_MARKER + "s is a test.")
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'Thiseus walts is a test.'")
    assertion("    Should result in more tokens than those that we started with", len(tokens) > len(starting_tokens))
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should have the text 'Thiseus walts ' at the start of the newly added tokens", "".join([token.text for token in tokens]).startswith("Thiseus walts "))

def test_inserting_single_start_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "This w" + _CARET_MARKER + "is a test.")
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'This wis a test.'")
    assertion("    Should result in the same amount of tokens than those that we started with", len(tokens) == len(starting_tokens))
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should have the text 'This wis' at the start of the newly added tokens", "".join([token.text for token in tokens]).startswith("This wis"))
    print(  "".join([token.text for token in tokens]) )

def test_inserting_multiple_start_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "This was gen" + _CARET_MARKER + "is a test.")
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'This was genis a test.'")
    assertion("    Should result in more tokens than those that we started with", len(tokens) > len(starting_tokens))
    assertion("    Should not result in a clearing of the format of the ending tokens", tokens[-1].format == "testingformat")
    assertion("    Should have the text 'This was genis' at the start of the newly added tokens", "".join([token.text for token in tokens]).startswith("This was genis"))
    print(  "".join([token.text for token in tokens]) )

def test_prepending_single_start_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "T" + _CARET_MARKER + "This is a test.")
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'TThis is a test.'")
    assertion("    Should result in the same amount of tokens than those that we started with", len(tokens) == len(starting_tokens))
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should have the text 'TThis' at the start of the newly added tokens", "".join([token.text for token in tokens]).startswith("TThis"))
    print(  "".join([token.text for token in tokens]) )

def test_prepending_multiple_start_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "There was a time where" + _CARET_MARKER + "This is a test.")
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'There was a time whereThis is a test.'")
    assertion("    Should result in more tokens than those that we started with", len(tokens) > len(starting_tokens))
    assertion("    Should not result in a clearing of the format of the ending tokens", tokens[-1].format == "testingformat")
    assertion("    Should have the text 'There was a time whereThis' at the start of the newly added tokens", "".join([token.text for token in tokens]).startswith("There was a time whereThis"))
    print(  "".join([token.text for token in tokens]) )

def test_inserting_single_middle_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "This is and" + _CARET_MARKER + " test.")
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'This is and test.'")
    assertion("    Should result in the same amount of tokens than those that we started with", len(tokens) == len(starting_tokens))
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should result in a reindexation", tokens[0].index_from_line_end != starting_tokens[0].index_from_line_end)
    assertion("    Should have the text 'and test.' at the end of the newly added tokens", "".join([token.text for token in tokens]).endswith("and test."))

def test_inserting_multiple_middle_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"    
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "This is and will" + _CARET_MARKER + " test.")
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'This is and will test.'")
    assertion("    Should result in more tokens than those that we started with", len(tokens) > len(starting_tokens))
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should result in a reindexation", tokens[0].index_from_line_end != starting_tokens[0].index_from_line_end)
    assertion("    Should have the text 'and will test.' at the end of the newly added tokens", "".join([token.text for token in tokens]).endswith("and will test."))

def test_removing_single_middle_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    starting_tokens_length = len(starting_tokens)
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "This is a te" + _CARET_MARKER + "t.")
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'This is a tet.'")
    assertion("    Should result the same amount of tokens as we started with", len(tokens) == starting_tokens_length)
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should result in a reindexation", tokens[0].index_from_line_end != starting_tokens[0].index_from_line_end)
    assertion("    Should have the text 'tet.' at the end of the newly added tokens", "".join([token.text for token in tokens]).endswith("tet."))

def test_removing_multiple_middle_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    starting_tokens_length = len(starting_tokens)
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "This is" + _CARET_MARKER + "t.")
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'This ist.'")
    assertion("    Should result less tokens than those that we started with", len(tokens) < starting_tokens_length)
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should result in a reindexation", tokens[0].index_from_line_end != starting_tokens[0].index_from_line_end)
    assertion("    Should have the text 'ist.' at the end of the newly added tokens", "".join([token.text for token in tokens]).endswith("ist."))

def test_removing_single_start_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    starting_tokens_length = len(starting_tokens)
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, _CARET_MARKER + "is is a test.")
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'is is a test.'")
    assertion("    Should result in the same amount of tokens as we started with", len(tokens) == starting_tokens_length)
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should have the text 'is is' at the start of the newly added tokens", "".join([token.text for token in tokens]).startswith("is is"))
    assertion("    Should have the text 'a test.' at the end of the newly added tokens", "".join([token.text for token in tokens]).endswith("a test."))

def test_removing_multiple_start_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    starting_tokens_length = len(starting_tokens)
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "Thi" + _CARET_MARKER + "s a test.")
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'This a test.'")
    assertion("    Should result in less tokens than those that we started with", len(tokens) < starting_tokens_length)
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should result in a reindexation", tokens[0].index_from_line_end != starting_tokens[0].index_from_line_end)
    assertion("    Should have the text 'This' at the start of the newly added tokens", "".join([token.text for token in tokens]).startswith("This "))
    assertion("    Should have the text 'a test.' at the end of the newly added tokens", "".join([token.text for token in tokens]).endswith("a test."))

def test_removing_single_end_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    starting_tokens_length = len(starting_tokens)
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "This is a tes" + _CARET_MARKER)
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'This a tes'")
    assertion("    Should result in the same amount of tokens as we started with", len(tokens) == starting_tokens_length)
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should result in a reindexation", tokens[0].index_from_line_end != starting_tokens[0].index_from_line_end)
    assertion("    Should have the text 'This' at the start of the newly added tokens", "".join([token.text for token in tokens]).startswith("This "))
    assertion("    Should have the text 'a tes' at the end of the newly added tokens", "".join([token.text for token in tokens]).endswith("a tes"))

def test_removing_multiple_end_of_token(assertion):
    input_indexer = VirtualBufferIndexer()
    vb = get_virtual_buffer()
    starting_tokens = input_indexer.index_text("This is a test.")
    starting_tokens[0].format = "testingformat"
    starting_tokens[-1].format = "testingformat"
    starting_tokens_length = len(starting_tokens)
    tokens, indices_to_insert = input_indexer.index_partial_tokens("This is a test.", starting_tokens, "This i" + _CARET_MARKER)
    vb.set_and_merge_tokens(tokens, indices_to_insert)
    tokens = vb.tokens

    assertion("Comparing the sentence 'This is a test.' with 'This a tes'")
    assertion("    Should result in less tokens than those that we started with", len(tokens) < starting_tokens_length)
    assertion("    Should not result in a clearing of the format of the starting tokens", tokens[0].format == "testingformat")
    assertion("    Should result in a reindexation", tokens[0].index_from_line_end != starting_tokens[0].index_from_line_end)
    assertion("    Should have the text 'This' at the start of the newly added tokens", "".join([token.text for token in tokens]).startswith("This "))
    assertion("    Should have the text 'a tes' at the end of the newly added tokens", "".join([token.text for token in tokens]).endswith("i"))


suite = create_test_suite("Partial indexation with cases of appending and removing in the middle of tokens")
suite.add_test(test_appending_single_middle_of_token)
suite.add_test(test_appending_multiple_middle_of_token)
suite.add_test(test_prepending_single_middle_of_token)
suite.add_test(test_prepending_multiple_middle_of_token)
#suite.add_test(test_prepending_single_start_of_token)
#suite.add_test(test_prepending_multiple_start_of_token)
#suite.add_test(test_inserting_single_start_of_token)
#suite.add_test(test_inserting_multiple_start_of_token)
suite.add_test(test_inserting_single_middle_of_token)
suite.add_test(test_inserting_multiple_middle_of_token)
suite.add_test(test_removing_single_middle_of_token)
suite.add_test(test_removing_multiple_middle_of_token)
suite.add_test(test_removing_single_start_of_token)
suite.add_test(test_removing_multiple_start_of_token)
suite.add_test(test_removing_single_end_of_token)
suite.add_test(test_removing_multiple_end_of_token)
suite.run() 