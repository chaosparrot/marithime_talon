from ...virtual_buffer.input_history import InputHistory, InputEventType
from ...virtual_buffer.typing import VirtualBufferToken
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite

def get_input_history() -> InputHistory:
    return InputHistory()

def test_skip_non_skippable_events_flow(assertion):
    assertion( "Appending unskippable events after marking an event as skipped" )
    input_history = get_input_history()

    for event_type in [
        InputEventType.REMOVE,
        InputEventType.INSERT,
        # InputEventType.MARITHIME_INSERT, - Used for self repair flows
        InputEventType.INSERT_CHARACTER,
        InputEventType.SELECT,
        InputEventType.NAVIGATION
    ]:
        # First - add an event
        input_history.add_event(event_type, ["this", "big", "bird"], 1000)

        # Second - Mark the next event as a skip event
        input_history.mark_next_as_skip()

        # Third - Repeat the event again
        input_history.add_event(event_type, ["this", "big", "bird"], 2000)
        assertion( "    Should give the history two " + str(event_type) + " events", len(input_history.history) == 2)
        assertion( "    Should detect a repetition", input_history.is_repetition())
        input_history.flush_history()

def test_skip_correction_flow(assertion):
    assertion( "Appending the events used for skipping corrections" )
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

    # Fifth - Mark the next event as a skip event
    input_history.mark_next_as_skip()

    # Sixth - Add the skip correction event
    input_history.add_event(InputEventType.CORRECTION, ["this", "big", "word"], 3000)

    # Seventh - A target is found
    events = text_to_virtual_buffer_tokens("This", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Bird", "bird"))
    input_history.append_target_to_last_event(events)

    assertion( "    Should give the history two events", len(input_history.history) == 2)
    assertion( "    Should not detect a repetition", input_history.is_repetition() == False)
    assertion( "    Should transform the second correction as a skip correction", input_history.history[-1].type == InputEventType.SKIP_CORRECTION)

def test_skip_partial_self_repair_flow(assertion):
    assertion( "Appending the events used for skipping partial self repairs" )
    input_history = get_input_history()

    # First - Add the marithime insert event
    input_history.add_event(InputEventType.MARITHIME_INSERT, ["this", "big", "word"], 1500)

    # Second - The insert gets transformed to camel case
    events = text_to_virtual_buffer_tokens("this", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Word", "word"))
    input_history.append_insert_to_last_event(events)
    
    # Third - Add the insert event
    input_history.add_event(InputEventType.INSERT, ["thisBigWord"], 1500)

    # Fourth - Add another marithime insert event
    input_history.add_event(InputEventType.MARITHIME_INSERT, ["big", "werd", "that"], 2500)

    # Fifth - A partial self repair is detected
    input_history.add_event(InputEventType.PARTIAL_SELF_REPAIR, ["big", "werd", "that"], 2600)
    events = text_to_virtual_buffer_tokens("Big", "big")
    events.extend( text_to_virtual_buffer_tokens("Werd", "werd"))
    input_history.append_target_to_last_event(events)

    # Sixth - The insert gets transformed to camel case by the formatter
    events = text_to_virtual_buffer_tokens("Big", "big")
    events.extend( text_to_virtual_buffer_tokens("Werd", "werd"))
    events.extend( text_to_virtual_buffer_tokens("That", "that"))
    input_history.append_insert_to_last_event(events)

    # Seventh - An insert event is added
    input_history.add_event(InputEventType.INSERT, ["BigWerdThat"], 2700)
    assertion( "    Should only have two events appended", len(input_history.history) == 2)
    assertion( input_history.history )

    # Eight - Mark the next event as a skip event
    input_history.mark_next_as_skip()

    # Ninth - Add another marithime insert event
    input_history.add_event(InputEventType.MARITHIME_INSERT, ["big", "werd", "that"], 4000)
    assertion( "    Should not clear the next skip state after the marithime insert was given", input_history.is_skip_event() == True)

    # Tenth - A full skip self repair is detected
    input_history.add_event(InputEventType.SELF_REPAIR, ["big", "werd", "that"], 4100)
    events = text_to_virtual_buffer_tokens("Big", "big")
    events.extend( text_to_virtual_buffer_tokens("Werd", "werd"))
    events.extend( text_to_virtual_buffer_tokens("That", "that"))
    input_history.append_target_to_last_event(events)
    assertion( "    Should clear the next skip state after the self repair was given", input_history.is_skip_event() == False)

    # Eleventh - The insert gets transformed to camel case by the formatter
    events = text_to_virtual_buffer_tokens("Big", "big")
    events.extend( text_to_virtual_buffer_tokens("Werd", "werd"))
    events.extend( text_to_virtual_buffer_tokens("That", "that"))
    input_history.append_insert_to_last_event(events)

    # Twelfth - Add the changed insert event ( Old text followed by new text )
    input_history.add_event(InputEventType.INSERT, "BigWordBigWerdThat", 4200)
    assertion( "    Should give the history three events", len(input_history.history) == 3)
    assertion( "    should not detect a repetition", input_history.is_repetition() == False)
    assertion( "    should transform the second self repair as a skip self repair", input_history.history[-1].type == InputEventType.SKIP_SELF_REPAIR)

def test_skip_full_self_repair_flow(assertion):
    assertion( "Appending the events used for skipping full self repairs" )
    input_history = get_input_history()

    # First - Add the marithime insert event
    input_history.add_event(InputEventType.MARITHIME_INSERT, ["this", "big", "word"], 1500)

    # Second - The insert gets transformed to camel case
    events = text_to_virtual_buffer_tokens("this", "this")
    events.extend( text_to_virtual_buffer_tokens("Big", "big"))
    events.extend( text_to_virtual_buffer_tokens("Word", "word"))
    input_history.append_insert_to_last_event(events)
    
    # Third - Add the insert event
    input_history.add_event(InputEventType.INSERT, ["thisBigWord"], 1500)

    # Fourth - Add another marithime insert event
    input_history.add_event(InputEventType.MARITHIME_INSERT, ["big", "werd"], 2500)

    # Fifth - A partial self repair is detected
    input_history.add_event(InputEventType.SELF_REPAIR, ["big", "werd"], 2600)
    events = text_to_virtual_buffer_tokens("Big", "big")
    events.extend( text_to_virtual_buffer_tokens("Werd", "werd"))
    input_history.append_target_to_last_event(events)

    # Sixth - The insert gets transformed to camel case by the formatter
    events = text_to_virtual_buffer_tokens("Big", "big")
    events.extend( text_to_virtual_buffer_tokens("Werd", "werd"))
    input_history.append_insert_to_last_event(events)

    # Seventh - An insert event is added
    input_history.add_event(InputEventType.INSERT, ["BigWerd"], 2700)
    assertion( "    Should only have two events appended", len(input_history.history) == 2)
    assertion( input_history.history )

    # Eight - Mark the next event as a skip event
    input_history.mark_next_as_skip()

    # Ninth - Add another marithime insert event
    input_history.add_event(InputEventType.MARITHIME_INSERT, ["big", "werd"], 4000)
    assertion( "    Should not clear the next skip state after the marithime insert was given", input_history.is_skip_event() == True)

    # Tenth - A full skip self repair is detected
    input_history.add_event(InputEventType.SELF_REPAIR, ["big", "werd"], 4100)
    events = text_to_virtual_buffer_tokens("Big", "big")
    events.extend( text_to_virtual_buffer_tokens("Werd", "werd"))
    input_history.append_target_to_last_event(events)
    assertion( "    Should clear the next skip state after the self repair was given", input_history.is_skip_event() == False)

    # Eleventh - The insert gets transformed to camel case by the formatter
    events = text_to_virtual_buffer_tokens("Big", "big")
    events.extend( text_to_virtual_buffer_tokens("Werd", "werd"))
    input_history.append_insert_to_last_event(events)

    # Twelfth - Add the changed insert event ( Old text followed by new text )
    input_history.add_event(InputEventType.INSERT, "BigWordBigWerd", 4200)
    assertion( "    Should give the history three events", len(input_history.history) == 3)
    assertion( "    should not detect a repetition", input_history.is_repetition() == False)
    assertion( "    should transform the second self repair as a skip self repair", input_history.history[-1].type == InputEventType.SKIP_SELF_REPAIR)

suite = create_test_suite("Appending skip events to the history that shouldn't result in more than one issue")
suite.add_test(test_skip_non_skippable_events_flow)
suite.add_test(test_skip_correction_flow) 
suite.add_test(test_skip_partial_self_repair_flow)
suite.add_test(test_skip_full_self_repair_flow) 