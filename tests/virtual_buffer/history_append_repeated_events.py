from ...virtual_buffer.input_history import InputHistory, InputEventType
from ...virtual_buffer.typing import VirtualBufferToken
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite

def get_input_history() -> InputHistory:
    return InputHistory()

repeated_events_list = [
    "marithime_insert",
    "insert",
    "insert_character",
    "remove",
    "select",
    "correction",
    "skip_correction",
    # "partial_self_repair", - By definition cannot repeat after one another
    "skip_self_repair",
    "self_repair",
    "navigation",
    "exit"
]

def apply_event(input_history, event_type, phrases):
    input_event_type = InputEventType.INSERT
    if event_type == "insert_character":
        input_event_type = InputEventType.INSERT_CHARACTER
    if event_type == "marithime_insert":
        input_event_type = InputEventType.MARITHIME_INSERT
    if event_type == "remove":
        input_event_type = InputEventType.REMOVE
    if event_type == "select":
        input_event_type = InputEventType.SELECT
    if event_type == "correction":
        input_event_type = InputEventType.CORRECTION
    elif event_type == "skip_correction":
        input_event_type = InputEventType.SKIP_CORRECTION
    elif event_type == "self_repair":
        input_event_type = InputEventType.SELF_REPAIR
    elif event_type == "skip_self_repair":
        input_event_type = InputEventType.SKIP_SELF_REPAIR
    elif event_type == "navigation":
        input_event_type = InputEventType.NAVIGATION
    elif event_type == "exit":
        input_event_type = InputEventType.EXIT

    input_history.add_event(input_event_type, phrases)

def test_append_exact_repeating_events(assertion):
    for repeated_event in repeated_events_list:
        assertion( "Appending the same " + repeated_event + " event after one another")
        input_history = get_input_history()
        apply_event(input_history, repeated_event, ["this"])
        apply_event(input_history, repeated_event, ["this"])
        assertion( "    Should give the history two events", len(input_history.history) == 2)
        assertion( "    Should detect a repetition", input_history.is_repetition() == True)

def test_append_dissimilar_repeating_events(assertion):
    for repeated_event in repeated_events_list:
        assertion( "Appending different " + repeated_event + " events after one another")
        input_history = get_input_history()
        apply_event(input_history, repeated_event, ["this", "machine"])
        apply_event(input_history, repeated_event, ["that", "machine"])
        assertion( "    Should give the history two events", len(input_history.history) == 2)
        assertion( "    Should detect a repetition", input_history.is_repetition() == False)

def test_repetition_count(assertion):
    for repeated_event in repeated_events_list:
        assertion( "Appending the same " + repeated_event + " event after one another")
        input_history = get_input_history()
        apply_event(input_history, repeated_event, ["this"])
        apply_event(input_history, repeated_event, ["this"])
        assertion( "    Should detect a repetition", input_history.is_repetition() == True)
        assertion( "    Should count a single repetition", input_history.get_repetition_count() == 1)
        apply_event(input_history, repeated_event, ["this"])
        assertion( "Appending it again")
        assertion( "    Should count two repetitions", input_history.get_repetition_count() == 2)

def test_marthime_insert_repetition(assertion):
    input_history = get_input_history()
    assertion( "Appending a self repair after the exact same marthime insert")
    apply_event(input_history, "marithime_insert", ["testing"])
    apply_event(input_history, "marithime_insert", ["testing"])
    apply_event(input_history, "self_repair", ["testing"])
    events = text_to_virtual_buffer_tokens("Testink", "testing")
    input_history.append_target_to_last_event(events, before=True)
    assertion( "    Should count a single repetition", input_history.get_repetition_count() == 1)

    assertion( "Appending another same marthime insert that can become a self repair")
    apply_event(input_history, "marithime_insert", ["testing"])
    assertion( "    Should not count a second repetition yet", input_history.get_repetition_count() == 1)
    apply_event(input_history, "self_repair", ["testing"])
    events = text_to_virtual_buffer_tokens("Testinh", "testinh")
    input_history.append_target_to_last_event(events, before=True)
    assertion( "    Should count a second repetition after the event has changed to self repair", input_history.get_repetition_count(True) == 2)

    assertion( "Appending a different marthime insert that can become a self repair")
    apply_event(input_history, "marithime_insert", ["besting"])
    assertion( "    Should reset the repetition count", input_history.get_repetition_count() == 0)
    assertion( input_history.history )
    assertion( input_history.get_repetition_count() )

suite = create_test_suite("Appending same events to the history")
suite.add_test(test_append_exact_repeating_events)
suite.add_test(test_append_dissimilar_repeating_events)
suite.add_test(test_repetition_count)
suite.add_test(test_marthime_insert_repetition)