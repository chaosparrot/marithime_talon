from talon import Module, Context
from .typing import VirtualBufferToken, VirtualBufferTokenContext
from .matcher import VirtualBufferMatcher
from typing import List, Dict
from .caret_tracker import CaretTracker
from ..phonetics.actions import phonetic_search
from .indexer import text_to_phrase, normalize_text, reindex_tokens
import re
mod = Module()
ctx = Context()

MERGE_STRATEGY_IGNORE = -1
MERGE_STRATEGY_APPEND_AFTER = 0
MERGE_STRATEGY_JOIN = 1
MERGE_STRATEGY_SPLIT_LEFT_JOIN_RIGHT = 2
MERGE_STRATEGY_JOIN_LEFT_SPLIT_RIGHT = 3
MERGE_STRATEGY_SPLIT = 4

# Class to manage the state of inserted text
class VirtualBuffer:
    tokens: List[VirtualBufferToken] = None
    caret_tracker: CaretTracker = None

    last_action_type = "insert"

    def __init__(self):
        self.caret_tracker = CaretTracker()
        self.matcher = VirtualBufferMatcher(phonetic_search)
        self.set_tokens()

    def is_selecting(self) -> bool:
        return self.caret_tracker.is_selecting()
    
    def is_phrase_selected(self, phrase: str) -> bool:
        return self.matcher.has_matching_phrase(self, phrase)

    def clear_tokens(self):
        self.set_tokens()

    def set_tokens(self, tokens: List[VirtualBufferToken] = None):
        if tokens is None:
            self.caret_tracker.clear()
            self.tokens = []
        else:
            self.tokens = tokens

    def determine_leftmost_token_index(self):
        return self.determine_token_index(self.caret_tracker.get_leftmost_caret_index())
    
    def determine_rightmost_token_index(self):
        return self.determine_token_index(self.caret_tracker.get_rightmost_caret_index())

    def determine_token_index(self, caret_index: (int, int) = None) -> (int, int):
        if caret_index is None:
            caret_index = self.caret_tracker.get_caret_index()

        line_index, character_index = caret_index
        if line_index > -1 and character_index > -1: 
            for token_index, token in enumerate(self.tokens):
                if token.line_index == line_index and \
                    token.index_from_line_end <= character_index and token.index_from_line_end + len(token.text) >= character_index:
                    token_character_index = (len(token.text.replace("\n", "")) + token.index_from_line_end) - character_index
                    return token_index, token_character_index
            
            # Detect new lines properly
            if len(self.tokens) > 0 and "\n" in self.tokens[-1].text:
                return len(self.tokens) - 1, len(self.tokens[-1].text)
        return -1, -1
    
    def determine_context(self) -> VirtualBufferTokenContext:
        index, character_index = self.determine_token_index()
        if index > -1 and character_index > -1:
            current = self.tokens[index]
            previous = None if index == 0 else self.tokens[index - 1]
            next = None if index >= len(self.tokens) - 1 else self.tokens[index + 1]
            return VirtualBufferTokenContext(character_index, previous, current, next)

        else:
            return VirtualBufferTokenContext(0)
    
    def insert_tokens(self, tokens: List[VirtualBufferToken]):
        token_index = self.determine_token_index()
        reformat_after_each_token = token_index[0] < len(self.tokens) - 1

        for index, token in enumerate(tokens):
            self.insert_token(token, reformat_after_each_token or index == len(tokens) - 1)

    def insert_token(self, token_to_insert: VirtualBufferToken, reformat = True):
        if self.is_selecting() and token_to_insert.text != "":
            self.remove_selection()

        line_index, character_index = self.caret_tracker.get_caret_index()
        if line_index > -1 and character_index > -1:
            token_index, token_character_index = self.determine_token_index()

            merge_strategies = self.detect_merge_strategy(token_index, token_character_index, token_to_insert)

            appended = False
            if merge_strategies[0] == MERGE_STRATEGY_APPEND_AFTER or merge_strategies[1] == MERGE_STRATEGY_APPEND_AFTER:
                # Update the previous tokens on this line to have accurate character count
                for token in self.tokens:
                    if token_to_insert.line_index == line_index:
                        token.index_from_line_end += len(token.text.replace("\n", ""))
                token_to_insert.line_index += line_index
                
                if merge_strategies[1] == MERGE_STRATEGY_APPEND_AFTER:
                    if token_index < len(self.tokens) - 1:
                        self.append_token_after(token_index, token_to_insert, reformat)
                    else:
                        self.tokens.append(token_to_insert)
                        if reformat:
                            self.reformat_tokens()
                else:
                    self.append_token_after(token_index - 1, token_to_insert, reformat)

                self.caret_tracker.append_before_caret(token_to_insert.text)
                appended = True

            # If empty tokens are inserted in the middle, just ignore them
            elif token_index < len(self.tokens) - 1 and token_to_insert.text == "":
                return
            
            if appended == False:
                self.caret_tracker.append_before_caret(token_to_insert.text)

                if MERGE_STRATEGY_JOIN in merge_strategies:
                    if merge_strategies[1] == MERGE_STRATEGY_JOIN:
                        self.merge_tokens(token_index, token_character_index, token_to_insert)
                    elif merge_strategies[0] == MERGE_STRATEGY_JOIN:
                        self.merge_tokens(token_index - 1, len(self.tokens[token_index - 1].text), token_to_insert)
                    elif merge_strategies[2] == MERGE_STRATEGY_JOIN:
                        self.merge_tokens(token_index + 1, 0, token_to_insert)
                    if reformat:
                        self.reformat_tokens()

                elif MERGE_STRATEGY_SPLIT in merge_strategies or \
                    MERGE_STRATEGY_JOIN_LEFT_SPLIT_RIGHT in merge_strategies or MERGE_STRATEGY_SPLIT_LEFT_JOIN_RIGHT in merge_strategies:
                    self.split_tokens(token_index, token_character_index, token_to_insert, merge_strategies)
        else:
            self.clear_tokens()
            self.tokens.append(token_to_insert)
            self.caret_tracker.append_before_caret(token_to_insert.text)

        self.last_action_type = "insert"

    def append_token_after(self, token_index: int, appended_token: VirtualBufferToken, should_reindex = True):
        appended_token.line_index = self.tokens[token_index].line_index
        if self.tokens[token_index].text.endswith("\n"):
            appended_token.line_index += 1

        reindex = should_reindex and token_index + 1 < len(self.tokens)
        self.tokens.insert(token_index + 1, appended_token)
        if reindex:
            self.reformat_tokens()

    def find_self_repair(self, phrase: List[str]):
        self_repair_matches = self.matcher.find_self_repair_match(self, phrase)
        return self_repair_matches

    def detect_self_repair(self, phrase: List[str]) -> bool:
        return self.find_self_repair(phrase) is not None

    def detect_merge_strategy(self, token_index: int, token_character_index: int, token: VirtualBufferToken) -> (int, int, int):
        current_strategy = MERGE_STRATEGY_IGNORE
        previous_strategy = MERGE_STRATEGY_IGNORE
        next_strategy = MERGE_STRATEGY_IGNORE

        if len(self.tokens) != 0:
            token_text = normalize_text(token.text)
            previous_token_text = "" if token_index - 1 < 0 else normalize_text(self.tokens[token_index - 1].text)
            current_token_text = "" if token_index < 0 else normalize_text(self.tokens[token_index].text)
            next_token_text = "" if token_index + 1 > len(self.tokens) - 1 else normalize_text(self.tokens[token_index + 1].text)

        if len(self.tokens) == 0:
            current_strategy = MERGE_STRATEGY_APPEND_AFTER

        # When we are at the start of an token, we can possibly join the previous token with the current input
        elif token_character_index == 0:
            if current_token_text == "" or ( not token_text.endswith(" ") and not current_token_text.startswith(" ") ):
                current_strategy = MERGE_STRATEGY_JOIN
            
            if token_index > 0 and not token_text.startswith(" ") and not previous_token_text.endswith(" "):
                previous_strategy = MERGE_STRATEGY_JOIN
            elif current_strategy != MERGE_STRATEGY_JOIN:
                previous_strategy = MERGE_STRATEGY_APPEND_AFTER
        
        # When we are at the end of an token, we can possibly join the next token with the current input
        elif token_character_index >= len(self.tokens[token_index].text):
            if (not token_text.startswith(" ") or token_text.replace(" ", "") == "") and not current_token_text.endswith(" "):
                current_strategy = MERGE_STRATEGY_JOIN

            if token_index < len(self.tokens) - 1 and not token_text.endswith(" ") and not next_token_text.startswith(" "):
                next_strategy = MERGE_STRATEGY_JOIN
            elif token.text.endswith("\n"):
                current_strategy = MERGE_STRATEGY_JOIN
            elif current_strategy != MERGE_STRATEGY_JOIN:
                current_strategy = MERGE_STRATEGY_APPEND_AFTER

        # Determine how to divide and join the current token
        else:
            current_text = self.tokens[token_index].text
            previous_character = " " if token_character_index - 1 < 0 else current_text[token_character_index - 1]
            next_character = " " if token_character_index < 0 and token_character_index != len(current_text) else current_text[token_character_index]
            can_join_left = ( not token_text.startswith(" ") and normalize_text(previous_character) != " " ) or token.text == "\n"
            can_join_right = not token_text.endswith(" ") and normalize_text(next_character) != " "

            if can_join_left and can_join_right:
                current_strategy = MERGE_STRATEGY_JOIN
            elif can_join_left:
                current_strategy = MERGE_STRATEGY_JOIN_LEFT_SPLIT_RIGHT
            elif can_join_right:
                current_strategy = MERGE_STRATEGY_SPLIT_LEFT_JOIN_RIGHT
            else:
                current_strategy = MERGE_STRATEGY_SPLIT

        return (previous_strategy, current_strategy, next_strategy)

    def split_tokens(self, token_index: int, token_character_index: int, token: VirtualBufferToken, merge_strategy: (int, int, int)):
        before_text = self.tokens[token_index].text[:token_character_index]
        after_text = self.tokens[token_index].text[token_character_index:]
        if merge_strategy[1] == MERGE_STRATEGY_SPLIT:
            self.tokens[token_index].text = before_text
            self.tokens[token_index].phrase = text_to_phrase(before_text)
            self.append_token_after(token_index, token)
            self.append_token_after(token_index + 1, VirtualBufferToken(after_text, text_to_phrase(after_text), self.tokens[token_index].format))

        elif merge_strategy[1] == MERGE_STRATEGY_JOIN_LEFT_SPLIT_RIGHT:
            self.tokens[token_index].text = before_text + token.text
            self.tokens[token_index].phrase = text_to_phrase(before_text + token.text)
            self.append_token_after(token_index, VirtualBufferToken(after_text, text_to_phrase(after_text), self.tokens[token_index].format))

        elif merge_strategy[1] == MERGE_STRATEGY_SPLIT_LEFT_JOIN_RIGHT:
            self.tokens[token_index].text = before_text
            self.tokens[token_index].phrase = text_to_phrase(before_text)
            token.text = token.text + after_text
            token.phrase = text_to_phrase(token.text)
            self.append_token_after(token_index, token)
        self.reformat_tokens()

    def merge_tokens(self, token_index: int, token_character_index: int, token: VirtualBufferToken):
        previous_token = self.tokens[token_index]

        if "\n" in token.text:
            text_lines = token.text.splitlines()
            if token.text.endswith("\n"):
                text_lines.append("")
        else:
            text_lines = [token.text]
        
        total_text_lines = len(text_lines)
        tokens = []
        for line_index, text_line in enumerate(text_lines):
            text = ""
            if line_index == 0:
                text = previous_token.text[:token_character_index]
            text += text_line
            if total_text_lines > 1 and line_index != total_text_lines - 1:
                text += "\n"
            if line_index == total_text_lines - 1:
                text += previous_token.text[token_character_index:]
            
            new_token = VirtualBufferToken(text, text_to_phrase(text), "")
            new_token.line_index = previous_token.line_index + line_index
            tokens.append(new_token)

        for index, new_token in enumerate(tokens):
            if index == 0:
                self.tokens[token_index].text = new_token.text
                self.tokens[token_index].phrase = new_token.phrase
                if new_token.text.endswith("\n"):
                    self.tokens[token_index].index_from_line_end = 0
            else:
                self.append_token_after(token_index + index - 1, new_token)
        
    def remove_selection(self) -> bool:
        selection_indexes = self.caret_tracker.remove_selection()
        if selection_indexes[0][0] != selection_indexes[1][0] or \
            selection_indexes[0][1] != selection_indexes[1][1]:
            
            start_index = self.determine_token_index(selection_indexes[0])
            end_index = self.determine_token_index(selection_indexes[1])

            merge_token = None
            should_detect_merge = False

            tokens = []
            for token_index, token in enumerate(self.tokens):
                if token_index < start_index[0] or token_index > end_index[0]:

                    # Attempt merge if the tokens can be combined
                    if should_detect_merge and not re.sub(r"[^\w\s]", ' ', token.text).replace("\n", " ").startswith(" ") and \
                            not re.sub(r"[^\w\s]", ' ', tokens[-1].text).replace("\n", " ").endswith(" "):

                        merge_token = tokens[-1]
                        text = merge_token.text + token.text
                        tokens[-1].text = text
                        tokens[-1].phrase = text_to_phrase(text)
                        merge_token = None
                        should_detect_merge = False

                    # Otherwise just add the token
                    else:
                        tokens.append(token)
                else:
                    text = token.text

                    # Same token - No overlap between tokens
                    if token_index == start_index[0] and token_index == end_index[0]:
                        text = text[:start_index[1]] + text[end_index[1]:]
                        if text != "":
                            tokens.append(VirtualBufferToken(text, text_to_phrase(text), "", token.line_index))
                            should_detect_merge = start_index[1] == 0 or end_index[1] >= len(text.replace("\n", ""))
                    # Split token, remember the first token from the selection
                    elif token_index == start_index[0]:
                        text = text[:start_index[1]]
                        should_detect_merge = not re.sub(r"[^\w\s]", ' ', text).replace("\n", " ").endswith(" ")
                        if start_index[1] == len(token.text.replace('\n', '')) and not should_detect_merge:
                            tokens.append(token)
                        elif start_index[1] > 0:
                            merge_token = VirtualBufferToken(text, text_to_phrase(text), "", token.line_index)
                    # Split token, attempt to merge the first token with the current token
                    elif token_index == end_index[0]:
                        text = text[end_index[1]:]

                        if merge_token is not None and should_detect_merge and not re.sub(r"[^\w\s]", ' ', text).replace("\n", " ").startswith(" "):
                            text = merge_token.text + text
                        elif merge_token is not None:
                            tokens.append(merge_token)

                        merge_token = None
                        should_detect_merge = False
                        if text != "":
                            tokens.append(VirtualBufferToken(text, text_to_phrase(text), "", token.line_index))
            
            # If we are left with a merge token, add it anyway
            if merge_token is not None:
                tokens.append(merge_token)

            self.tokens = tokens
            self.reformat_tokens()

            return True
        else:
            return False
    
    def apply_delete(self, delete_count = 0):
        if self.is_selecting() and delete_count > 0:
            if self.remove_selection():
                delete_count -= 1

        if delete_count <= 0:
            return

        line_index, character_index = self.caret_tracker.get_caret_index()
        if line_index > -1 and character_index > -1:
            token_index, token_character_index = self.determine_token_index()
            text = self.tokens[token_index].text
            remove_from_token = min(len(text) - token_character_index, delete_count)
            remove_from_next_tokens = delete_count - (len(text) - token_character_index)

            # If we are removing a full token in the middle, make sure to just remove the token
            text = text[:token_character_index] + text[token_character_index + remove_from_token:]
            should_detect_merge = token_character_index == 0 or token_character_index >= len(text.replace("\n", ""))

            if text == "":
                del self.tokens[token_index]
                token_index -= 1
            else:
                self.tokens[token_index].text = text
                self.tokens[token_index].phrase = text_to_phrase(text)

            next_token_index = token_index + 1
            if remove_from_next_tokens > 0:
                while next_token_index < len(self.tokens) and remove_from_next_tokens > 0:
                    if len(self.tokens[next_token_index].text) <= remove_from_next_tokens:
                        remove_from_next_tokens -= len(self.tokens[next_token_index].text)
                        del self.tokens[next_token_index]
                    else:
                        next_text = self.tokens[next_token_index].text[remove_from_next_tokens:]
                        self.tokens[next_token_index].text = next_text
                        self.tokens[next_token_index].phrase = text_to_phrase(next_text)

                        remove_from_next_tokens = 0
                        self.reformat_tokens()

            # Detect if we should merge the tokens if the text combines
            if should_detect_merge and next_token_index - 1 >= 0:
                token_index = next_token_index - 1
                next_token_index = token_index + 1
                
                if next_token_index < len(self.tokens):
                    previous_text = "" if token_index < 0 else self.tokens[token_index].text
                    text = self.tokens[next_token_index].text

                    if should_detect_merge and (text == "\n" or not re.sub(r"[^\w\s]", ' ', text).replace("\n", " ").startswith(" ") ) and not re.sub(r"[^\w\s]", ' ', previous_text).replace("\n", " ").endswith(" "):
                        text = previous_text + text
                        self.tokens[token_index].text = text
                        self.tokens[token_index].phrase = text_to_phrase(text)
                        del self.tokens[next_token_index]
                        self.reformat_tokens()            

            self.caret_tracker.remove_after_caret(delete_count)
        self.last_action_type = "remove"
        
    def apply_backspace(self, backspace_count = 0):
        if self.is_selecting() and backspace_count > 0:
            if self.remove_selection():
                backspace_count -= 1
            self.last_action_type = "remove"

        if backspace_count <= 0:
            return

        line_index, character_index = self.caret_tracker.get_caret_index()
        if line_index > -1 and character_index > -1:
            token_index, token_character_index = self.determine_token_index()
            remove_from_previous_tokens = abs(min(0, token_character_index - backspace_count ))
            remove_from_token = backspace_count - remove_from_previous_tokens
            text = self.tokens[token_index].text

            # If we are removing a full token in the middle, make sure to just remove the token
            text = text[:token_character_index - remove_from_token] + text[token_character_index:]
            should_detect_merge = token_character_index - backspace_count <= 0 or token_character_index >= len(text.replace("\n", ""))            
            if text == "" and token_index + 1 < len(self.tokens) - 1:
                del self.tokens[token_index]
            else:
                self.tokens[token_index].text = text
                self.tokens[token_index].phrase = text_to_phrase(text)
            
            previous_token_index = token_index - 1
            if remove_from_previous_tokens > 0:
                while previous_token_index >= 0 and remove_from_previous_tokens > 0:
                    if len(self.tokens[previous_token_index].text) <= remove_from_previous_tokens:
                        remove_from_previous_tokens -= len(self.tokens[previous_token_index].text)
                        del self.tokens[previous_token_index]
                        previous_token_index -= 1
                    else:
                        previous_text = self.tokens[previous_token_index].text
                        previous_text = previous_text[:len(previous_text) - remove_from_previous_tokens]
                        self.tokens[previous_token_index].text = previous_text
                        self.tokens[previous_token_index].phrase = text_to_phrase(previous_text)

                        remove_from_previous_tokens = 0
                        self.reformat_tokens()

            # Detect if we should merge the tokens if the text combines
            if should_detect_merge:
                token_index = previous_token_index + 1
                if token_index == 0 and len(self.tokens) > 1:
                    previous_token_index = 0

                if previous_token_index + 1 < len(self.tokens):
                    previous_text = "" if previous_token_index < 0 else self.tokens[previous_token_index].text
                    text = self.tokens[previous_token_index + 1].text

                    if should_detect_merge and (text == "\n" or not re.sub(r"[^\w\s]", ' ', text).replace("\n", " ").startswith(" ") ) and not re.sub(r"[^\w\s]", ' ', previous_text).replace("\n", " ").endswith(" "):
                        text = previous_text + text
                        self.tokens[previous_token_index].text = text
                        self.tokens[previous_token_index].phrase = text_to_phrase(text)
                        del self.tokens[previous_token_index + 1]

                        self.reformat_tokens()            

            self.caret_tracker.remove_before_caret(backspace_count)
        self.last_action_type = "remove"

    def reformat_tokens(self):
        self.tokens = reindex_tokens(self.tokens)

    def apply_key(self, keystring: str):
        keys = keystring.lower().split(" ")
        for key in keys:
            key_used = self.caret_tracker.apply_key(key)
            if key_used:
                self.last_action_type = self.caret_tracker.last_caret_movement
            if not key_used and "backspace" in key or "delete" in key:
                key_modifier = key.split(":")
                if len(key_modifier) > 1 and key_modifier[-1] == "up":
                    continue
                if "ctrl" in key_modifier[0]:
                    self.clear_tokens()
                else:
                    key_presses = 1
                    if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                        key_presses = int(key_modifier[-1])

                    if "delete" in key:
                        self.apply_delete(key_presses)
                    else:
                        self.apply_backspace(key_presses)

        if not self.caret_tracker.text_buffer:
            self.clear_tokens()

    def has_matching_phrase(self, phrase: str) -> bool:
        return self.matcher.has_matching_phrase(self, phrase)
    
    def go_phrase(self, phrase: str, position: str = 'end', keep_selection: bool = False, next_occurrence: bool = True) -> List[str]:
        token = self.find_token_by_phrase(phrase, -1 if position == 'end' else 0, next_occurrence)
        if token:
            return self.navigate_to_token(token, -1 if position == 'end' else 0, keep_selection)
        else:
            return None
        
    def select_until_end(self, phrase: str = "") -> List[str]:
        keys = []
        if len(self.tokens) > 0:
            if phrase != "":
                start_token = self.find_token_by_phrase(phrase, 0, True, False)
                if start_token:
                    keys.extend(self.navigate_to_token(start_token, 0, False))
            
            keys.extend(self.select_token(self.tokens[-1], True))

        return keys
    
    def select_phrases(self, phrases: List[str], match_threshold: float = 1, extend_selection: bool = False) -> List[str]:
        # For a single phrase we can fall back to a single selection
        if len(phrases) == 1:
            return self.select_phrase(phrases[0], extend_selection)

        # Determine if we need to cycle between selections
        should_go_to_next_occurrence = not extend_selection
        if should_go_to_next_occurrence:
            for phrase in phrases:
                should_go_to_next_occurrence = self.matcher.is_phrase_selected(self, phrase)
                if not should_go_to_next_occurrence:
                    break

        best_match = self.matcher.find_best_match_by_phrases(self, phrases, match_threshold, should_go_to_next_occurrence, True)
        if best_match is not None and len(best_match) > 0:
            return self.select_token_range(best_match[0], best_match[-1])
        else:
            return []
    
    def select_token_range(self, start_token: VirtualBufferToken, end_token: VirtualBufferToken, extend_selection: bool = False ) -> List[str]:
        if not extend_selection:
            keys = self.navigate_to_token(start_token, 0)
        else:
            keys = self.select_token(start_token, extend_selection)
        keys.extend( self.select_token(end_token, True))

        return keys

    def select_phrase(self, phrase: str, extend_selection: bool = False) -> List[str]:        
        token = self.find_token_by_phrase(phrase, 0, not extend_selection and self.matcher.is_phrase_selected(self, phrase), True)
        return self.select_token(token, extend_selection)
    
    def select_token(self, token: VirtualBufferToken, extend_selection: bool = False) -> List[str]:
        if token:
            self.use_last_set_formatter = False
            keys = []

            # Continue the selection we have going right now
            if extend_selection:
                # By default, go towards the end of the token
                token_caret_end = -1            
                reset_selection = False

                left_caret = self.caret_tracker.get_leftmost_caret_index()
                right_caret = self.caret_tracker.get_rightmost_caret_index()

                caret_index = self.caret_tracker.get_caret_index()
                caret_on_left_side = caret_index[0] == left_caret[0] and caret_index[1] == left_caret[1]

                # We need to reset our selection if we are adding new tokens in the opposite side of the selection
                if token.line_index < left_caret[0] or \
                    (token.line_index == left_caret[0] and token.index_from_line_end + len(token.text.replace('\n', '')) > left_caret[1]):

                    # When extending left, make sure to move to the start of the token to be selected
                    left_caret = (token.line_index, token.index_from_line_end + len(token.text.replace('\n', '')))
                    if caret_on_left_side:
                        token_caret_end = 0
                    else:
                        reset_selection = True
                
                # When going right, we need to reset the selection if our caret is on the left side of the seletion
                elif token.line_index > right_caret[0] or \
                    (token.line_index == right_caret[0] and token.index_from_line_end < right_caret[1]):

                    right_caret = (token.line_index, token.index_from_line_end)                
                    if caret_on_left_side:
                        reset_selection = True

                if not reset_selection:                    
                    after_keys = self.navigate_to_token(token, token_caret_end, True)
                    if not self.caret_tracker.shift_down:
                        for key in after_keys:
                            keys.append( "shift-" + key )
                    else:
                        keys.extend(after_keys)

                # Reset the selection, go to the left side and all the way to the right side
                else:
                    key_events = self.caret_tracker.navigate_to_position(left_caret[0], left_caret[1], True)
                    for key in key_events:
                        self.apply_key(key)
                    keys.extend(key_events)

                    key_events = self.caret_tracker.navigate_to_position(right_caret[0], right_caret[1], False)
                    for key in key_events:
                        self.apply_key("shift-" + key)
                    keys.extend(key_events)
            
            # New selection - just go to the token and select it
            else:                
                before_keys = self.navigate_to_token(token, 0, False)
                keys.extend(before_keys)
                after_keys = self.navigate_to_token(token, -1, True)
                for key in after_keys:
                    keys.append("shift-" + key)

            return keys
        else: 
            return None

    def find_token_by_phrase(self, phrase: str, char_position: int = -1, next_occurrence: bool = True, selecting: bool = False) -> VirtualBufferToken:
        return self.matcher.find_single_match_by_phrase(self, phrase, char_position, next_occurrence, selecting)

    def navigate_to_token(self, token: VirtualBufferToken, char_position: int = -1, keep_selection: bool = False) -> List[str]:
        if token != None:
            index_from_end = token.index_from_line_end + len(token.text)
            if char_position == -1:
                char_position = -len(token.text)

            key_events = self.caret_tracker.navigate_to_position(token.line_index, index_from_end + char_position, not keep_selection)
            for key in key_events:
                self.apply_key(key)

            # If we do not move, still keep a memory that a caret movement was done rather than an insertion or removal
            if len(key_events) == 0:
                self.last_action_type = self.caret_tracker.last_caret_movement
        else:
            key_events = []
        return key_events
    
    def get_current_formatters(self) -> List[str]:
        formatters = []
        token_index = self.determine_leftmost_token_index()
        if token_index[0] != -1:
            token = self.tokens[token_index[0]]
            if len(token.format) > 0:
                formatters = token.format.split("|")
        return formatters
    
    # Get the text before the caret, or a possible selection
    def get_previous_text(self):
        token_index = self.determine_leftmost_token_index()
        previous_text = ""
        if token_index[0] != -1:
            previous_text = ""
            for index, token in enumerate(self.tokens):
                if index < token_index[0]:
                    previous_text += token.text
                elif index == token_index[0]:
                    if token_index[1] > 0 and token_index[1] <= len(token.text.replace("\n", "")):
                        previous_text += token.text[:token_index[1]]
                else:
                    break

        return previous_text

    # Get the text after the caret, or a possible selection
    def get_next_text(self) -> str:
        right_token_index = self.determine_rightmost_token_index()
        next_text = ""
        if right_token_index[0] != -1:
            for index, token in enumerate(self.tokens):
                if index > right_token_index[0]:
                    next_text += token.text
                elif index == right_token_index[0]:
                    if right_token_index[1] > 0 and right_token_index[1] < len(token.text.replace("\n", "")):
                        next_text += self.tokens[index].text[right_token_index[1]:]

        return next_text
