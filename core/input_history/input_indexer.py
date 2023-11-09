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
        new_events.append(InputHistoryEvent(event.text, event.phrase, event.format, line_index, event.index_from_line_end))

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
            new_events = text_to_input_history_events(word, None, self.default_formatter.name)
            for event in new_events:
                if len(input_history_events) == 0:
                    input_history_events.append(event)
                else:
                    event_text = normalize_text(event.text)
                    previous_event_text = normalize_text(input_history_events[-1].text)

                    # All the different cases in which we need to do merging
                    is_only_line_ending = event.text == "\n"
                    is_line_ending_word = event.text.endswith("\n") and len(event_text.replace(" ", "")) > 0
                    is_punctuation_only = event_text.replace(" ", "") == ""
                    can_merge_letters = not event_text.startswith(" ") and not previous_event_text.endswith(" ")
                    
                    if (is_only_line_ending and not is_line_ending_word) or is_punctuation_only or can_merge_letters:
                        input_history_events[-1].text += event.text
                        input_history_events[-1].phrase = text_to_phrase(input_history_events[-1].text)
                    else:
                        input_history_events.append(event)
                
        return reindex_events(input_history_events)

    # Determine the cursor position based on the previous state, the current state, and the inserted text
    def determine_diverges_from(self, previous_text: str, current_text: str, inserted: str = "") -> (int, int):
        line_index = -1
        from_end_of_line = -1
        normalized_inserted = inserted.replace("\r\n", "\n").replace("\r", "\n")

        # If everything is deleted - We estimate that we are at position 0, 0
        if current_text == "" and inserted == "":
            return (0, 0)
        elif current_text != "":
            is_deletion = inserted == "" and len(current_text) < len(previous_text)
            is_insertion = inserted != "" and len(current_text) - len(inserted) == len(previous_text)

            current_text = current_text.replace("\r\n", "\n")
            previous_text = previous_text.replace("\r\n", "\n")

            # Find the location where are are diverging from the text
            line_count = 1
            character_in_line_index = 0
            divergence_index = -1
            convergence_index = -1
            for char_index, char in enumerate(current_text):
                if char == "\n":
                    line_count += 1
                    character_in_line_index = 0

                if char_index < len(previous_text) and (char != previous_text[char_index]):
                    divergence_index = char_index

                    # Within a deletion we only need to known when the next character is the same again to find the convergence point
                    if is_deletion:
                        for previous_index in range(divergence_index, len(previous_text)):
                            if previous_text[previous_index] == current_text[divergence_index] and current_text[divergence_index:] == previous_text[previous_index:]:
                                convergence_index = previous_index

                                # Not sure why this fixes the multiline indexation but we'll take it
                                if line_count > 1:
                                    character_in_line_index -= 1

                                # If we are deleting some text and the text following the deletion is the same, we do not know the exact location
                                removed_text = previous_text[divergence_index:convergence_index]
                                current_text_lines = ""
                                if ( previous_index + 1 < len(previous_text) and previous_text[previous_index + 1:].startswith(removed_text) ) or \
                                    current_text[:char_index].endswith(removed_text):
                                    return (line_count - 1, -1)
                                break

                        break
                    else:
                        insertion_length = len(normalized_inserted)
                        start_substring = max(0, divergence_index - insertion_length)
                        substring_range = current_text[start_substring:divergence_index + insertion_length]
                        found_index = substring_range.find(normalized_inserted)
                        while found_index > -1:
                            if found_index <= insertion_length:
                                character_in_line_index = start_substring + found_index
                                break
                            found_index = substring_range.find(normalized_inserted, found_index + 1)

                        # If the substring of the inserted text does not appear in the area where we are changing
                        if found_index == -1:
                            return (-1, -1)
                        else:
                            break

                if divergence_index >= 0 and convergence_index >= 0:
                    break
                character_in_line_index += 1

            # When we are appending to the text, we can assume the final line count as well as the character location being the last of the sentence
            if divergence_index == -1 and is_insertion and current_text.startswith(previous_text):
                return (line_count - 1, 0)

            # If characters are deleted from the end of the selection, we know it is at the end of the current text
            if is_deletion and divergence_index == -1:
                line_index = len(current_text.split("\n")) -1
                from_end_of_line = 0

            elif divergence_index >= 0:
                line_index = line_count - 1 + max(0, len(normalized_inserted.split("\n")) - 1)
                current_text_lines = current_text.split("\n")
                line = current_text_lines[line_index] if line_index < len(current_text_lines) else current_text_lines[-1]

                if is_deletion:
                    from_end_of_line = len(line) - character_in_line_index
                else:                    
                    inserted_text_lines = normalized_inserted.split("\n")

                    # For multiline insertions, make sure that the character index of the insertion is used
                    # Instead of the found character index
                    character_in_line_index = 0 if len(inserted_text_lines) > 1 else character_in_line_index
                    if len(inserted_text_lines) > 1:
                        character_in_line_index = len(inserted_text_lines[-1])
                        from_end_of_line = len(line) - character_in_line_index
                    else:
                        from_end_of_line = len(line) - (character_in_line_index + len(normalized_inserted))

        return (line_index, from_end_of_line)

    # Find the end of the needle inside the haystack
    def determine_cursor_position(self, needle: str, haystack: str) -> (int, int):
        line_index = -1
        from_end_of_line = -1

        normalized_needle = " ".join(needle.split(" "))
        normalized_haystack = " ".join(haystack.split(" "))

        occurrences_count = normalized_haystack.count(normalized_needle)
        if occurrences_count == 1 and needle != "" and haystack != "":
            from_end_of_line = -1
            needle_index = normalized_haystack.find(normalized_needle)
            if needle_index > -1:
                line_count = 1
                for char_index, char in enumerate(normalized_haystack):
                    if char_index == needle_index:
                        line_index = line_count - 1
                        break

                    if char == "\n":
                        line_count += 1

                # Find exact character location within line
                if line_index >= 0:
                    needle_lines = needle.splitlines()
                    last_needle_line = needle_lines[-1]
                    haystack_line = haystack.splitlines()[line_index + len(needle_lines) - 1]

                    character_index = haystack_line.find(last_needle_line)
                    if character_index >= 0:
                        line_index += len(needle_lines) - 1
                        from_end_of_line = len(haystack_line) - character_index - len(last_needle_line)
                    # TODO Do fuzzier matching based on whitespace etc
                    else:
                        line_index = -1

        # For counts higher than 1 we are certain that we have matches, but they are too uncertain to match exactly
        elif occurrences_count > 1 and needle != "":
            line_index = -2
            from_end_of_line = -2

        # For counts lower than 1, we output -1, -1 to indicate none was found
        else:
            line_index = -1
            from_end_of_line = -1

        return (line_index, from_end_of_line)