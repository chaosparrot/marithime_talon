from enum import Enum
from typing import List
from dataclasses import dataclass
from .typing import VirtualBufferToken
import time

# All kinds of events that can be applied to the input history
# To detect a transition or an input fix
class InputEventType(Enum):
    MARITHIME_INSERT = "marithime_insert" # DONE
    INSERT = "insert" # DONE
    INSERT_CHARACTER = "insert_character" # DONE
    REMOVE = "remove"
    SELECT = "select" # DONE
    CORRECTION = "correction" # DONE
    SKIP_CORRECTION = "skip_correction" # DONE
    PARTIAL_SELF_REPAIR = "partial_self_repair" # DONE
    SKIP_SELF_REPAIR = "skip_self_repair" # DONE
    SELF_REPAIR = "self_repair" # DONE
    NAVIGATION = "navigation" # DONE
    EXIT = "exit" # DONE

@dataclass
class InputEvent:
    timestamp_ms: int = -1
    type: InputEventType = InputEventType.INSERT
    phrases: List[str] = None
    target: List[VirtualBufferToken] = None
    insert: List[VirtualBufferToken] = None

# Class to maintain a list of input history items
# For a single virtual buffer to use in checking
# The 
class InputHistory:    
    history: List[InputEvent] = None
    mark_as_skip: bool = False
    repetition_count: int = 0

    def __init__(self):
        self.history = []
        self.mark_as_skip = False
        self.repetition_count = 0

    def add_event(self, type: InputEventType, phrases: List[str] = None, timestamp_ms: int = -1):
        if timestamp_ms == -1:
            timestamp_ms = round(time.time() * 1000)

        # Transform to skip event
        if self.mark_as_skip:

            # Do not clear marithime inserts as they can result in self repairs
            if type != InputEventType.MARITHIME_INSERT:
                self.mark_next_as_skip(False)

            if type == InputEventType.CORRECTION:
                type = InputEventType.SKIP_CORRECTION
            elif type == InputEventType.SELF_REPAIR:
                type = InputEventType.SKIP_SELF_REPAIR

        event = InputEvent(timestamp_ms, type, phrases)
        print( "ADD EVENT", event )

        if self.should_update_event(event):
            self.history[-1].timestamp_ms = event.timestamp_ms
            self.history[-1].type = event.type

            if self.is_repetition():
                self.repetition_count += 1
                print( "INCREASING REPETITION COUNT UPDATE!", event.type, self.repetition_count )

        elif self.should_transition(event):
            last_event = self.get_last_event()

            self.history.append(event)
            self.history = self.history[-60:] # Do not make the history balloon too much

            if self.is_repetition():
                self.repetition_count += 1
                print( "INCREASING REPETITION COUNT TRANSITION!", event.type, self.repetition_count )                
            else:
                # Reset the event count only if the phrases do not match up directly
                # And if we aren't in an event that can still transition to another event
                if last_event is not None and ("".join(event.phrases) != "".join(last_event.phrases) or event.type != InputEventType.MARITHIME_INSERT):
                    self.repetition_count = 0
                
        # Reset the events timestamp if we do not have a transition
        else:
            self.history[-1].timestamp_ms = event.timestamp_ms

    # Whether the new input event is part of the current input event
    # A correction contains a navigation, selection and an insert in rapid succession for instance
    def should_transition(self, event: InputEvent):
        transitioning = True
        if len(self.history) > 0:
            last_event = self.get_last_event()
            last_event_ts = last_event.timestamp_ms
            last_event_type = last_event.type
            if event.timestamp_ms - last_event_ts > 500:
                transitioning = True

            # When dealing with an insert, it can be a part of a bigger combined action being executed
            # If the insert of the previous insert is empty
            elif event.type == InputEventType.INSERT and last_event_type in [
                    InputEventType.MARITHIME_INSERT,
                    InputEventType.SELF_REPAIR,
                    InputEventType.SKIP_SELF_REPAIR,
                    InputEventType.PARTIAL_SELF_REPAIR,
                    InputEventType.CORRECTION
                ] and last_event.insert is None:
                transitioning = False

            # When dealing with a remove, it can be a part of a bigger combined action being executed
            # If the insert of the previous insert is empty
            elif event.type == InputEventType.REMOVE and last_event_type in [
                    InputEventType.SELF_REPAIR,
                    InputEventType.SKIP_SELF_REPAIR,
                    InputEventType.PARTIAL_SELF_REPAIR,
                    InputEventType.CORRECTION
                ] and last_event.insert is None:
                transitioning = False

            # If we have a remove event added as a part of a marithime insert event
            # We should check if we have a selection beforehand, as that removes the target
            elif event.type == InputEventType.REMOVE and last_event_type == InputEventType.MARITHIME_INSERT:
                if len(self.history) > 1 and self.history[-2].type == InputEventType.SELECT:
                    transitioning = False

            # If we have a remove event added that removes a selection as well as more text
            # We should combine them together
            elif event.type == InputEventType.REMOVE and last_event_type == InputEventType.REMOVE and \
                last_event.target is not None and event.timestamp_ms - last_event_ts < 100:
                if len(self.history) > 1 and self.history[-2].type == InputEventType.SELECT:
                    transitioning = False

            # If we have a marithime insert event added as a part of a correction event with the same phrases
            elif event.type == InputEventType.MARITHIME_INSERT and last_event_type == InputEventType.CORRECTION:
                if "".join(last_event.phrases) == "".join(event.phrases):
                    transitioning = False

        return transitioning

    # Whether the new input event should replace the previous input event type
    # As the first event indicates a new event at a later time
    def should_update_event(self, event: InputEvent):
        updating = False
        if len(self.history) > 0:
            last_event = self.get_last_event()
            last_event_ts = last_event.timestamp_ms
            if event.timestamp_ms - last_event_ts > 500:
                updating = False

            # When dealing with a marithime insert,
            # It can transition into a different history event based on the event happening right after
            elif event.type == InputEventType.SELF_REPAIR and last_event.type == InputEventType.MARITHIME_INSERT and \
                    "".join(last_event.phrases) == "".join(event.phrases):
                updating = True
            elif event.type in [
                    InputEventType.PARTIAL_SELF_REPAIR,
                    InputEventType.SKIP_SELF_REPAIR
                ] and last_event.type == InputEventType.MARITHIME_INSERT and \
                    "".join(event.phrases).endswith("".join(last_event.phrases)):
                updating = True

        return updating

    def get_first_target_from_event(self) -> List[VirtualBufferToken]:
        if len(self.history) == 0:
            return []
        if self.repetition_count > 0 and len(self.history) > self.repetition_count:
            offset = 1

            # For a self repair cycle, the starting point is a marithime insert or a regular insert which does not have a target
            # In that case, check the event happening right after that for the target
            if self.history[-(self.repetition_count + 1)].type in [InputEventType.MARITHIME_INSERT, InputEventType.INSERT]:
                offset = 0
            return self.history[-(self.repetition_count + offset)].target
        else:
            return self.get_last_event().target

    def flush_history(self):
        self.history = []
        self.repetition_count = 0

    def mark_next_as_skip(self, mark_next: bool = True):
        self.mark_as_skip = mark_next

    def is_skip_event(self) -> bool:
        return self.mark_as_skip

    def append_phrases_to_last_event(self, phrases: List[str]):
        if len(self.history) > 0:
            self.history[-1].phrases = phrases
    
    def append_target_to_last_event(self, target: List[VirtualBufferToken], before: bool = False):
        if len(self.history) > 0 and "".join([token.text for token in target]) != "":
            if self.history[-1].target is None:
                self.history[-1].target = target

            # Append to the left or to the right of the existing target
            else:
                last_event_target = self.history[-1].target

                new_target = []

                # When the new target is larger than the existing target, naively assume that they don't include duplicates
                if len(target) > len(last_event_target):
                    new_target = target

                else:
                    for target_token_index, target_token in enumerate(target):
                        if before:

                            # Only add the event before the target if it doesn't exactly match the existing target
                            # To ensure we don't get duplicates
                            if not (target_token.line_index == last_event_target[target_token_index].line_index and \
                                target_token.index_from_line_end == last_event_target[target_token_index].index_from_line_end and \
                                len(target_token.text) == len(last_event_target[target_token_index].text)):
                                new_target.append(target_token)
                        
                        elif not before:
                            target_after_index = -len(target) + target_token_index

                            # Only add the event afer the target if it doesn't exactly match the existing target
                            # To ensure we don't get duplicates
                            if not (target_token.line_index == last_event_target[target_after_index].line_index and \
                                target_token.index_from_line_end == last_event_target[target_after_index].index_from_line_end and \
                                len(target_token.text) == len(last_event_target[target_after_index].text)):
                                new_target.append(target_token)

                if before:
                    new_target.extend(self.history[-1].target)
                    self.history[-1].target = new_target
                elif before == False:
                    self.history[-1].target.extend(new_target)
    
    def append_insert_to_last_event(self, insert: List[VirtualBufferToken]):
        if len(self.history) > 0:
            self.history[-1].insert = insert
    
    # Check if this is an exact repetition of a previous event
    # To see if we need to 
    def is_repetition(self):
        is_repeated_event = False
        if len(self.history) > 1:
            current_event = self.history[-1]
            previous_event = self.history[-2]

            is_repeated_event = current_event.type == previous_event.type and "".join(current_event.phrases) == "".join(previous_event.phrases)
            if is_repeated_event:

                # Partially repeated events cannot follow one another up
                # As by definition if you repeat a partial self repair, it would create a full self repair
                if current_event.type == InputEventType.PARTIAL_SELF_REPAIR and previous_event.type == InputEventType.PARTIAL_SELF_REPAIR:
                    is_repeated_event = False
        return is_repeated_event

    def get_repetition_count(self):
        return self.repetition_count
    
    def count_remaining_single_character_presses(self) -> int:
        single_character_presses = 0
        index = 0
        while abs(index) < len(self.history):
            index -= 1

            # Only count single character presses if we are dealing with repeated insert character and remove events
            # As any other event interupts the flow for single character inputting and is no longer relevant to the user
            if self.history[index].type not in [InputEventType.REMOVE, InputEventType.INSERT_CHARACTER]:
                single_character_presses = 0
                break
            elif self.history[index].type == InputEventType.INSERT_CHARACTER:
                single_character_presses += len(self.history[index].insert)
            else:
                single_character_presses -= len([token.text for token in self.history[index].target])

        return max(single_character_presses, 0)

    def get_last_event(self) -> InputEvent:
        return self.history[-1] if len(self.history) > 0 else None