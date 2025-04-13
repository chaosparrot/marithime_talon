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

    # Second - The insert gets transformed to camel case
    events = text_to_virtual_buffer_tokens("this", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Word", "word"))
    input_history.append_insert_to_last_event(events)

    # Third - Add the insert event
    input_history.add_event(InputEventType.INSERT, ["thisBigWord"], 1900)
    assertion( "    should only have one event appended", len(input_history.history) == 1)
    assertion( "    should not have the insert appended", input_history.get_last_event().type != InputEventType.INSERT )

def test_full_self_repair_flow(assertion):
    assertion( "Appending the events used for self repairs" )
    input_history = get_input_history()

    # First - Add the insert event
    input_history.add_event(InputEventType.MARITHIME_INSERT, ["this", "big", "word"], 1500)

    # Second - A partial self repair is detected
    input_history.add_event(InputEventType.SELF_REPAIR, ["this", "big", "word"], 1700)
    events = text_to_virtual_buffer_tokens("This", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Word", "word"))
    input_history.append_target_to_last_event(events)

    # Third - The insert gets transformed to camel case by the formatter
    events = text_to_virtual_buffer_tokens("This", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Word", "word"))
    input_history.append_insert_to_last_event(events)

    # Third - Add the insert event
    input_history.add_event(InputEventType.INSERT, ["ThisBigWord"], 1900)
    assertion( "    should only have one event appended", len(input_history.history) == 1)
    assertion( "    should only have the self repair added", input_history.get_last_event().type == InputEventType.SELF_REPAIR )

def test_partial_self_repair_flow(assertion):
    assertion( "Appending the events used for partial self repairs" )
    input_history = get_input_history()

    # First - Add the insert event
    input_history.add_event(InputEventType.MARITHIME_INSERT, ["this", "big", "word"], 1500)

    # Second - A partial self repair is detected
    input_history.add_event(InputEventType.PARTIAL_SELF_REPAIR, ["this", "big", "word"], 1700)
    events = text_to_virtual_buffer_tokens("This", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    input_history.append_target_to_last_event(events)

    # Third - The insert gets transformed to camel case by the formatter
    events = text_to_virtual_buffer_tokens("This", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Word", "word"))
    input_history.append_insert_to_last_event(events)

    # Third - Add the insert event
    input_history.add_event(InputEventType.INSERT, "ThisBigWord", 1900)
    assertion( "    should only have one event appended", len(input_history.history) == 1)
    assertion( "    should only have the partial self repair added", input_history.get_last_event().type == InputEventType.PARTIAL_SELF_REPAIR )

def test_skip_self_repair_flow(assertion):
    assertion( "Appending the events used for skip self repairs" )
    input_history = get_input_history()

    # First - Add the insert event
    input_history.add_event(InputEventType.MARITHIME_INSERT, ["this", "big", "word"], 1500)

    # Second - A skip self repair is detected
    input_history.add_event(InputEventType.SKIP_SELF_REPAIR, ["this", "big", "word"], 1700)
    events = text_to_virtual_buffer_tokens("This", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    input_history.append_target_to_last_event(events)

    # Third - The insert gets transformed to camel case by the formatter
    events = text_to_virtual_buffer_tokens("This", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Word", "word"))
    input_history.append_insert_to_last_event(events)

    # Third - Add the insert event
    input_history.add_event(InputEventType.INSERT, "ThisBigWord", 1900)
    assertion( "    should only have one event appended", len(input_history.history) == 1)
    assertion( "    should only have the skip self repair added", input_history.get_last_event().type == InputEventType.SKIP_SELF_REPAIR )


def test_correction_flow(assertion):
    assertion( "Appending the events used for partial self repairs" )
    input_history = get_input_history()

    # First - Add the insert event
    input_history.add_event(InputEventType.CORRECTION, ["this", "big", "word"], 1500)

    # Second - A target is found
    events = text_to_virtual_buffer_tokens("This", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Bird", "bird"))    
    input_history.append_target_to_last_event(events)

    # Third - The insert gets transformed to camel case by the formatter
    events = text_to_virtual_buffer_tokens("This", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Word", "word"))
    input_history.append_insert_to_last_event(events)

    # Fourth - Add the insert event
    input_history.add_event(InputEventType.INSERT, "ThisBigWord", 1900)
    assertion( "    should only have one event appended", len(input_history.history) == 1)
    assertion( "    should only have the correction added", input_history.get_last_event().type == InputEventType.CORRECTION )

suite = create_test_suite("Appending events to the history that shouldn't result in more events as they are combined")
suite.add_test(test_marithime_insert_flow)
suite.add_test(test_partial_self_repair_flow)
suite.add_test(test_full_self_repair_flow)
# suite.add_test(test_skip_self_repair_flow) - TODO - FIX SKIP SELF REPAIR FLOW
suite.add_test(test_correction_flow)