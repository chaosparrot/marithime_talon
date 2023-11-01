from ..input_history import InputHistoryManager
from ..input_history_typing import InputHistoryEvent
from ...utils.test import create_test_suite

def get_empty_ihm() -> InputHistoryManager:
    return InputHistoryManager()

def get_filled_ihm() -> InputHistoryManager:
    input_history = get_empty_ihm()
    input_history.insert_input_events(input_history.text_to_input_history_events("This ", "This"))
    input_history.insert_input_events(input_history.text_to_input_history_events("is ", "is"))
    input_history.insert_input_events(input_history.text_to_input_history_events("a ", "a"))
    input_history.insert_input_events(input_history.text_to_input_history_events("test", "test"))
    input_history.insert_input_events(input_history.text_to_input_history_events(".or", "or"))    
    return input_history

def test_detect_merge_in_between_events(assertion):
    assertion( "Detecting merge strategies for inserting input events in between events" )
    previous_no_merge = get_filled_ihm().detect_merge_strategy(0, 0, InputHistoryEvent("Ask ", "ask", ""))
    assertion( "    Should always append before the first event if the event cannot be merged", previous_no_merge == (0, -1, -1))
    previous_no_merge_middle = get_filled_ihm().detect_merge_strategy(1, 0, InputHistoryEvent("ask ", "ask", ""))
    assertion( "    Should always append before the second event if the event cannot be merged", previous_no_merge_middle == (0, -1, -1))
    current_append_after = get_filled_ihm().detect_merge_strategy(0, 5, InputHistoryEvent("ask ", "ask", ""))
    assertion( "    Should always append after the first event if the event cannot be merged", current_append_after == (-1, 0, -1))
    current_middle_append_after = get_filled_ihm().detect_merge_strategy(1, 3, InputHistoryEvent("ask ", "ask", ""))
    assertion( "    Should merge append after the second event if the event cannot be merged", current_middle_append_after == (-1, 0, -1))
    current_first_merge = get_filled_ihm().detect_merge_strategy(0, 0, InputHistoryEvent("Ask", "ask", ""))
    assertion( "    Should merge with the first event if the event can be merged at the start", current_first_merge == (-1, 1, -1))
    second_first_merge = get_filled_ihm().detect_merge_strategy(1, 0, InputHistoryEvent("Ask", "ask", ""))
    assertion( "    Should merge with the second event if the event can be merged at the start", second_first_merge == (-1, 1, -1))
    fourth_first_merge = get_filled_ihm().detect_merge_strategy(3, 0, InputHistoryEvent("Ask", "ask", ""))
    assertion( "    Should merge with the current event if the event can be merged at the start", fourth_first_merge == (-1, 1, -1))
    third_last_merge = get_filled_ihm().detect_merge_strategy(2, 2, InputHistoryEvent("Ask", "ask", ""))
    assertion( "    Should merge with the final event if the event can be merged at the end of the current event", third_last_merge == (-1, -1, 1))
    fourth_last_merge = get_filled_ihm().detect_merge_strategy(3, 5, InputHistoryEvent("Ask", "ask", ""))
    assertion( "    Should merge with the current event if the event can be merged at the end", fourth_last_merge == (-1, 1, -1))
    final_last_merge = get_filled_ihm().detect_merge_strategy(4, 3, InputHistoryEvent("Ask", "ask", ""))
    assertion( "    Should merge with the final event if the event can be merged at the end", final_last_merge == (-1, 1, -1)) 

def test_detect_merge_in_middle_of_events(assertion):
    assertion( "Detecting merge strategies for inserting input events in the middle of events" )
    first_merge_middle = get_filled_ihm().detect_merge_strategy(0, 1, InputHistoryEvent("ask", "ask", ""))
    assertion( "    Should merge with the first event if the event can be merged from both sides", first_merge_middle == (-1, 1, -1))
    current_merge_middle = get_filled_ihm().detect_merge_strategy(1, 1, InputHistoryEvent("ask", "ask", ""))
    assertion( "    Should merge with the current event if the event can be merged from both sides", current_merge_middle == (-1, 1, -1))
    final_merge_middle = get_filled_ihm().detect_merge_strategy(4, 2, InputHistoryEvent("ask", "ask", ""))
    assertion( "    Should merge with the final event if the event can be merged from both sides", final_merge_middle == (-1, 1, -1))
    first_split_left = get_filled_ihm().detect_merge_strategy(0, 1, InputHistoryEvent(" ask", "ask", ""))
    assertion( "    Should split left of the first event if the event can only be merged from the right", first_split_left == (-1, 2, -1))
    current_split_left = get_filled_ihm().detect_merge_strategy(1, 1, InputHistoryEvent(" ask", "ask", ""))
    assertion( "    Should split left of the current event if the event can only be merged from the right", current_split_left == (-1, 2, -1))
    final_split_left = get_filled_ihm().detect_merge_strategy(4, 1, InputHistoryEvent(" ask", "ask", ""))
    assertion( "    Should split left of the final event if the event can only be merged from the right", final_split_left == (-1, 2, -1))
    first_split_right = get_filled_ihm().detect_merge_strategy(0, 1, InputHistoryEvent("ask ", "ask", ""))
    assertion( "    Should split right of the first event if the event can only be merged from the left", first_split_right == (-1, 3, -1))
    current_split_right = get_filled_ihm().detect_merge_strategy(1, 1, InputHistoryEvent("ask ", "ask", ""))
    assertion( "    Should split right of the current event if the event can only be merged from the left", current_split_right == (-1, 3, -1))
    final_split_right = get_filled_ihm().detect_merge_strategy(4, 2, InputHistoryEvent("ask ", "ask", ""))
    assertion( "    Should split right of the final event if the event can only be merged from the left", final_split_right == (-1, 3, -1))
    first_split_both = get_filled_ihm().detect_merge_strategy(0, 1, InputHistoryEvent(" ask ", "ask", ""))
    assertion( "    Should split on both sides of the first event if the event cannot be merged", first_split_both == (-1, 4, -1))
    current_split_both = get_filled_ihm().detect_merge_strategy(1, 1, InputHistoryEvent(" ask ", "ask", ""))
    assertion( "    Should split on both sides of the current event if the event cannot be merged", current_split_both == (-1, 4, -1))
    final_split_both = get_filled_ihm().detect_merge_strategy(4, 1, InputHistoryEvent(" ask ", "ask", ""))
    assertion( "    Should split on both sides of the final event if the event cannot be merged", final_split_both == (-1, 4, -1))

suite = create_test_suite("Merge and split detection")
suite.add_test(test_detect_merge_in_between_events)
suite.add_test(test_detect_merge_in_middle_of_events)