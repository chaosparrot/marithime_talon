from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite
from ...virtual_buffer.settings import VirtualBufferSettings

def get_virtual_buffer() -> VirtualBuffer:
    settings = VirtualBufferSettings(live_checking=False)
    return VirtualBuffer(settings)

def test_virtual_select_single_word_and_extending(assertion):
    vb = get_virtual_buffer()
    vb.settings.shift_selection = False
    vb.insert_tokens(text_to_virtual_buffer_tokens("Insert ", "insert"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("a ", "a"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("new ", "new"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("sentence.", "sentence"))

    assertion( "    Selecting a single character to the left and then selecting 'Insert a'...")
    keys = vb.select_phrases(["insert", "a"])
    assertion( "        Should not have the text 'Insert a ' selected", vb.caret_tracker.get_selection_text() != 'Insert a ')
    assertion( "        Should start the virtual selecting with 'Insert '", vb.virtual_selection[0].text == 'Insert ')    
    assertion( "        Should not deselect the previous selection", keys[0] not in ["left", "right"])
    assertion( "        Should go right 13 times to connect the end of 'a '", keys[0] == "left:13")
    assertion( "    Virtually selecting 'Insert ' until 'new ' after that...")
    vb.select_phrases(["insert"])
    keys = vb.select_phrases(["new"], extend_selection=True) 
    assertion( "        Should not have the text 'Insert a new ' selected", vb.caret_tracker.get_selection_text() != 'Insert a new ')
    assertion( "        Should end the virtual selecting with 'new '", vb.virtual_selection[-1].text == 'new ')
    assertion( "        Should not deselect the previous selection", keys[0] not in ["left", "right"])
    assertion( "        Should go right 6 times to connect the end of 'Insert ' with 'new '", keys[0] == "right:6") 
    assertion( "    Virtually selecting 'Insert ' and extend it until the end of the buffer...")
    keys = vb.select_until_end("insert")
    assertion( "        Should not have the text 'Insert a new sentence.' selected", vb.caret_tracker.get_selection_text() != 'Insert a new sentence.')
    assertion( "        Should not deselect the previous selection", keys[0] not in ["left", "right"])
    assertion( "        Should end the virtual selecting with 'sentence.'", vb.virtual_selection[-1].text == 'sentence.')    
    assertion( "        Should go right 10 times to go from the end of 'Insert a new ' to the end of 'sentence.'", keys[0] == "right:9")
    assertion( "    Virtually selecting 'new ' and extend it until the end of the buffer...")
    vb.select_phrases(["new"])
    keys = vb.select_until_end()
    assertion( "        Should not have the text 'new sentence.' selected", vb.caret_tracker.get_selection_text() != 'new sentence.')
    assertion( "        Should end the virtual selecting with 'sentence.'", vb.virtual_selection[-1].text == 'sentence.')
    assertion( "        Should not deselect the previous selection", keys[0] not in ["left", "right"])
    assertion( "        Should go right 9 times to connect the end of 'new ' with 'sentence.'", keys[0] == "right:9")
    assertion( "    Virtually selecting 'Insert ' using 'inssert' and extend it until the end of the buffer...")
    keys = vb.select_until_end("inssert")
    assertion( "        Should not have the text 'Insert a new sentence.' selected", vb.caret_tracker.get_selection_text() != 'Insert a new sentence.')
    assertion( "        Should not move at all since we have the same end selection", len(keys) == 0)

suite = create_test_suite("Virtual selection range after words")
suite.add_test(test_virtual_select_single_word_and_extending)