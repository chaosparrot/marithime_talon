from talon import actions, clip
from typing import List
import re

# CURSOR MARKERS
 # TODO APPEND RANDOM NUMBER FOR LESS COLLISIONS?
_CURSOR_MARKER = "$CURSOR" # Keeps track of the exact cursor position
_COARSE_MARKER = "$COARSE_CURSOR" # Keeps track of the line number if we arent sure what character we are on
_INCONSISTENT_WHITESPACE_MARKER = "\u00A0"

# SHOULD SUPPORT:
# MULTI LINE TEXT
# SINGLE LINE TEXT
# SELECTION DETECTION
# CONTEXT CLEARING
# MOVING TO WORDS WITHIN THE HISTORY
# MULTIPLE KEY STROKES
# KEYSTROKE DETECTION

# Class to keep track of the cursor position in the recently inserted text
# There are some assumptions made in order for this to work
#
# 1 - On the first line, we cannot go up or past the start of the line, as other text might be in front of it
# 2 - On the last line, we cannot go down or past the end of the line, as other text might be after it
# 3 - Going left and going right moves the cursor in a predictable manner
# 4 - Going left and going right might skip over to another line, it isn't bounded
# 5 - Going up moves to an inconsistent place inside the above line
# 6 - Going down moves to an inconsistent place inside the below line
# 7 - When we are dealing with word wrapping, which happens in non-terminal and IDE environments, going up and down might not even go on the next line
# 8 - Pressing (shift-)enter will insert a new line with an unknown amount of whitespace
# 9 - Pressing tab will insert an unknown amount of whitespace ( either a tab, or N amount of space characters )
# 10 - If we select text and press right, the cursor will always appear on the right of the selection and end the selection
# 11 - If we select text and press left, the cursor will appear on an inconsistent place depending on the program
# 12 - If we select a whole line and read its contents, we can determine the position of the cursor within the text history
# 13 - Pressing backspace behaves inconsistently
# 14 - Pressing backspace before whitespace behaves inconsistently in some programs ( IDEs )
# 15 - Pressing backspace with a selection behaves consistently ( removes the selection and keeps the cursor in that position )
# 16 - Pressing control + an arrow key behaves in an inconsistent manner
# 17 - Inserting text places the cursor at the end of the inserted text
# 18 - Pressing end behaves consistently cursor wise
# 19 - Home, page up, page down, alt and hotkeys behave inconsistently cursor wise
# 20 - When a mouse click is done, we cannot be sure of the cursor position
# 21 - When a switch is made to a different program, we cannot be certain of the cursor position or that the right focus is maintained
# 22 - After a certain amount of time, we cannot be certain that we still have a consistent cursor position
# 23 - Spreadsheet programs have inconsistent cursor movement due to arrow keys moving between cells
# 24 - Screen reader software behaves consistently only when an input field is selected
# 25 - When a DESYNC is detected, we need to either search in advance to normalize our cursor position, or do nothing at all
# 26 - Autocompleting will make the history inconsistent as well as the cursor position
# 27 - Pasting will give a consistent whitespace
# 28 - From a coarse position, we can always move back to the end of the current line to have a consistent position
# 29 - By default, when a selection is made, going to the left places the cursor on the left end of the selection, and going to the right places it on the right
# 30 - Certain programs do not allow selection, like terminals
class CursorPositionTracker:
    text_history: str = ""
    enable_cursor_tracking: bool = True
    selecting_text: bool = False
    shift_down: bool = False
    selection_cursor_marker = (-1, -1)
    last_cursor_movement: str = ""

    def __init__(self):
        self.clear()

    def clear(self):
        self.set_history("")

    def disable_cursor_tracking(self):
        self.cursor_tracking_enabled = False

    def enable_cursor_tracking(self):
        self.cursor_tracking_enabled = len(self.text_history) > 0

    def apply_key(self, key: str) -> bool:
        if not self.cursor_tracking_enabled:
            return False

        key_used = False
        keys = key.lower().split(" ")
        for key in keys:
            key_modifier = key.split(":")
            if len(key_modifier) > 1 and key_modifier[-1] == "up":
                if "shift" in key:
                    self.shift_down = False
                continue

            if "alt" in key:
                self.set_history("")
                key_used = True

            # Control keys are slightly inconsistent across programs, but generally they skip a word
            elif "ctrl" in key:
                self.selecting_text = "shift" in key
                key_combinations = key_modifier[0].lower().split("-")                
                if "left" in key: 
                    left_movements = 1
                    if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                        left_movements = int(key_modifier[-1])
                    self.last_cursor_movement = "left"
                    self.track_coarse_cursor_left(left_movements)
                elif "right" in key:
                    right_movements = 1
                    if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                        right_movements = int(key_modifier[-1])

                    self.last_cursor_movement = "right"
                    self.track_coarse_cursor_right(right_movements)
                
                # Only a few items do not change the focus or cursor position for the cursor
                # But for other hotkeys the history needs to be cleared
                elif not("s" in key_combinations or "c" in key_combinations or \
                    "x" in key_combinations or "v" in key_combinations):
                    self.set_history("")
                key_used = True
            elif "shift" in key:
                self.shift_down = key_modifier[-1] == "down"
                key_used = True
            elif "left" in key:
                selecting_text = "shift" in key or self.shift_down
                left_movements = 1
                if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                    left_movements = int(key_modifier[-1])

                if selecting_text != self.selecting_text:
                    left_movements = abs(self.track_selection(selecting_text, -left_movements))

                if left_movements > 0:
                    self.track_cursor_left(left_movements)
                key_used = True
                self.last_cursor_movement = "left"
            elif "right" in key:
                selecting_text = "shift" in key or self.shift_down
                right_movements = 1
                if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                    right_movements = int(key_modifier[-1])
                
                if selecting_text != self.selecting_text:
                    right_movements = self.track_selection(selecting_text, right_movements)
                    
                if right_movements > 0:
                    self.track_cursor_right(right_movements)
                key_used = True
                self.last_cursor_movement = "right"
            elif "end" in key:
                self.mark_cursor_to_end_of_line()
                key_used = True
                self.last_cursor_movement = "right"                
            elif "home" in key:
                self.mark_line_as_coarse()
                key_used = True
                self.last_cursor_movement = "left"
            elif "up" in key:
                up_movements = 1
                if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                    up_movements = int(key_modifier[-1])
                for _ in range(up_movements):
                    self.mark_above_line_as_coarse()
                key_used = True
            elif "down" in key:
                down_movements = 1
                if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                    down_movements = int(key_modifier[-1])
                for _ in range(down_movements):
                    self.mark_below_line_as_coarse()
                key_used = True
        return key_used

    # Select a line and index it to find where we are in the current text history
    def search_line(self):
        self.cursor_tracking_enabled = False
        
        found_line_index = -1
        if self.text_history:
            with clip.revert():
                actions.edit.line_start()
                actions.edit.extend_line_end()
                text = actions.edit.selected_text()
                actions.edit.right()

            if text:
                lines = self.text_history.splitlines()
                index = -1
                for line in lines:
                    index += 1
                    # NAIVE CHECK - TODO IMPROVE MATCHING IN DIFFERENT MOMENTS
                    if line.startswith(text) or line.endswith(text):
                        found_line_index = index
                        break
        
        if found_line_index > -1:
            index = -1
            text_history = self.text_history.replace(_CURSOR_MARKER, "").replace(_COARSE_MARKER, "")
            lines = text_history.splitlines()

            before_cursor = []
            after_cursor = []
            for line in lines:
                index += 1
                if index <= found_line_index:
                    before_cursor.append(line)
                else:
                    after_cursor.append(line)
            
            before_cursor_text = "\n".join(before_cursor)
            after_cursor_text = "\n".join(after_cursor)
            if len(after_cursor) > 0:
                after_cursor_text = "\n" + after_cursor_text

            self.set_history(before_cursor_text, after_cursor_text)
        else:
            self.set_history("")

    def mark_cursor_to_end_of_line(self):
        lines = self.text_history.splitlines()
        before_cursor = []
        after_cursor = []
        before_cursor_marker = True
        for line in lines:
            if _CURSOR_MARKER in line or _COARSE_MARKER in line:
                before_cursor.append(line.replace(_CURSOR_MARKER, "").replace(_COARSE_MARKER, ""))
                before_cursor_marker = False
            else:
                if before_cursor_marker:
                    before_cursor.append(line)
                else:
                    after_cursor.append(line)

        before_cursor_text = "\n".join(before_cursor)
        after_cursor_text = "\n".join(after_cursor)
        if len(after_cursor) > 0:
            after_cursor_text = "\n" + after_cursor_text
        self.set_history(before_cursor_text, after_cursor_text)

    def mark_line_as_coarse(self, difference_from_line: int = 0):
        before_cursor = []
        after_cursor = []
        lines = self.text_history.splitlines()

        char_index = 0
        line_with_cursor = -1
        for line_index, line in enumerate(lines):
            if ( _COARSE_MARKER in line or _CURSOR_MARKER in line ):
                split_line = line.replace(_COARSE_MARKER, _CURSOR_MARKER).split(_CURSOR_MARKER)
                if len(split_line) > 1:
                    char_index = len(split_line[0])
                line_with_cursor = line_index
                break

        # If the line falls outside of the known line count, we have lost the cursor position entirely
        # And must clear the input entirely
        line_out_of_known_bounds = line_with_cursor + difference_from_line < 0 or line_with_cursor + difference_from_line > len(lines)
        if line_out_of_known_bounds:
            before_cursor = []
            after_cursor = []
        else:
            for line_index, line in enumerate(lines):
                replaced_line = line.replace(_CURSOR_MARKER, "").replace(_COARSE_MARKER, "")
                if difference_from_line == 0 and line_index < line_with_cursor:
                    before_cursor.append(replaced_line)
                elif difference_from_line != 0 and line_index <= (line_with_cursor + difference_from_line):

                    # Maintain a rough idea of the place of the coarse cursor
                    if line_index == line_with_cursor + difference_from_line:
                        if char_index >= len(replaced_line):
                            char_index = len(replaced_line)
                        before_cursor.append(replaced_line[:char_index])
                        after_cursor.append(replaced_line[char_index:])
                    else:
                        before_cursor.append(replaced_line)
                else:
                    after_cursor.append(replaced_line)
        
        before_cursor_text = "\n".join(before_cursor)
        after_cursor_text = "\n".join(after_cursor)
        if len(after_cursor) > 0:
            if difference_from_line == 0:
                before_cursor_text += "\n"
            elif char_index == 0:
                after_cursor_text = "\n" + after_cursor_text
        self.set_history(before_cursor_text, after_cursor_text, _COARSE_MARKER)

    def is_selecting(self):
        if self.selecting_text:
            cursor_index = self.get_cursor_index()
            selection = cursor_index[0] * 1000 + cursor_index[1] != self.selection_cursor_marker[0] * 1000 + self.selection_cursor_marker[1]
            if not selection:
                self.selecting_text = False

        return self.selecting_text

    def mark_above_line_as_coarse(self):
        self.mark_line_as_coarse(-1)

    def mark_below_line_as_coarse(self):
        self.mark_line_as_coarse(1)

    def track_cursor_position(self, right_amount = 0):
        is_coarse = _COARSE_MARKER in self.text_history
        if is_coarse or _CURSOR_MARKER in self.text_history:
            line_with_cursor = -1
            lines = self.text_history.splitlines()
            for line_index, line in enumerate(lines):
                if _CURSOR_MARKER in line or _COARSE_MARKER in line:
                    line_with_cursor = line_index
                    break

            items = lines[line_with_cursor].replace(_COARSE_MARKER, _CURSOR_MARKER).split(_CURSOR_MARKER)

            before_string = ""
            after_string = ""
            # Move cursor leftward
            if right_amount < 0:
                # Single line amount to the left
                if len(items[0]) >= abs(right_amount):
                    before_string = items[0][:len(items[0]) + right_amount]
                    after_string = items[0][right_amount:] + items[1]
                # Multi-line amount to the left
                else:
                    amount = abs(right_amount)
                    while amount > 0:
                        if amount > len(items[0]):
                            amount -= len(items[0]) + 1
                            line_with_cursor -= 1

                        # Early return with empty history if we move left past our selection
                        if line_with_cursor < 0:
                            self.set_history("")
                            return

                        items = [lines[line_with_cursor], ""]
                        if len(items[0]) >= amount:
                            before_string = items[0][:len(items[0]) - abs(amount)]
                            after_string = items[0][len(items[0]) - abs(amount):] + items[1]
                            amount = 0
            elif right_amount > 0:
                # Single line amount to the right
                if len(items[1]) >= right_amount:
                    before_string = items[0] + items[1][:right_amount]
                    after_string = items[1][right_amount:]
                # Multi-line amount to the right
                else:
                    amount = abs(right_amount)
                    while amount > 0:
                        if amount >= len(items[1]):
                            amount -= len(items[1])
                            if amount > 0:
                                amount -= 1
                                line_with_cursor += 1

                        # Early return with empty history if we move left past our selection
                        if line_with_cursor > len(lines) - 1:
                            self.set_history("")
                            return

                        items = ["", lines[line_with_cursor]]

                        if amount == 0:
                            before_string = items[0]
                            after_string = items[1]
                        elif len(items[1]) >= amount:
                            before_string = items[0] + items[1][:amount]
                            after_string = items[1][amount:]
                            amount = 0
            
            # Clear the history if the coarse cursor has traveled beyond a line
            # Because we do not know the line position for sure.
            if is_coarse and line_with_cursor != line_index:
                self.clear()
            
            # Determine new state
            before_cursor = []
            after_cursor = []
            for line_index, line in enumerate(lines):
                replaced_line = line.replace(_CURSOR_MARKER, "").replace(_COARSE_MARKER, "")
                if line_index < line_with_cursor:
                    before_cursor.append(replaced_line)
                elif line_index > line_with_cursor:
                    after_cursor.append(replaced_line)
                else:
                    before_cursor.append(before_string)
                    after_cursor.append(after_string)

            before_cursor_text = "\n".join(before_cursor)
            after_cursor_text = "\n".join(after_cursor)
            self.set_history(before_cursor_text, after_cursor_text)
        
        # Detect if we are still selecting items
        if self.selection_cursor_marker[0] > -1 and self.selection_cursor_marker[1] > -1:
            cursor_index = self.get_cursor_index()
            if cursor_index[0] > -1 and cursor_index[1] > -1:
                self.selecting_text = cursor_index[0] * 1000 + cursor_index[1] != self.selection_cursor_marker[0] * 1000 + self.selection_cursor_marker[1]
            else:
                self.selecting_text = False
        else:
            self.selecting_text = False

    def track_cursor_left(self, amount = 1):
        self.track_cursor_position(-amount)

    def track_cursor_right(self, amount = 1):
        self.track_cursor_position(amount)

    def track_selection(self, selecting: bool, right_amount: int = 1) -> int:
        current_index = self.get_cursor_index()

        # Remember the cursor position of the start of the selection
        if selecting:
            self.selection_cursor_marker = current_index

        # Set the cursor to the a side of the selection
        if not selecting:
            # Determine which cursor is further, applying a large multiplier to the line to make comparisons easier

            cursor = current_index
            selection = self.selection_cursor_marker
            cursor_is_left_side = cursor[0] < selection[0] or ( cursor[0] == selection[0] and cursor[1] > selection[1] )

            cursor_at_selection = False
            if right_amount > 0:
                cursor_at_selection = cursor_is_left_side
                right_amount -= 1
            elif right_amount < 0:
                cursor_at_selection = not cursor_is_left_side                    
                right_amount += 1

            # Set the cursor at the selection
            if cursor_at_selection:
                before_cursor = []
                after_cursor = []
                before_cursor_string = ""
                after_cursor_string = ""
                lines = self.text_history.splitlines()
                for line_index, line in enumerate(lines):
                    replaced_line = line.replace(_CURSOR_MARKER, "").replace(_COARSE_MARKER, "")
                    if line_index < self.selection_cursor_marker[0]:
                        before_cursor.append(replaced_line)
                    elif line_index > self.selection_cursor_marker[0]:
                        after_cursor.append(replaced_line)
                    elif line_index == self.selection_cursor_marker[0]:
                        before_cursor_string = replaced_line[:len(replaced_line) - self.selection_cursor_marker[1]]
                        after_cursor_string = replaced_line[len(replaced_line) - self.selection_cursor_marker[1]:]

                        if line_index > 0:
                            before_cursor_string = "\n" + before_cursor_string
                        if line_index < len(lines) - 1:
                            after_cursor_string += "\n"

                self.set_history("\n".join(before_cursor) + before_cursor_string, after_cursor_string + "\n".join(after_cursor))

            self.selecting_text = False
            self.selection_cursor_marker = (-1, -1)

        return right_amount
    
    def remove_selection(self) -> ((int, int), (int, int)):
        cursor_index = self.get_cursor_index()
        selection_index = self.selection_cursor_marker

        first_index = selection_index
        second_index = cursor_index
        if self.is_selecting():
            if (cursor_index[0] == selection_index[0] and cursor_index[1] > selection_index[1]) or cursor_index[0] < selection_index[0]:
                first_index = cursor_index
                second_index = selection_index

            before_cursor = []
            after_cursor = []
            before_cursor_string = ""
            after_cursor_string = ""
            lines = self.text_history.splitlines()
            for line_index, line in enumerate(lines):
                replaced_line = line.replace(_CURSOR_MARKER, "").replace(_COARSE_MARKER, "")
                if line_index < first_index[0]:
                    before_cursor.append(replaced_line)
                elif line_index > second_index[0]:
                    after_cursor.append(replaced_line)
                else:
                    if line_index == first_index[0]:
                        before_cursor_string = replaced_line[:len(replaced_line) - first_index[1]]
                        if line_index > 0:
                            before_cursor_string = "\n" + before_cursor_string                        

                    if line_index == second_index[0]:
                        after_cursor_string = replaced_line[len(replaced_line) - second_index[1]:]
                        if line_index < len(lines) - 1:
                            after_cursor_string += "\n"

            self.set_history("\n".join(before_cursor) + before_cursor_string, after_cursor_string + "\n".join(after_cursor))
            self.selecting_text = False
            self.selection_cursor_marker = (-1, -1)
        else:
            first_index = cursor_index

        return (first_index, second_index)

    def track_coarse_cursor_left(self, amount = 1):
        self.track_coarse_cursor_right(-amount)

    # Very naive coarse tracking - only considers whitespace
    def track_coarse_cursor_right(self, amount = 1):
        items = []
        if _CURSOR_MARKER in self.text_history:
            items = self.text_history.split(_CURSOR_MARKER)
        if _COARSE_MARKER in self.text_history:
            items = self.text_history.split(_COARSE_MARKER)

        line_index = 0
        if len(items) > 1:
            line_index = len(items[0].splitlines()) - 1

        if amount < 0:
            whitespace_items = self.split_string_with_punctuation(items[0])
            if len(whitespace_items) < abs(amount):
                self.clear() # Clear history because we are going past our bounds
            else:
                previous_item = whitespace_items[amount]
                index = items[0].rfind(previous_item)
                if index != -1 and line_index == len(items[0][:index].split("\n")) - 1:
                    self.set_history(items[0][:index], items[0][index:] + items[1], _COARSE_MARKER)
                    # Clear history because we are going past a line boundary and we do not know the line position
                else:
                    self.clear()

        elif amount > 0:
            whitespace_items = items[1].split()
            if len(whitespace_items) < amount:
                self.clear() # Clear history because we are going past our bounds
            else:
                next_item = whitespace_items[amount - 1]
                index = items[1].find(next_item)
                if index != -1 and line_index == len((items[0] + items[1][:index]).split("\n")) - 1:
                    index += len(next_item)
                    self.set_history(items[0] + items[1][:index], items[1][index:], _COARSE_MARKER)
                else:
                    self.clear()       

    # Synchronize the cursor position
    def set_history(self, before_cursor: str, after_cursor: str = "", marker: str = _CURSOR_MARKER):
        if before_cursor + after_cursor:
            self.text_history = before_cursor + marker + after_cursor
        else:
            self.text_history = ""
        self.enable_cursor_tracking()

    def append_before_cursor(self, before_cursor_text: str):
        items = self.text_history.split(_CURSOR_MARKER)
        items[0] += before_cursor_text
        after_cursor = ""
        if len(items) > 1:
            after_cursor = items[1]
        self.set_history(items[0], after_cursor)

    def remove_before_cursor(self, remove_character_count: int):
        items = self.text_history.split(_CURSOR_MARKER)
        after_cursor = ""
        if len(items) > 1:
            after_cursor = items[1]
        before_cursor = "" if len(items[0]) <= remove_character_count else items[0][:-remove_character_count]
        self.set_history(before_cursor, after_cursor)

    def remove_after_cursor(self, remove_character_count: int):
        items = self.text_history.split(_CURSOR_MARKER)
        before_cursor = items[0]
        after_cursor = ""
        if len(items) > 1:
            after_cursor = items[1]
        after_cursor = "" if len(items[1]) <= remove_character_count else items[1][remove_character_count:]
        self.set_history(before_cursor, after_cursor)

    def get_cursor_index(self, check_coarse = False) -> (int, int):
        line_index = -1
        character_index = -1
        lines = self.text_history.splitlines()
        if _CURSOR_MARKER in self.text_history:
            for index, line in enumerate(lines):
                if _CURSOR_MARKER in line:
                    line_index = index
                    character_index = len(line.split(_CURSOR_MARKER)[1])
                    break
        
        if _COARSE_MARKER in self.text_history:
            for index, line in enumerate(lines):
                if _COARSE_MARKER in line:
                    line_index = index
                    character_index = len(line.split(_COARSE_MARKER)[1]) if check_coarse else -1
                    break

        return line_index, character_index
    
    def split_string_with_punctuation(self, text: str) -> List[str]:
        return re.sub(r"[" + re.escape("!\"#$%&'()*+, -./:;<=>?@[\\]^`{|}~") + "]+", " ", text).split()

    def navigate_to_position(self, line_index: int, character_from_end: int, deselection: bool = True) -> List[str]:
        current = self.get_cursor_index()

        keys = []
        if deselection:
            if self.shift_down:
                keys.append("shift:up")
            
            if self.is_selecting():
                selection = self.selection_cursor_marker

                # If we are dealing with a coarse cursor, navigate from the selection start point instead to have a known starting point
                favour_selection = False
                if current[1] == -1 and selection[1] != -1:
                    favour_selection = True
                # Favor the closest end to the desired character
                else:
                    if current[0] == selection[0] and line_index == current[0]:
                        favour_selection = abs(selection[1] - character_from_end) < abs(current[1] - character_from_end)
                    elif current[0] == line_index:
                        favour_selection = False
                    elif selection[0] == line_index:
                        favour_selection = True
                    else:
                        favour_selection = abs(selection[0] - line_index) < abs(current[0] - line_index)

                if favour_selection:
                    current = selection

                coarse_cursor = self.get_cursor_index(True)
                if coarse_cursor[0] < selection[0]:
                    keys.append("right" if favour_selection else "left")
                elif coarse_cursor[0] > selection[0]:
                    keys.append("left" if favour_selection else "right")
                else:
                    if favour_selection:
                        keys.append("left" if selection[1] > coarse_cursor[1] else "right")
                    else:
                        keys.append("left" if selection[1] < coarse_cursor[1] else "right")

        if not line_index == current[0] and line_index != -1:
            difference = current[0] - line_index

            # Reset any auto correct items before making large character changes
            # For example in VSCODE
            keys.append( "left right" )

            # Move up or down multiple times depending on how many lines we need to cross
            if abs(difference) == 1:
                keys.append("down" if difference < 0 else "up")
            else:
                keys.append( ("down:" if difference < 0 else "up:" ) + str(abs(difference)) )
            current = (line_index, -1)

        # Move to line end to have a consistent line ending, as that seems to be consistent
        if current[1] == -1:
            keys.append( "end" )
            current = (current[0], 0)

        # Move to the right character position
        if not character_from_end == current[1] and current[1] != -1:
            char_diff = current[1] - character_from_end
            keys.append(("left:" if char_diff < 0 else "right:") + str(abs(char_diff)))

        if current[0] == -1 or current[1] == -1:
            keys = []

        return keys