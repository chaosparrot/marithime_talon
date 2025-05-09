from ...virtual_buffer.input_history import InputHistory, InputEventType
from ...virtual_buffer.typing import VirtualBufferToken
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite

def get_input_history() -> InputHistory:
    return InputHistory()

def test_marithime_insert_flow(assertion):
    assertion( "Appending the events used for simple marithime insert" )
    input_history = get_input_history()

    # First - Add the insert event
    input_history.add_event(InputEventType.MARITHIME_INSERT, ["this", "big", "word"], 1500)

    # Second - Add the insert event wit hthe transformed text
    input_history.add_event(InputEventType.INSERT, ["thisBigWord"], 1900)

    # Third - Add the inserts to the last event
    events = text_to_virtual_buffer_tokens("this", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Word", "word"))
    input_history.append_insert_to_last_event(events)

    assertion( "    should only have one event appended", len(input_history.history) == 1)
    assertion( "    should not have the insert appended", input_history.get_last_event().type != InputEventType.INSERT )

def test_full_self_repair_flow(assertion):
    assertion( "Appending the events used for self repairs" )
    input_history = get_input_history()

    # First - Add the insert event
    input_history.add_event(InputEventType.MARITHIME_INSERT, ["this", "big", "bird"], 1500)

    # Second - A full self repair is detected
    input_history.add_event(InputEventType.SELF_REPAIR, ["this", "big", "bird"], 1700)
    events = text_to_virtual_buffer_tokens("This", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Word", "word"))
    input_history.append_target_to_last_event(events)

    # Third - A remove event is added after the text is selected
    input_history.add_event(InputEventType.REMOVE, [], 1900)
    events = text_to_virtual_buffer_tokens("Word", "word")
    input_history.append_target_to_last_event(events)

    # Fourth - The insert events gets added and transformed to camel case by the formatter
    # Which chopped off the first part of the insert as that was already available
    input_history.add_event(InputEventType.INSERT, ["Bird"], 1900)
    events = text_to_virtual_buffer_tokens("Bird", "bird")
    input_history.append_insert_to_last_event(events)
    assertion( "    should only have one event appended", len(input_history.history) == 1)
    assertion( "    should only have the self repair added", input_history.get_last_event().type == InputEventType.SELF_REPAIR )

def test_partial_self_repair_flow(assertion):
    assertion( "Appending the events used for partial self repairs" )
    input_history = get_input_history()

    # First - Add the insert event
    input_history.add_event(InputEventType.MARITHIME_INSERT, ["this", "gig", "word"], 1500)

    # Second - A partial self repair is detected
    input_history.add_event(InputEventType.PARTIAL_SELF_REPAIR, ["this", "gig", "word"], 1700)
    events = text_to_virtual_buffer_tokens("This", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    input_history.append_target_to_last_event(events)

    # Third - A remove event is added after the text is selected
    input_history.add_event(InputEventType.REMOVE, [], 1900)
    events = text_to_virtual_buffer_tokens("Big", "big")
    input_history.append_target_to_last_event(events)

    # Fourth - The insert event is added and gets transformed to camel case by the formatter
    # Which chopped off the first part of the insert as that was already available
    input_history.add_event(InputEventType.INSERT, ["GigWord"], 2100)
    events = text_to_virtual_buffer_tokens("Gig", "gig")
    events.extend( text_to_virtual_buffer_tokens("Word", "word"))
    input_history.append_insert_to_last_event(events)
    assertion( "    should only have one event appended", len(input_history.history) == 1)
    assertion( "    should only have the partial self repair added", input_history.get_last_event().type == InputEventType.PARTIAL_SELF_REPAIR )

def test_correction_flow(assertion):
    assertion( "Appending the events used for partial self repairs" )
    input_history = get_input_history()

    # First - Add the correction event
    input_history.add_event(InputEventType.CORRECTION, ["this", "big", "word"], 1500)

    # Second - A target is found
    events = text_to_virtual_buffer_tokens("This", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Bird", "bird"))
    input_history.append_target_to_last_event(events)

    # Third - The marithime insert event is added
    input_history.add_event(InputEventType.MARITHIME_INSERT, ["this", "big", "word"], 1600)

    # Fourth - A remove event is added after the text is selected
    input_history.add_event(InputEventType.REMOVE, [], 1900)
    input_history.append_target_to_last_event(events)

    # Fifth - The insert event is added and gets transformed to camel case by the formatter
    input_history.add_event(InputEventType.INSERT, ["ThisBigWord"], 1900)
    events = text_to_virtual_buffer_tokens("This", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Word", "word"))
    input_history.append_insert_to_last_event(events)
    assertion( "    should only have one event appended", len(input_history.history) == 1)
    assertion( "    should only have the correction added", input_history.get_last_event().type == InputEventType.CORRECTION )

def test_multiple_remove_flows_backspace(assertion):
    assertion( "Appending the events used for pressing backspace multiple times with a selection removal" )
    input_history = get_input_history()

    # First - Add the selection event
    input_history.add_event(InputEventType.SELECT, ["this", "big", "word"], 1500)

    # Second - A target is found
    events = text_to_virtual_buffer_tokens("This", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Bird", "bird"))
    input_history.append_target_to_last_event(events)

    # Third - A remove event is added after the text is selected
    input_history.add_event(InputEventType.REMOVE, [], 2900)
    input_history.append_target_to_last_event(events)

    # Fourth - Another remove event is added right after the text is added
    input_history.add_event(InputEventType.REMOVE, [], 2930)
    events = text_to_virtual_buffer_tokens("Entirely", "entirely")
    input_history.append_target_to_last_event(events, before=True)
    assertion( "    should only have two events appended", len(input_history.history) == 2)
    assertion( "    should only have the remove event at the end", input_history.get_last_event().type == InputEventType.REMOVE )
    assertion( "    should combine the targets together", "".join([token.text for token in input_history.get_last_event().target]) == "EntirelyThisBigBird" )

def test_multiple_remove_flows_delete(assertion):
    assertion( "Appending the events used for pressing delete multiple times with a selection removal" )
    input_history = get_input_history()

    # First - Add the selection event
    input_history.add_event(InputEventType.SELECT, ["this", "big", "word"], 1500)

    # Second - A target is found
    events = text_to_virtual_buffer_tokens("This", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Bird", "bird"))
    input_history.append_target_to_last_event(events)

    # Third - A remove event is added after the text is selected
    input_history.add_event(InputEventType.REMOVE, [], 2900)
    input_history.append_target_to_last_event(events)

    # Fourth - Another remove event is added right after the text is added
    input_history.add_event(InputEventType.REMOVE, [], 2930)
    events = text_to_virtual_buffer_tokens("Entirely", "entirely")
    input_history.append_target_to_last_event(events, before=False)
    assertion( "    should only have two events appended", len(input_history.history) == 2)
    assertion( "    should only have the remove event at the end", input_history.get_last_event().type == InputEventType.REMOVE )
    assertion( "    should combine the targets together", "".join([token.text for token in input_history.get_last_event().target]) == "ThisBigBirdEntirely" )

suite = create_test_suite("Appending events to the history that shouldn't result in more events as they are combined")
suite.add_test(test_marithime_insert_flow)
suite.add_test(test_partial_self_repair_flow)
suite.add_test(test_full_self_repair_flow)
suite.add_test(test_correction_flow)
suite.add_test(test_multiple_remove_flows_backspace)
suite.add_test(test_multiple_remove_flows_delete)