from ..buffer import VirtualBuffer
from ..indexer import text_to_virtual_buffer_tokens
from ...utils.test import create_test_suite

def test_selecting_multiple_fuzzy_words(assertion):
    vb = VirtualBuffer()
    tokens = []
    tokens.extend(text_to_virtual_buffer_tokens("Insert ", "insert"))
    tokens.extend(text_to_virtual_buffer_tokens("a ", "a"))
    tokens.extend(text_to_virtual_buffer_tokens("new ", "new"))
    tokens.extend(text_to_virtual_buffer_tokens("sentence.", "sentence"))

    vb.insert_tokens(tokens)

    assertion( "    Starting from the end and searching for 'Insert an'...") 
    keys = vb.select_phrases(["insert", "an"])
    assertion( "        Should have the text 'Insert a ' selected", vb.caret_tracker.get_selection_text() == 'Insert a ')
    assertion( "        Should go left 22 times to go to the start of 'Insert'", keys[0] == "left:22")
    assertion( "        Should then hold down shift", keys[1] == "shift:down")
    assertion( "        And then go right until 'a ' is selected", keys[2] == "right:9")
    keys = vb.select_phrases(["insert", "new"])
    assertion( "    Starting from the current selection and searching for 'Insert new' ( forgetting 'a' )...")
    assertion( "        Should have the text 'Insert a new ' selected", vb.caret_tracker.get_selection_text() == 'Insert a new ')
    assertion( "        Should go left once to go to the start of 'Insert'", keys[0] == "left")
    assertion( "        Should then hold down shift", keys[1] == "shift:down")
    assertion( "        And then go right until 'new ' is selected", keys[2] == "right:13")
    assertion( "    Starting from the current selection and searching for 'an new'...")
    keys = vb.select_phrases(["an", "new"])
    assertion( "        Should have the text 'a new ' selected", vb.caret_tracker.get_selection_text() == 'a new ')
    assertion( "        Should go right once to go to the end of 'Insert a new '", keys[0] == "right")
    assertion( "        Should then go left 6 times to go to the start of 'a'", keys[1] == "left:6")
    assertion( "        Should then hold down shift", keys[2] == "shift:down")
    assertion( "        And then go right until 'new ' is selected", keys[3] == "right:6")
    keys = vb.select_phrases(["a", "nyou", "sentences"])
    assertion( "    Starting from the current selection and searching for 'a nyou sentences'...")
    assertion( "        Should have the text 'a new sentence.' selected", vb.caret_tracker.get_selection_text() == 'a new sentence.')
    assertion( "        Should go left once to go to the start of 'a '", keys[0] == "left")
    assertion( "        Should then hold down shift", keys[1] == "shift:down")
    assertion( "        Should then go right 15 times to go to the end of 'sentence'", keys[2] == "right:15" )

suite = create_test_suite("Selecting a whole mispronounced phrase in the virtual buffer")
suite.add_test(test_selecting_multiple_fuzzy_words)