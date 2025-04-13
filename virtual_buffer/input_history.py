from enum import Enum
from typing import List
from dataclasses import dataclass
from .typing import VirtualBufferToken
import time

# All kinds of events that can be applied to the input history
# To detect a transition or an input fix
class InputEventType(Enum):
    MARITHIME_INSERT = "marithime_insert"
    INSERT = "insert"
    INSERT_CHARACTER = "insert_character"
    REMOVE = "remove"
    SELECT = "select"
    CORRECTION = "correction"
    SKIP_CORRECTION = "skip_correction"
    PARTIAL_SELF_REPAIR = "partial_self_repair"
    SKIP_SELF_REPAIR = "skip_self_repair"
    SELF_REPAIR = "self_repair"
    NAVIGATION = "navigation"
    EXIT = "exit"

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

    def __init__(self):
        self.history = []

    def add_event(self, type: InputEventType, phrases: List[str] = None, timestamp_ms: int = -1):
        if timestamp_ms == -1:
            timestamp_ms = round(time.time() * 1000)
        event = InputEvent(timestamp_ms, type, phrases)

        if self.should_update_event(event):
            self.history[-1].timestamp_ms = event.timestamp_ms
            self.history[-1].type = event.type

        elif self.should_transition(event):
            self.history.append(event)
            self.history = self.history[-60:] # Do not make the history balloon too much

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
            elif event.type == InputEventType.INSERT and last_event_type in [
                    InputEventType.MARITHIME_INSERT,
                    InputEventType.PARTIAL_SELF_REPAIR,
                    InputEventType.SKIP_SELF_REPAIR,
                    InputEventType.SELF_REPAIR,
                    InputEventType.CORRECTION
                ]:
                last_event_insert = last_event.insert

                if last_event_insert is not None and \
                    "".join(event.phrases) == "".join([token.text for token in last_event_insert]):
                    transitioning = False

        return transitioning

    # Whether the new input event should replace the previous input event type
    # As the first event indicates a new event at a later time
    def should_update_event(self, event: InputEvent):
        updating = False
        if len(self.history) > 0:
            last_event = self.get_last_event()
            last_event_ts = last_event.timestamp_ms
            last_event_type = last_event.type
            if event.timestamp_ms - last_event_ts > 500:
                updating = False

            # When dealing with a marithime insert,
            # It can transition into a different history event based on the event happening right after
            elif event.type in [
                    InputEventType.PARTIAL_SELF_REPAIR,
                    InputEventType.SKIP_SELF_REPAIR,
                    InputEventType.SELF_REPAIR
                ] and last_event.type == InputEventType.MARITHIME_INSERT and \
                    "".join(last_event.phrases) == "".join(event.phrases):
                updating = True

        return updating


    def flush_history(self):
        self.history = []

    def append_phrases_to_last_event(self, phrases: List[str]):
        if len(self.history) > 0:
            self.history[-1].phrases = phrases
    
    def append_target_to_last_event(self, target: List[VirtualBufferToken]):
        if len(self.history) > 0:
            self.history[-1].target = target
    
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

    def get_last_event(self) -> InputEvent:
        return self.history[-1] if len(self.history) > 0 else None