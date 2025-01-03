from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite
from ...virtual_buffer.settings import VirtualBufferSettings

def get_virtual_buffer() -> VirtualBuffer:
    settings = VirtualBufferSettings(live_checking=False)
    return VirtualBuffer(settings)

def get_filled_vb():
    vb = get_virtual_buffer()
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert ", "insert"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("two ", "two"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("words ", "words"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("into ", "into"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("a ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("previous ", "previous"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("sentence, ", "sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("so ", "so"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("that ", "that"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("the ", "the"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("previous ", "previous"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("sentence ", "sentence"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("will ", "will"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("become ", "become"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("longer ", "longer"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("too! ", "too"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("Words ", "words"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("can ", "can"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("be ", "be"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("anything.", "anything"))

    return vb

def test_multiple_words_with_multiple_occurrences(assertion):
    vb = get_filled_vb()
    assertion( "    Starting from the end and searching for 'previous sentence'...")
    keys = vb.select_phrases(["previous", "sentence"], verbose=False)
    assertion( "        Should have the text 'previous sentence ' selected", vb.caret_tracker.get_selection_text() == 'previous sentence ')
    assertion( "        Should go left 64 times to go to the start of 'previous sentence '", keys[0] == "left:64")
    assertion( "        And then go right until 'previous sentence ' is selected", keys[1] == "shift-right:18")
    assertion( "    Starting from the end of the word 'so' and searching for 'previous sentence'...")
    vb.go_phrase("so")
    keys = vb.select_phrases(["previous", "sentence"])
    assertion( "        Should have the text 'previous sentence, ' selected", vb.caret_tracker.get_selection_text() == 'previous sentence, ')
    assertion( "        Should go left until the start of 'previous'", keys[0] == "left:22")
    assertion( "        And then go right until 'previous sentence, ' is selected", keys[1] == "shift-right:19")
    assertion( "    Starting from the current selection and and searching for 'to words'...")
    keys = vb.select_phrases(["to", "words"])
    assertion( "        Should have the text 'two words ' selected", vb.caret_tracker.get_selection_text() == 'two words ')
    assertion( "        Should deselect the current selection", keys[0] == "left")
    assertion( "        Should go left once to go to the start of 'two'", keys[1] == "left:17")
    assertion( "        And then go right until 'two words ' is selected", keys[2] == "shift-right:10")
    assertion( "    Moving to the end of the inserted text and searching for 'to words'...")
    vb.go_phrase('anything')
    keys = vb.select_phrases(["to", "words"])
    assertion( "        Should have the text 'too! Words ' selected", vb.caret_tracker.get_selection_text() == 'too! Words ')
    assertion( "        Should go left once to go to the start of 'too!'", keys[0] == "left:27")
    assertion( "        And then go right until 'too! Words ' is selected", keys[1] == "shift-right:11")

suite = create_test_suite("Selecting a whole phrase in the virtual buffer that happens multiple times")
suite.add_test(test_multiple_words_with_multiple_occurrences)