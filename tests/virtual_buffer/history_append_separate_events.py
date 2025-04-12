from ...virtual_buffer.input_history import InputHistory, InputEventType
from ...virtual_buffer.typing import VirtualBufferToken
from ...virtual_buffer.indexer import text_to_virtual_buffer_tokens
from ..test import create_test_suite

def get_input_history() -> InputHistory:
    return InputHistory()

non_related_events_transition_table = [
    # Marithime insert event
    # ["marithime_insert", "marithime_insert"], - Possible repetition
    # ["marithime_insert", "insert"], - Insert followed by marithime insert can be a part of the marithime insert evet
    ["marithime_insert", "insert_character"],
    ["marithime_insert", "remove"],
    ["marithime_insert", "select"],
    ["marithime_insert", "correction"],
    # ["marithime_insert", "self_repair"], - Possibly included in marithime insert
    # ["marithime_insert", "partial_self_repair"], - Possibly included in marithime insert
    ["marithime_insert", "navigation"],
    ["marithime_insert", "exit"],

    # Insert event
    ["insert", "marithime_insert"],
    # ["insert", "insert"], - Possible repetition
    # ["insert", "insert_character"], - Insert character can be a part of an insert statement
    ["insert", "remove"],
    ["insert", "select"],
    ["insert", "correction"],
    ["insert", "self_repair"],
    ["insert", "partial_self_repair"],
    ["insert", "navigation"],
    ["insert", "exit"],

    # Insert character event
    ["insert_character", "marithime_insert"],
    ["insert_character", "insert"],
    # ["insert_character", "insert_character"], - Possible repetition
    ["insert_character", "remove"],
    ["insert_character", "select"],
    ["insert_character", "correction"],
    ["insert_character", "self_repair"],
    ["insert_character", "partial_self_repair"],
    ["insert_character", "navigation"],
    ["insert_character", "exit"],

    # Remove event
    ["remove", "marithime_insert"],
    ["remove", "insert"],
    ["remove", "insert_character"],
    #["remove", "remove"], - Possible repetition
    ["remove", "select"],
    ["remove", "correction"],
    ["remove", "self_repair"],
    ["remove", "partial_self_repair"],
    ["remove", "navigation"],
    ["remove", "exit"],

    # Select event
    ["select", "marithime_insert"],
    ["select", "insert"],
    ["select", "insert_character"],
    ["select", "remove"],
    #["select", "select"], - Possible repetition
    ["select", "correction"],
    ["select", "self_repair"],
    ["select", "partial_self_repair"],
    ["select", "navigation"],
    ["select", "exit"],

    # Correction event
    ["correction", "marithime_insert"],
    # ["correction", "insert"], - Possible part of correction event
    ["correction", "insert_character"],
    # ["correction", "remove"], - Possible part of correction event
    # ["correction", "select"], - Possible part of correction event
    # ["correction", "correction"], - Possible repetition
    ["correction", "self_repair"],
    ["correction", "partial_self_repair"],
    ["correction", "navigation"],
    ["correction", "exit"],

    # Skip correction event
    ["skip_correction", "marithime_insert"],
    ["skip_correction", "insert"],
    ["skip_correction", "insert_character"],
    ["skip_correction", "remove"],
    # ["skip_correction", "select"], - Possible part of skip_correction event
    # ["skip_correction", "correction"], - Possible repetition
    # ["skip_correction", "skip_correction"], - Possible repetition
    ["skip_correction", "self_repair"],
    ["skip_correction", "partial_self_repair"],
    ["skip_correction", "navigation"],
    ["skip_correction", "exit"],

    # Partial self repair event
    ["partial_self_repair", "marithime_insert"],
    # ["partial_self_repair", "insert"], - Possible part of partial_self_repair event
    ["partial_self_repair", "insert_character"],
    # ["partial_self_repair", "remove"], - Possible part of parial_self_repair event
    # ["partial_self_repair", "select"], - Possible part of partial_self_repair event
    ["partial_self_repair", "correction"],
    # ["partial_self_repair", "self_repair"], - Possible repetition
    ["partial_self_repair", "partial_self_repair"], # NO REPETITION - Since this can only happen if we have partial rather than complete matches
    ["partial_self_repair", "navigation"],
    ["partial_self_repair", "exit"],

    # Self repair event
    ["self_repair", "marithime_insert"],
    # ["self_repair", "insert"], - Possible part of self_repair event
    ["self_repair", "insert_character"],
    # ["self_repair", "remove"], - Possible part of self_repair event
    # ["self_repair", "select"], - Possible part of self_repair event
    ["self_repair", "correction"],
    # ["self_repair", "self_repair"], - Possible repetition
    ["self_repair", "partial_self_repair"],
    ["self_repair", "navigation"],
    ["self_repair", "exit"],

    ["skip_self_repair", "marithime_insert"],
    # ["skip_self_repair", "insert"], - Possible part of skip_self_repair event
    ["skip_self_repair", "insert_character"],
    # ["skip_self_repair", "remove"], - Possible part of skip_self_repair event
    # ["skip_self_repair", "select"], - Possible part of skip_self_repair event
    ["skip_self_repair", "correction"],
    ["skip_self_repair", "self_repair"],
    ["skip_self_repair", "partial_self_repair"],
    ["skip_self_repair", "navigation"],
    ["skip_self_repair", "exit"],

    # Navigation event
    ["navigation", "marithime_insert"],
    ["navigation", "insert"],
    ["navigation", "insert_character"],
    ["navigation", "remove"],
    ["navigation", "select"],
    ["navigation", "correction"],
    ["navigation", "self_repair"],
    ["navigation", "partial_self_repair"],
    # ["navigation", "navigation"], # Possible repetition
    ["navigation", "exit"],
]

def apply_event(input_history, event_type):
    input_event_type = InputEventType.INSERT
    phrase = ["that which"]
    if event_type == "insert_character":
        input_event_type = InputEventType.INSERT_CHARACTER
        phrase = ["air"]
    if event_type == "marithime_insert":
        input_event_type = InputEventType.MARITHIME_INSERT
        phrase = ["that which"]
    if event_type == "remove":
        input_event_type = InputEventType.REMOVE
        phrase = []
    if event_type == "select":
        input_event_type = InputEventType.SELECT
        phrase = ["before"]
    if event_type == "correction":
        input_event_type = InputEventType.CORRECTION
        phrase = ["before", "that"]
    elif event_type == "skip_correction":
        input_event_type = InputEventType.SKIP_CORRECTION
        phrase = ["before", "that"]
    elif event_type == "partial_self_repair":
        input_event_type = InputEventType.PARTIAL_SELF_REPAIR
        phrase = ["before", "this", "thing", "that"]
    elif event_type == "self_repair":
        input_event_type = InputEventType.SELF_REPAIR
        phrase = ["before", "this"]
    elif event_type == "skip_self_repair":
        input_event_type = InputEventType.SKIP_SELF_REPAIR
        phrase = ["before", "this"]
    elif event_type == "navigation":
        input_event_type = InputEventType.NAVIGATION
        phrase = ["before"]
    elif event_type == "exit":
        phrase = []
        input_event_type = InputEventType.EXIT

    input_history.add_event(input_event_type, phrase)

def test_append_non_related_events(assertion):
    for non_related_events in non_related_events_transition_table:
        assertion( "Adding an " + non_related_events[0] + " event and a " + non_related_events[1] + " event")        
        input_history = get_input_history()
        apply_event(input_history, non_related_events[0])
        apply_event(input_history, non_related_events[1])
        assertion( "    Should give the history two events", len(input_history.history) == 2)
        assertion( "    Should not detect a repetition", input_history.is_repetition() == False)

suite = create_test_suite("Appending non-related events")
suite.add_test(test_append_non_related_events)
