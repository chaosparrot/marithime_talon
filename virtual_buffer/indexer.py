from .typing import VirtualBufferToken
from ..formatters.text_formatter import TextFormatter
import re
from typing import List, Tuple
from ..formatters.formatters import DICTATION_FORMATTERS
from .caret_tracker import _CARET_MARKER, _COARSE_MARKER

def text_to_phrase(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", ' ', text.replace("'", "").replace("’", "")).lower().split()).strip()

def normalize_text(text: str) -> str:
    return re.sub(r"[^\w\s]", ' ', text).replace("\n", " ")

# Transform raw text to virtual buffer tokens
def text_to_virtual_buffer_tokens(text: str, phrase: str = None, format: str = None) -> List[VirtualBufferToken]:
    lines = text.splitlines()
    if text.endswith("\n"):
        lines.append("")
    tokens = []
    if len(lines) == 1:
        token = VirtualBufferToken(text, "", "" if format is None else format)
        if phrase is not None:
            token.phrase = phrase
        else:
            token.phrase = text_to_phrase(text)
        return [token]
        # If there are line endings, split them up properly
    else:
        for line_index, line in enumerate(lines):
            token = VirtualBufferToken(line + "\n" if line_index < len(lines) - 1 else line, "", "" if format is None else format)
            token.phrase = text_to_phrase(line)
            tokens.append(token)
        return tokens

# Make sure the line numbers and character counts from the end of the line are properly kept
def reindex_tokens(tokens: List[VirtualBufferToken]) -> List[VirtualBufferToken]:
    length = len(tokens)
    if length == 0:
        return []

    # First sync the line counts
    line_index = 0
    previous_line_index = tokens[0].line_index
    new_tokens = []
    for index, token in enumerate(tokens):
        new_tokens.append(VirtualBufferToken(token.text, token.phrase, token.format, line_index, token.index_from_line_end))

        if token.text.endswith("\n"):
            line_index += 1

    # Then sync the character count
    previous_line_index = new_tokens[-1].line_index
    previous_line_end_count = 0
    for index, token in enumerate(reversed(new_tokens)):
        true_index = length - 1 - index
        if token.line_index == previous_line_index:
            new_tokens[true_index].index_from_line_end = previous_line_end_count
        else:
            previous_line_end_count = 0
            new_tokens[true_index].index_from_line_end = 0
            previous_line_index = token.line_index
        previous_line_end_count += len(token.text.replace("\n", ""))

    return new_tokens

# Class used to split off text into properly matched virtual buffer tokens
class VirtualBufferIndexer:

    default_formatter: TextFormatter = None
    formatters = []

    def __init__(self, formatters: List[TextFormatter] = []):
        self.default_formatter = DICTATION_FORMATTERS['EN']
        self.formatters = formatters

    def set_default_formatter(self, formatter: TextFormatter = None):
        pass
        #if formatter:
        #    self.default_formatter = formatter

    # Split raw (multi-line) text to virtual buffer tokens
    def index_text(self, text: str) -> List[VirtualBufferToken]:
        text = text.replace(_CARET_MARKER, '').replace(_COARSE_MARKER, '')

        # TODO - Do index matching based on if we are dealing with a regular or a programming language
        # We are now just using the default formatter instead
        words = self.default_formatter.split_format(text)
        
        tokens = []
        for word in words:
            new_tokens = text_to_virtual_buffer_tokens(word, None, self.default_formatter.name)
            for token in new_tokens:
                if len(tokens) == 0:
                    tokens.append(token)
                else:
                    token_text = normalize_text(token.text)
                    previous_token_text = normalize_text(tokens[-1].text)

                    # All the different cases in which we need to do merging
                    is_only_line_ending = token.text == "\n"
                    is_line_ending_word = token.text.endswith("\n") and len(token_text.replace(" ", "")) > 0
                    is_punctuation_only = token_text.replace(" ", "") == ""
                    can_merge_letters = not token_text.startswith(" ") and not previous_token_text.endswith(" ")
                    
                    if (is_only_line_ending and not is_line_ending_word) or is_punctuation_only or can_merge_letters:
                        tokens[-1].text += token.text
                        tokens[-1].phrase = text_to_phrase(tokens[-1].text)
                    else:
                        tokens.append(token)
                
        return reindex_tokens(tokens)

    # Determine the caret position based on the previous state, the current state, and the inserted text
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
                    
                    # Divergence at newline, make sure we do not increment the line index
                    if char_index < len(previous_text) and (char != previous_text[char_index]):
                        line_count -= 1

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
                                start_substring_in_line = character_in_line_index - (char_index - start_substring)
                                character_in_line_index = start_substring_in_line + found_index
                                if line_count > 1:
                                    character_in_line_index -= 1                                
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
    def determine_caret_position(self, needle: str, haystack: str, position: int = -1) -> (int, int):
        line_index = -1
        from_end_of_line = -1

        normalized_needle = " ".join(needle.split(" "))
        normalized_haystack = " ".join(haystack.split(" "))
        occurrences_count = normalized_haystack.count(normalized_needle)

        # Special case - End of the total value
        if position == len(normalized_haystack):
            line_index = len(haystack.splitlines()) - 1
            from_end_of_line = 0

        # Calculate the line and character index
        elif (occurrences_count == 1 and needle != "" and haystack != "") or position != -1:
            from_end_of_line = -1
            if position != -1:
                needle_index = position
            else:
                needle_index = normalized_haystack.find(normalized_needle)

            if needle_index > -1:
                line_count = 1
                index_from_line_start = 0
                for char_index, char in enumerate(normalized_haystack):
                    if char_index == needle_index:
                        line_index = line_count - 1
                        if position != -1:
                            from_end_of_line = len(haystack.splitlines()[line_index]) - index_from_line_start
                        break
                    index_from_line_start += 1

                    if char == "\n":
                        line_count += 1
                        index_from_line_start = 0

                # Find exact character location within line
                if line_index >= 0 and position == -1:
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

    def index_partial_tokens(self, previous_text: str, previous_tokens: List[VirtualBufferToken] = None, current_text: str = "") -> (List[VirtualBufferToken], List[int]):
        previous_text = previous_text.replace(_CARET_MARKER, '').replace(_COARSE_MARKER, '')
        current_text_caret_index = current_text.index(_CARET_MARKER) if _CARET_MARKER in current_text else -1
        current_text = current_text.replace(_CARET_MARKER, '').replace(_COARSE_MARKER, '')

        total_tokens = []
        merge_token_pairs = []

        # If the only thing that has changed is the caret position
        # We do not need to update the tokens
        if previous_text == current_text:
            return (previous_tokens, [])

        # If the text has gotten bigger, try to do some simple indexations before doing complex ones
        if len(previous_tokens) > 0:
            if len(current_text) > len(previous_text):
                # Simple appending, only create new tokens based on all the text after the previous tokens
                if current_text.startswith(previous_text):
                    appended_tokens = self.index_text(current_text[len(previous_text):])
                    total_tokens.extend(previous_tokens)
                    merge_token_pairs.append([len(previous_tokens) - 1, len(previous_tokens)])
                    total_tokens.extend(appended_tokens)
                
                # Simple prepending, only create new tokens based on all the text before the previous tokens
                elif current_text.endswith(previous_text):
                    prepended_tokens = self.index_text(current_text[:-len(previous_text) - 1])
                    total_tokens.extend(prepended_tokens)
                    merge_token_pairs.append([len(prepended_tokens) - 1, len(prepended_tokens)])
                    total_tokens.extend(previous_tokens)

                # Simple middle insertion comparing carets, only create new tokens based on all the tokens in the middle
                elif current_text_caret_index > -1 and previous_text.endswith(current_text[current_text_caret_index:]):
                    characters_to_remove = len(current_text[current_text_caret_index:])
                    starting_text = current_text[:current_text_caret_index]

                    if current_text[:current_text_caret_index].startswith(previous_text[:-characters_to_remove]):
                        created_text = starting_text[len(previous_text[:-characters_to_remove]):]
                        inserted_tokens = self.index_text(created_text)
                        total_tokens.extend(previous_tokens)
                        
                        # Find the token index where we should insert
                        has_token_split = False
                        inserted_index = -1
                        while characters_to_remove > 0:
                            if len(total_tokens[inserted_index].text) <= characters_to_remove:
                                text_to_remove = len(total_tokens[inserted_index].text)
                                characters_to_remove -= text_to_remove
                                inserted_index -= 1
                            elif len(total_tokens[inserted_index].text) > characters_to_remove:

                                # Split token so that it can be merged later
                                next_token_text = total_tokens[inserted_index].text[len(total_tokens[inserted_index].text) - characters_to_remove:]

                                total_tokens[inserted_index].text = total_tokens[inserted_index].text[:len(total_tokens[inserted_index].text) - characters_to_remove]
                                total_tokens[inserted_index].phrase = text_to_phrase(total_tokens[inserted_index].text)

                                # Append new split tokens
                                if len(next_token_text) > 0:
                                    new_tokens = text_to_virtual_buffer_tokens(next_token_text)
                                    for token_index, new_token in enumerate(new_tokens):
                                        new_tokens[token_index].format = total_tokens[-1].format
                                    inserted_tokens.extend(new_tokens)
                                    has_token_split = True

                                characters_to_remove = 0

                        index_in_total_tokens = len(total_tokens) + inserted_index + 1
                        merge_token_pairs.append([index_in_total_tokens - 1, index_in_total_tokens])
                        if has_token_split:
                            merge_token_pairs.append([index_in_total_tokens + len(inserted_tokens) - 2, index_in_total_tokens + len(inserted_tokens) - 1])
                        if inserted_index == -1:
                            total_tokens.extend(inserted_tokens)
                        else:
                            if has_token_split:
                                inserted_index += 1
                            total_tokens[inserted_index:inserted_index] = inserted_tokens
            
            # If the text has gotten smaller, try to do simple indexations before doing complex ones
            else:
                # Simple removal at the end, only remove tokens based on the amount of characters removed from the previous text
                difference = len(previous_text) - len(current_text)
                characters_to_remove = difference
                if previous_text.startswith(current_text):
                    total_tokens = previous_tokens
                    while characters_to_remove > 0:
                        if len(total_tokens) > 0:
                            if len(total_tokens[-1].text) <= characters_to_remove:
                                text_to_remove = len(total_tokens[-1].text)
                                del total_tokens[-1]
                                characters_to_remove -= text_to_remove
                            elif len(total_tokens[-1].text) > characters_to_remove:
                                total_tokens[-1].text = total_tokens[-1].text[:len(total_tokens[-1].text) - characters_to_remove]
                                total_tokens[-1].phrase = text_to_phrase(total_tokens[-1].text)
                                characters_to_remove = 0
                        else:
                            characters_to_remove = 0
                    merge_token_pairs.append([len(total_tokens) - 2, len(total_tokens) - 1])

                # Simple removal at the start, only remove tokens based on the amount of characters removed from the previous text
                elif previous_text.endswith(current_text):
                    total_tokens = previous_tokens
                    while characters_to_remove > 0:
                        if len(total_tokens) > 0:
                            if len(total_tokens[0].text) <= characters_to_remove:
                                text_to_remove = len(total_tokens[0].text)
                                del total_tokens[0]
                                characters_to_remove -= text_to_remove
                            elif len(total_tokens[0].text) > characters_to_remove:
                                total_tokens[0].text = total_tokens[0].text[characters_to_remove:]
                                total_tokens[0].phrase = text_to_phrase(total_tokens[0].text)
                                characters_to_remove = 0
                        else:
                            characters_to_remove = 0
                    merge_token_pairs.append([0, 1])
                
                # Simple middle removal comparing carets, only remove tokens based on all the tokens in the middle
                elif current_text_caret_index > -1 and previous_text.endswith(current_text[current_text_caret_index:]):
                    starting_text = current_text[:current_text_caret_index]
                    token_length_at_end = len(starting_text)
                    if current_text[:current_text_caret_index].startswith(previous_text[:-characters_to_remove - token_length_at_end]):
                        total_tokens = previous_tokens
                        index_to_remove = -1
                        while token_length_at_end > 0:
                            if len(total_tokens[-1].text) <= token_length_at_end:
                                text_to_remove = len(total_tokens[-1].text)
                                token_length_at_end -= text_to_remove
                                index_to_remove -= 1
                            elif len(total_tokens[-1].text) > token_length_at_end:
                                token_length_at_end = 0

                        merge_token_pairs.append([len(total_tokens) + index_to_remove, len(total_tokens) + index_to_remove - 1])
                        while characters_to_remove > 0:
                            if abs(index_to_remove) < len(total_tokens):
                                if len(total_tokens[index_to_remove].text) <= characters_to_remove:
                                    text_to_remove = len(total_tokens[index_to_remove].text)
                                    del total_tokens[index_to_remove]
                                    characters_to_remove -= text_to_remove
                                elif len(total_tokens[index_to_remove].text) > characters_to_remove:
                                    total_tokens[index_to_remove].text = total_tokens[index_to_remove].text[characters_to_remove:]
                                    total_tokens[index_to_remove].phrase = text_to_phrase(total_tokens[index_to_remove].text)
                                    characters_to_remove = 0
                            else:
                                characters_to_remove = 0
                        merge_token_pairs.append([len(total_tokens) + index_to_remove, len(total_tokens) + index_to_remove + 1])

        if len(total_tokens) > 0:

            # Sort merged token pairs by highest index first
            # So we don't have to deal with shifting indices later
            indices_to_insert = []
            for pair in merge_token_pairs:
                indices_to_insert.append(pair[0])
                indices_to_insert.append(pair[-1])

            indices_to_insert = list(set(sorted(indices_to_insert)))
            return (reindex_tokens(total_tokens), indices_to_insert)
        else:
            return (self.index_full_partial_mending(previous_text, previous_tokens, current_text), [])

    def index_full_partial_mending(self, previous_text: str, previous_tokens: List[VirtualBufferToken] = None, current_text: str = ""):
        # TODO - COMPLEX MENDING WITHIN TEXT OR JUST AUTOMATIC FORMATTER DETECTION?
        print("WEEEE :(")
        return self.index_text(current_text)