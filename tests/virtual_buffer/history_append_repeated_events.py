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

suite = create_test_suite("Appending same events")
suite.add_test(test_append_exact_repeating_events)
suite.add_test(test_append_dissimilar_repeating_events)
