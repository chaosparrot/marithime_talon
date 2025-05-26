from ...virtual_buffer.caret_tracker import _CARET_MARKER
from ...virtual_buffer.buffer import VirtualBuffer
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite
from ...virtual_buffer.settings import VirtualBufferSettings
from ...virtual_buffer.input_history import InputHistory, InputEventType

def get_virtual_buffer() -> VirtualBuffer:
    settings = VirtualBufferSettings(live_checking=False)
    return VirtualBuffer(settings)

def get_filled_vb() -> InputHistory:
    vb = get_virtual_buffer()
    vb.insert_tokens(text_to_virtual_buffer_tokens("Suggest ", "suggest"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("create ", "create"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("delete ", "delete"))
    vb.insert_tokens(text_to_virtual_buffer_tokens("insertion", "insertion"))
    vb.caret_tracker.text_buffer = "Suggest create delete insertion" + _CARET_MARKER

    return vb

def test_append_events_after_buffer(assertion):
    assertion( "Appending marithime inserts after one another" )
    buffer = get_filled_vb()
    input_history = buffer.input_history

    # Simulate inserting through insert_tokens directly
    buffer.input_history.add_event(InputEventType.MARITHIME_INSERT, ["creation"])
    buffer.insert_tokens(text_to_virtual_buffer_tokens(" creation", "creation"))
    assertion( "    Should give the history one event", len(input_history.history) == 1)
    assertion( "    Should add the token on the same line as the others", input_history.history[-1].insert[0].line_index == 0)
    assertion( "    Should add the token at the end of the line", input_history.history[-1].insert[0].index_from_line_end == 0)

    # Simulate inserting through insert_tokens directly
    assertion( "Appending another event" )
    buffer.input_history.add_event(InputEventType.MARITHIME_INSERT, ["deletion"])
    buffer.insert_tokens(text_to_virtual_buffer_tokens(" deletion", "deletion"))
    assertion( "    Should give the history two events", len(input_history.history) == 2)
    assertion( "    Should add the token on the same line as the others", input_history.history[-1].insert[0].line_index == 0)
    assertion( "    Should add the token at the end of the line", input_history.history[-1].insert[0].index_from_line_end == 0)

    assertion( "Adding a line end" )
    buffer.input_history.add_event(InputEventType.INSERT, [])
    buffer.insert_tokens(text_to_virtual_buffer_tokens(".\n", ""))
    assertion( "    Should give the history three events", len(input_history.history) == 3)
    assertion( "    Should add the token after the next line", input_history.history[-1].insert[0].line_index == 1)
    assertion( "    Should add the token at the end of the line", input_history.history[-1].insert[0].index_from_line_end == 0)

    assertion( "Adding a token after the line end" )
    buffer.input_history.add_event(InputEventType.MARITHIME_INSERT, ["testing"])
    buffer.insert_tokens(text_to_virtual_buffer_tokens("Testing", "testing"))
    assertion( "    Should give the history four events", len(input_history.history) == 4)
    assertion( "    Should add the token on the second line", input_history.history[-1].insert[0].line_index == 1)
    assertion( "    Should add the token at the end of the line", input_history.history[-1].insert[0].index_from_line_end == 0)    

def test_append_events_between_buffer(assertion):
    assertion( "Appending marithime inserts in the middle of the buffer" )
    buffer = get_filled_vb()
    buffer.caret_tracker.text_buffer = "Suggest create " + _CARET_MARKER + "delete insertion"
    input_history = buffer.input_history

    buffer.input_history.add_event(InputEventType.MARITHIME_INSERT, ["abolition"])
    buffer.insert_tokens(text_to_virtual_buffer_tokens("abolition ", "abolition"))
    assertion( "    Should give the history one events", len(input_history.history) == 1)
    assertion( "    Should add the token on the same line as the others", input_history.history[-1].insert[0].line_index == 0)
    assertion( "    Should add the token at the middle of the line", input_history.history[-1].insert[0].index_from_line_end == 16)

    assertion( "Adding a line end" )
    buffer.input_history.add_event(InputEventType.INSERT, [])
    buffer.insert_tokens(text_to_virtual_buffer_tokens(".\n", ""))
    assertion( "    Should give the history two events", len(input_history.history) == 2)
    assertion( "    Should set the token on the next line", input_history.history[-1].insert[0].line_index == 1)
    assertion( "    Should set the token at the end of the line", input_history.history[-1].insert[0].index_from_line_end == 16)

    assertion( "Adding a token after the line end" )
    buffer.input_history.add_event(InputEventType.MARITHIME_INSERT, ["testing"])
    buffer.insert_tokens(text_to_virtual_buffer_tokens("Testing ", "testing"))
    assertion( "    Should give the history three events", len(input_history.history) == 3)
    assertion( "    Should add the token on the second line", input_history.history[-1].insert[0].line_index == 1)
    assertion( "    Should add the token at the end of the line", input_history.history[-1].insert[0].index_from_line_end == 16)

def test_append_events_between_token(assertion):
    assertion( "Appending marithime inserts in the middle of a token" )
    buffer = get_filled_vb()
    buffer.caret_tracker.text_buffer = "Suggest" + _CARET_MARKER + " create delete insertion"
    input_history = buffer.input_history

    buffer.input_history.add_event(InputEventType.MARITHIME_INSERT, ["abolition"])
    buffer.insert_tokens(text_to_virtual_buffer_tokens("abolition ", "abolition"))
    assertion( "    Should give the history one event", len(input_history.history) == 1)
    assertion( "    Should add the token on the same line as the others", input_history.history[-1].insert[0].line_index == 0)
    assertion( "    Should add the token at the middle of the line", input_history.history[-1].insert[0].index_from_line_end == 24)
    assertion( "    Should merge the text from the returned token in the tokens", buffer.tokens[0].text == "Suggestabolition ")
    assertion( "    Should not merge the text from the returned token in the input history", input_history.history[-1].insert[0].text == "abolition ")

def test_append_events_between_token_split(assertion):
    assertion( "Appending marithime inserts in the middle of a token to split it in two" )
    buffer = get_filled_vb()
    buffer.caret_tracker.text_buffer = "Sugg" + _CARET_MARKER + "est create delete insertion"
    input_history = buffer.input_history

    buffer.input_history.add_event(InputEventType.MARITHIME_INSERT, ["abolition"])
    buffer.insert_tokens(text_to_virtual_buffer_tokens("abolition ", "abolition"))
    assertion( "    Should give the history one event", len(input_history.history) == 1)
    assertion( "    Should add the token on the same line as the others", input_history.history[-1].insert[0].line_index == 0)
    assertion( "    Should add the token at the middle of the line", input_history.history[-1].insert[0].index_from_line_end == 27)
    assertion( "    Should merge the text from the returned token in the tokens", buffer.tokens[0].text == "Suggabolition ")
    assertion( "    Should not merge the text from the returned token in the input history", input_history.history[-1].insert[0].text == "abolition ")

def test_append_events_between_token_merge(assertion):
    assertion( "Appending marithime inserts in the middle of a token to merge it" )
    buffer = get_filled_vb()
    buffer.caret_tracker.text_buffer = "Sugg" + _CARET_MARKER + "est create delete insertion"
    input_history = buffer.input_history

    buffer.input_history.add_event(InputEventType.MARITHIME_INSERT, ["abolition"])
    buffer.insert_tokens(text_to_virtual_buffer_tokens("abolition", "abolition"))
    assertion( "    Should give the history one event", len(input_history.history) == 1)
    assertion( "    Should add the token on the same line as the others", input_history.history[-1].insert[0].line_index == 0)
    assertion( "    Should add the token at the middle of the line", input_history.history[-1].insert[0].index_from_line_end == 27)
    assertion( "    Should merge the text from the returned token in the tokens", buffer.tokens[0].text == "Suggabolitionest ")
    assertion( "    Should not merge the text from the returned token in the input history", input_history.history[-1].insert[0].text == "abolition")


def test_append_events_with_clear_on_enter(assertion):
    assertion( "Appending marithime inserts with an enter clear key" )
    buffer = get_filled_vb()
    buffer.settings.multiline_supported = False
    buffer.settings.clear_key = "enter"
    input_history = buffer.input_history

    # Simulate inserting through insert_tokens directly
    buffer.input_history.add_event(InputEventType.MARITHIME_INSERT, ["creation"])
    buffer.insert_tokens(text_to_virtual_buffer_tokens(".\nCreation", "creation"))
    assertion( "    Should have a single token", len(buffer.tokens) == 1)
    assertion( "    Should give the history one event", len(input_history.history) == 1)
    assertion( "    Should add the token on the same line as the others", input_history.history[-1].insert[0].line_index == 0)
    assertion( "    Should add the token at the end of the line", input_history.history[-1].insert[0].index_from_line_end == 0)

def test_append_events_with_partial_self_repair(assertion):
    assertion( "Appending marithime inserts with a partial self repair" )
    buffer = get_filled_vb()
    buffer.settings.multiline_supported = False
    buffer.settings.clear_key = "enter"
    input_history = buffer.input_history

    assertion( "Appending marithime insert event" )
    buffer.input_history.add_event(InputEventType.MARITHIME_INSERT, ["anding"])
    buffer.insert_tokens(text_to_virtual_buffer_tokens(" anding", "anding"))
    assertion( "    Should give the history two events", len(input_history.history) == 2)

    assertion( "Appending the partial self repair event with the target" )
    buffer.input_history.add_event(InputEventType.PARTIAL_SELF_REPAIR, ["ending", "with"])
    buffer.input_history.append_target_to_last_event([buffer.tokens[-1]])
    insert_tokens = text_to_virtual_buffer_tokens(" anding", "anding")
    insert_tokens.extend(text_to_virtual_buffer_tokens(" with", "with"))
    buffer.insert_tokens(insert_tokens)
    assertion( "    Should give the history two events", len(input_history.history) == 2)
    assertion( "    Should not count a repetition", input_history.get_repetition_count() == 0)
    assertion( "    Should retrieve the full insertion of the partial self repair", len(input_history.history[-1].insert) == 2)

def test_append_events_with_continuous_self_repair(assertion):
    assertion( "Appending marithime inserts with a continuous self repair" )
    buffer = get_filled_vb()
    buffer.settings.multiline_supported = False
    buffer.settings.clear_key = "enter"
    input_history = buffer.input_history

    assertion( "Appending marithime insert event" )
    buffer.input_history.add_event(InputEventType.MARITHIME_INSERT, ["anding"])
    buffer.insert_tokens(text_to_virtual_buffer_tokens(" anding", "anding"))
    assertion( "    Should give the history two events", len(input_history.history) == 2)

    assertion( "Appending the partial self repair event with the target" )
    buffer.input_history.add_event(InputEventType.PARTIAL_SELF_REPAIR, ["ending", "with"])
    buffer.input_history.append_target_to_last_event([buffer.tokens[-2], buffer.tokens[-1]])

    # Skip the ending insert token as it isn't being executed
    insert_tokens = text_to_virtual_buffer_tokens(" with", "with")
    buffer.insert_tokens(insert_tokens)
    assertion( "    Should give the history two events", len(input_history.history) == 2)
    assertion( "    Should not count a repetition", input_history.get_repetition_count() == 0)
    assertion( "    Should retrieve the combined insert of the partial self repair", len(input_history.history[-1].insert) == 2)
    assertion( "    Should start the insert with the same token", input_history.history[-1].insert[0].phrase == "ending")
    assertion( "    Should end the insert with the token 'with'", input_history.history[-1].insert[-1].phrase == "with")

def test_append_events_with_continuous_partial_self_repair(assertion):
    assertion( "Appending marithime inserts with a continuous self repair" )
    buffer = get_filled_vb()
    buffer.settings.multiline_supported = False
    buffer.settings.clear_key = "enter"
    input_history = buffer.input_history

    assertion( "Appending marithime insert event" )
    buffer.input_history.add_event(InputEventType.MARITHIME_INSERT, ["anding"])
    buffer.insert_tokens(text_to_virtual_buffer_tokens(" anding", "anding"))
    assertion( "    Should give the history two events", len(input_history.history) == 2)

    assertion( "Appending the continuous partial self repair event with the target" )
    buffer.input_history.add_event(InputEventType.PARTIAL_SELF_REPAIR, ["insertion", "ending", "with"])
    buffer.input_history.append_target_to_last_event([buffer.tokens[-3], buffer.tokens[-2], buffer.tokens[-1]])

    # Skip the 'insertion' insert token as it isn't being executed
    insert_tokens = text_to_virtual_buffer_tokens(" anding", "anding")
    insert_tokens.extend(text_to_virtual_buffer_tokens(" with", "with"))
    buffer.insert_tokens(insert_tokens)
    assertion( "    Should give the history two events", len(input_history.history) == 2)
    assertion( "    Should not count a repetition", input_history.get_repetition_count() == 0)
    assertion( "    Should retrieve the combined insert of the continuous partial self repair", len(input_history.history[-1].insert) == 3)
    assertion( "    Should start the insert with the 'insertion' token", input_history.history[-1].insert[0].phrase == "insertion")
    assertion( "    Should end the insert with the replaced token 'ending'", input_history.history[-1].insert[1].phrase == "with")
    assertion( "    Should end the insert with the token 'with'", input_history.history[-1].insert[-1].phrase == "with")

suite = create_test_suite("Appending insert tokens after history events")
suite.add_test(test_append_events_after_buffer)
suite.add_test(test_append_events_between_buffer) 
suite.add_test(test_append_events_between_token)
suite.add_test(test_append_events_between_token_split)
suite.add_test(test_append_events_between_token_merge)
suite.add_test(test_append_events_with_clear_on_enter)

#suite.add_test(test_append_events_with_partial_self_repair)
#suite.add_test(test_append_events_with_continuous_self_repair)
#suite.add_test(test_append_events_with_continuous_partial_self_repair) 
#suite.run()