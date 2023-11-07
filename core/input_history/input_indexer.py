from .input_history_typing import InputHistoryEvent
from .formatters.text_formatter import TextFormatter
import re
from typing import List
from .formatters.formatters import DICTATION_FORMATTERS
from .cursor_position_tracker import _CURSOR_MARKER

def text_to_phrase(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", ' ', text.replace("'", "").replace("’", "")).lower().split()).strip()

def normalize_text(text: str) -> str:
    return re.sub(r"[^\w\s]", ' ', text).replace("\n", " ")

# Transform raw text to input history events
def text_to_input_history_events(text: str, phrase: str = None, format: str = None) -> List[InputHistoryEvent]:
    lines = text.splitlines()
    if text.endswith("\n"):
        lines.append("")
    events = []
    if len(lines) == 1:
        event = InputHistoryEvent(text, "", "" if format is None else format)
        if phrase is not None:
            event.phrase = phrase
        else:
            event.phrase = text_to_phrase(text)
        return [event]
        # If there are line endings, split them up properly
    else:
        for line_index, line in enumerate(lines):
            event = InputHistoryEvent(line + "\n" if line_index < len(lines) - 1 else line, "", "" if format is None else format)
            event.phrase = text_to_phrase(line)
            events.append(event)
        return events

# Make sure the line numbers and character counts from the end of the line are properly kept
def reindex_events(input_history_events: List[InputHistoryEvent]) -> List[InputHistoryEvent]:
    length = len(input_history_events)
    if length == 0:
        return []

    # First sync the line counts
    line_index = 0
    previous_line_index = input_history_events[0].line_index
    new_events = []
    for index, event in enumerate(input_history_events):
        event.line_index = line_index
        new_events.append(event)
        if event.text.endswith("\n"):
            line_index += 1

    # Then sync the character count
    previous_line_index = new_events[-1].line_index
    previous_line_end_count = 0
    for index, event in enumerate(reversed(new_events)):
        true_index = length - 1 - index
        if event.line_index == previous_line_index:
            new_events[true_index].index_from_line_end = previous_line_end_count
        else:
            previous_line_end_count = 0
            new_events[true_index].index_from_line_end = 0
            previous_line_index = event.line_index
        previous_line_end_count += len(event.text.replace("\n", ""))

    return new_events

# Class used to split off text into properly matched input text events
class InputIndexer:

    default_formatter: TextFormatter = None
    formatters = []

    def __init__(self, formatters: List[TextFormatter] = []):
        self.default_formatter = DICTATION_FORMATTERS['EN']
        self.formatters = formatters

    def set_default_formatter(self, formatter: TextFormatter = None):
        if formatter:
            self.default_formatter = formatter

    # Split raw (multi-line) text to input history events
    def index_text(self, text: str) -> List[InputHistoryEvent]:
        text = text.replace(_CURSOR_MARKER, '')

        # TODO - Do index matching based on if we are dealing with a regular or a programming language
        # We are now just using the default formatter instead
        words = self.default_formatter.words_to_format(self.default_formatter.format_to_words(text))
        
        input_history_events = []
        for word in words:
            input_history_events.extend(text_to_input_history_events(word, None, self.default_formatter.name))

        return reindex_events(input_history_events)