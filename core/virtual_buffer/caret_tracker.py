from typing import List
import re
import platform

# CARET MARKERS
 # TODO APPEND RANDOM NUMBER FOR LESS COLLISIONS?
_CARET_MARKER = "$CARET" # Keeps track of the exact caret position
_COARSE_MARKER = "$COARSE_CARET" # Keeps track of the line number if we arent sure what character we are on

# SHOULD SUPPORT:
# MULTI LINE TEXT
# SINGLE LINE TEXT
# SELECTION DETECTION
# CONTEXT CLEARING
# MOVING TO WORDS WITHIN THE BUFFER
# MULTIPLE KEY STROKES
# KEYSTROKE DETECTION

# Class to keep track of the caret position in the recently inserted text
# There are some assumptions made in order for this to work
#
# 1 - On the first line, we cannot go up or past the start of the line, as other text might be in front of it
# 2 - On the last line, we cannot go down or past the end of the line, as other text might be after it
# 3 - Going left and going right moves the caret in a predictable manner
# 4 - Going left and going right might skip over to another line, it isn't bounded
# 5 - Going up moves to an inconsistent place inside the above line
# 6 - Going down moves to an inconsistent place inside the below line
# 7 - When we are dealing with word wrapping, which happens in non-terminal and IDE environments, going up and down might not even go on the next line
# 8 - Pressing (shift-)enter will insert a new line with an unknown amount of whitespace
# 9 - Pressing tab will insert an unknown amount of whitespace ( either a tab, or N amount of space characters )
# 10 - If we select text and press right, the caret will always appear on the right of the selection and end the selection
# 11 - If we select text and press left, the caret will appear on an inconsistent place depending on the program
# 12 - If we select a whole line and read its contents, we can determine the position of the caret within the text buffer
# 13 - Pressing backspace behaves inconsistently
# 14 - Pressing backspace before whitespace behaves inconsistently in some programs ( IDEs )
# 15 - Pressing backspace with a selection behaves consistently ( removes the selection and keeps the caret in that position )
# 16 - Pressing control + an arrow key behaves in an inconsistent manner
# 17 - Inserting text places the caret at the end of the inserted text
# 18 - Pressing end behaves consistently caret wise
# 19 - Home, page up, page down, alt and hotkeys behave inconsistently caret wise
# 20 - When a mouse click is done, we cannot be sure of the caret position
# 21 - When a switch is made to a different program, we cannot be certain of the caret position or that the right focus is maintained
# 22 - After a certain amount of time, we cannot be certain that we still have a consistent caret position
# 23 - Spreadsheet programs have inconsistent caret movement due to arrow keys moving between cells
# 24 - Screen reader software behaves consistently only when an input field is selected
# 25 - When a DESYNC is detected, we need to either search in advance to normalize our caret position, or do nothing at all
# 26 - Autocompleting will make the buffer inconsistent as well as the caret position
# 27 - Pasting will give a consistent whitespace
# 28 - From a coarse position, we can always move back to the end of the current line to have a consistent position
# 29 - By default, when a selection is made, going to the left places the caret on the left end of the selection, and going to the right places it on the right
# 30 - Certain programs do not allow selection, like terminals
class CaretTracker:
    system: str = ""
    is_macos: bool = False
    text_buffer: str = ""
    enable_caret_tracking: bool = True
    selecting_text: bool = False
    shift_down: bool = False
    selection_caret_marker = (-1, -1)
    last_caret_movement: str = ""

    def __init__(self, system = platform.system()):
        self.system = system
        self.is_macos = system == "Darwin"
        self.clear()

    def clear(self):
        self.set_buffer("")

    def disable_caret_tracking(self):
        self.caret_tracking_enabled = False

    def enable_caret_tracking(self):
        self.caret_tracking_enabled = len(self.text_buffer) > 0

    def apply_key(self, key: str) -> bool:
        if not self.caret_tracking_enabled:
            return False
        
        key_used = False
        keys = key.lower().split(" ")
        for key in keys:
            key_modifier = key.split(":")
            if len(key_modifier) > 1 and key_modifier[-1] == "up":
                if "shift" in key:
                    self.shift_down = False
                continue

            if self.is_macos:
                if "alt" in key:
                    self.selecting_text = "shift" in key or self.shift_down
                    key_combinations = key_modifier[0].lower().split("-")                
                    if "left" in key: 
                        left_movements = 1
                        if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                            left_movements = int(key_modifier[-1])
                        self.last_caret_movement = "left"
                        self.track_coarse_caret_left(left_movements)
                        key_used = True
                    elif "right" in key:
                        right_movements = 1
                        if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                            right_movements = int(key_modifier[-1])

                        self.last_caret_movement = "right"
                        self.track_coarse_caret_right(right_movements)
                        key_used = True
                # TODO PROPER CMD / SUPER TRACKING?
            else:
                # TODO PROPER ALT TRACKING? FOR NOW TURNED OFF SO WE KEEP CONTEXT DURING PROGRAM SWITCHES
                if "alt" in key:
                    key_used = True

                # Control keys are slightly inconsistent across programs, but generally they skip a word
                elif "ctrl" in key:
                    self.selecting_text = "shift" in key or self.shift_down
                    key_combinations = key_modifier[0].lower().split("-")                
                    if "left" in key: 
                        left_movements = 1
                        if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                            left_movements = int(key_modifier[-1])
                        self.last_caret_movement = "left"
                        self.track_coarse_caret_left(left_movements)
                    elif "right" in key:
                        right_movements = 1
                        if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                            right_movements = int(key_modifier[-1])

                        self.last_caret_movement = "right"
                        self.track_coarse_caret_right(right_movements)
                    
                    # Only a few items do not change the focus or caret position for the caret
                    # But for other hotkeys the buffer needs to be cleared
                    elif not("s" in key_combinations or "c" in key_combinations or \
                        "x" in key_combinations or "v" in key_combinations):
                        self.set_buffer("")
                    key_used = True

            # Noop if it has already been used
            if key_used == True:
                return key_used
                
            # Only track a shift down if it is the ONLY key pressed down
            elif "shift" == key_modifier[0]:
                self.shift_down = key_modifier[-1] == "down"
                if self.shift_down and self.selection_caret_marker == (-1, -1):
                    self.selection_caret_marker = self.get_caret_index()

                key_used = True
            elif "left" in key and not ("cmd" in key or "super" in key):
                selecting_text = "shift" in key or self.shift_down
                left_movements = 1
                if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                    left_movements = int(key_modifier[-1])

                if selecting_text != self.selecting_text or selecting_text == True:
                    left_movements = abs(self.track_selection(selecting_text, -left_movements))

                if left_movements > 0:
                    self.track_caret_left(left_movements)
                key_used = True
                self.last_caret_movement = "left"
            elif "right" in key and not ("cmd" in key or "super" in key):
                selecting_text = "shift" in key or self.shift_down
                right_movements = 1
                if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                    right_movements = int(key_modifier[-1])
                
                if selecting_text != self.selecting_text or selecting_text == True:
                    right_movements = self.track_selection(selecting_text, right_movements)

                if right_movements > 0:
                    self.track_caret_right(right_movements)
                key_used = True
                self.last_caret_movement = "right"
            elif ( not self.is_macos and "end" in key ) or ( self.is_macos and ("cmd" in key or "super" in key) and "right" in key ):
                self.mark_caret_to_end_of_line()
                key_used = True
                self.last_caret_movement = "right"
            elif ( not self.is_macos and "home" in key ) or ( self.is_macos and ("cmd" in key or "super" in key) and "left" in key ):
                self.mark_line_as_coarse()
                key_used = True
                self.last_caret_movement = "left"
            elif "up" in key and ( not self.is_macos or ("cmd" not in key and "super" not in key)):
                up_movements = 1
                if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                    up_movements = int(key_modifier[-1])
                for _ in range(up_movements):
                    self.mark_above_line_as_coarse()
                key_used = True
            elif "down" in key and ( not self.is_macos or ("cmd" not in key and "super" not in key)):
                down_movements = 1
                if len(key_modifier) >= 1 and key_modifier[-1].isnumeric():
                    down_movements = int(key_modifier[-1])
                for _ in range(down_movements):
                    self.mark_below_line_as_coarse()
                key_used = True
        return key_used

    def mark_caret_to_end_of_line(self):
        lines = self.text_buffer.splitlines()
        before_caret = []
        after_caret = []
        before_caret_marker = True
        for line in lines:
            if _CARET_MARKER in line or _COARSE_MARKER in line:
                before_caret.append(line.replace(_CARET_MARKER, "").replace(_COARSE_MARKER, ""))
                before_caret_marker = False
            else:
                if before_caret_marker:
                    before_caret.append(line)
                else:
                    after_caret.append(line)

        before_caret_text = "\n".join(before_caret)
        after_caret_text = "\n".join(after_caret)
        if len(after_caret) > 0:
            after_caret_text = "\n" + after_caret_text
        self.set_buffer(before_caret_text, after_caret_text)

    def mark_line_as_coarse(self, difference_from_line: int = 0):
        before_caret = []
        after_caret = []
        lines = self.text_buffer.splitlines()

        char_index = 0
        line_with_caret = -1
        for line_index, line in enumerate(lines):
            if ( _COARSE_MARKER in line or _CARET_MARKER in line ):
                split_line = line.replace(_COARSE_MARKER, _CARET_MARKER).split(_CARET_MARKER)
                if len(split_line) > 1:
                    char_index = len(split_line[0])
                line_with_caret = line_index
                break

        # If the line falls outside of the known line count, we have lost the caret position entirely
        # And must clear the input entirely
        line_out_of_known_bounds = line_with_caret + difference_from_line < 0 or line_with_caret + difference_from_line > len(lines)
        if line_out_of_known_bounds:
            before_caret = []
            after_caret = []
        else:
            for line_index, line in enumerate(lines):
                replaced_line = line.replace(_CARET_MARKER, "").replace(_COARSE_MARKER, "")
                if difference_from_line == 0 and line_index < line_with_caret:
                    before_caret.append(replaced_line)
                elif difference_from_line != 0 and line_index <= (line_with_caret + difference_from_line):

                    # Maintain a rough idea of the place of the coarse caret
                    if line_index == line_with_caret + difference_from_line:
                        if char_index >= len(replaced_line):
                            char_index = len(replaced_line)
                        before_caret.append(replaced_line[:char_index])
                        after_caret.append(replaced_line[char_index:])
                    else:
                        before_caret.append(replaced_line)
                else:
                    after_caret.append(replaced_line)
        
        before_caret_text = "\n".join(before_caret)
        after_caret_text = "\n".join(after_caret)
        if len(after_caret) > 0:
            if difference_from_line == 0:
                before_caret_text += "\n"
            elif char_index == 0:
                after_caret_text = "\n" + after_caret_text
        self.set_buffer(before_caret_text, after_caret_text, _COARSE_MARKER)

    def is_selecting(self):
        if self.selecting_text:
            caret_index = self.get_caret_index()
            selection = caret_index[0] * 1000 + caret_index[1] != self.selection_caret_marker[0] * 1000 + self.selection_caret_marker[1]
            if not selection:
                self.selecting_text = False

        return self.selecting_text

    def mark_above_line_as_coarse(self):
        self.mark_line_as_coarse(-1)

    def mark_below_line_as_coarse(self):
        self.mark_line_as_coarse(1)

    def track_caret_position(self, right_amount = 0):
        is_coarse = _COARSE_MARKER in self.text_buffer
        if is_coarse or _CARET_MARKER in self.text_buffer:
            line_with_caret = -1
            lines = self.text_buffer.splitlines()
            for line_index, line in enumerate(lines):
                if _CARET_MARKER in line or _COARSE_MARKER in line:
                    line_with_caret = line_index
                    break

            items = lines[line_with_caret].replace(_COARSE_MARKER, _CARET_MARKER).split(_CARET_MARKER)

            before_string = ""
            after_string = ""
            # Move caret leftward
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
                            line_with_caret -= 1

                        # Early return with empty buffer if we move left past our selection
                        if line_with_caret < 0:
                            self.set_buffer("")
                            return

                        items = [lines[line_with_caret], ""]
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
                                line_with_caret += 1

                        # Early return with empty buffer if we move left past our selection
                        if line_with_caret > len(lines) - 1:
                            self.set_buffer("")
                            return

                        items = ["", lines[line_with_caret]]

                        if amount == 0:
                            before_string = items[0]
                            after_string = items[1]
                        elif len(items[1]) >= amount:
                            before_string = items[0] + items[1][:amount]
                            after_string = items[1][amount:]
                            amount = 0
            
            # Clear the buffer if the coarse caret has traveled beyond a line
            # Because we do not know the line position for sure.
            if is_coarse and line_with_caret != line_index:
                self.clear()
            
            # Determine new state
            before_caret = []
            after_caret = []
            for line_index, line in enumerate(lines):
                replaced_line = line.replace(_CARET_MARKER, "").replace(_COARSE_MARKER, "")
                if line_index < line_with_caret:
                    before_caret.append(replaced_line)
                elif line_index > line_with_caret:
                    after_caret.append(replaced_line)
                else:
                    before_caret.append(before_string)
                    after_caret.append(after_string)

            before_caret_text = "\n".join(before_caret)
            after_caret_text = "\n".join(after_caret)
            self.set_buffer(before_caret_text, after_caret_text)
        
        # Detect if we are still selecting items
        if self.selection_caret_marker[0] > -1 and self.selection_caret_marker[1] > -1:
            caret_index = self.get_caret_index()
            if caret_index[0] > -1 and caret_index[1] > -1:
                self.selecting_text = caret_index[0] * 1000 + caret_index[1] != self.selection_caret_marker[0] * 1000 + self.selection_caret_marker[1]
            else:
                self.selecting_text = False
        else:
            self.selecting_text = False

    def track_caret_left(self, amount = 1):
        self.track_caret_position(-amount)

    def track_caret_right(self, amount = 1):
        self.track_caret_position(amount)

    def track_selection(self, selecting: bool, right_amount: int = 1) -> int:
        current_index = self.get_caret_index()

        # Remember the caret position of the start of the selection if we do not have a selection yet
        if selecting and self.selection_caret_marker == (-1, -1):
            self.selection_caret_marker = current_index

        # Set the caret to the a side of the selection
        if not selecting:
            # Determine which caret is further, applying a large multiplier to the line to make comparisons easier

            caret = current_index
            selection = self.selection_caret_marker
            caret_is_left_side = caret[0] < selection[0] or ( caret[0] == selection[0] and caret[1] > selection[1] )

            caret_at_selection = False
            if right_amount > 0:
                caret_at_selection = caret_is_left_side
                right_amount -= 1
            elif right_amount < 0:
                caret_at_selection = not caret_is_left_side                    
                right_amount += 1

            # Set the caret at the selection
            if caret_at_selection:
                before_caret = []
                after_caret = []
                before_caret_string = ""
                after_caret_string = ""
                lines = self.text_buffer.splitlines()
                for line_index, line in enumerate(lines):
                    replaced_line = line.replace(_CARET_MARKER, "").replace(_COARSE_MARKER, "")
                    if line_index < self.selection_caret_marker[0]:
                        before_caret.append(replaced_line)
                    elif line_index > self.selection_caret_marker[0]:
                        after_caret.append(replaced_line)
                    elif line_index == self.selection_caret_marker[0]:
                        before_caret_string = replaced_line[:len(replaced_line) - self.selection_caret_marker[1]]
                        after_caret_string = replaced_line[len(replaced_line) - self.selection_caret_marker[1]:]

                        if line_index > 0:
                            before_caret_string = "\n" + before_caret_string
                        if line_index < len(lines) - 1:
                            after_caret_string += "\n"

                self.set_buffer("\n".join(before_caret) + before_caret_string, after_caret_string + "\n".join(after_caret))

            self.selecting_text = False
            self.selection_caret_marker = (-1, -1)

        return right_amount
    
    def remove_selection(self) -> ((int, int), (int, int)):
        caret_index = self.get_caret_index()
        selection_index = self.selection_caret_marker

        first_index = selection_index
        second_index = caret_index
        if self.is_selecting():
            if (caret_index[0] == selection_index[0] and caret_index[1] > selection_index[1]) or caret_index[0] < selection_index[0]:
                first_index = caret_index
                second_index = selection_index

            before_caret = []
            after_caret = []
            before_caret_string = ""
            after_caret_string = ""
            lines = self.text_buffer.splitlines()
            for line_index, line in enumerate(lines):
                replaced_line = line.replace(_CARET_MARKER, "").replace(_COARSE_MARKER, "")
                if line_index < first_index[0]:
                    before_caret.append(replaced_line)
                elif line_index > second_index[0]:
                    after_caret.append(replaced_line)
                else:
                    if line_index == first_index[0]:
                        before_caret_string = replaced_line[:len(replaced_line) - first_index[1]]
                        if line_index > 0:
                            before_caret_string = "\n" + before_caret_string                        

                    if line_index == second_index[0]:
                        after_caret_string = replaced_line[len(replaced_line) - second_index[1]:]
                        if line_index < len(lines) - 1:
                            after_caret_string += "\n"

            self.set_buffer("\n".join(before_caret) + before_caret_string, after_caret_string + "\n".join(after_caret))
            self.selecting_text = False
            self.selection_caret_marker = (-1, -1)
        else:
            first_index = caret_index

        return (first_index, second_index)

    def track_coarse_caret_left(self, amount = 1):
        self.track_coarse_caret_right(-amount)

    # Very naive coarse tracking - only considers whitespace
    def track_coarse_caret_right(self, amount = 1):
        items = []
        if _CARET_MARKER in self.text_buffer:
            items = self.text_buffer.split(_CARET_MARKER)
        if _COARSE_MARKER in self.text_buffer:
            items = self.text_buffer.split(_COARSE_MARKER)

        line_index = 0
        if len(items) > 1:
            line_index = len(items[0].splitlines()) - 1

        if amount < 0:
            whitespace_items = self.split_string_with_punctuation(items[0])
            if len(whitespace_items) < abs(amount):
                self.clear() # Clear buffer because we are going past our bounds
            else:
                previous_item = whitespace_items[amount]
                index = items[0].rfind(previous_item)
                if index != -1 and line_index == len(items[0][:index].split("\n")) - 1:
                    self.set_buffer(items[0][:index], items[0][index:] + items[1], _COARSE_MARKER)
                    # Clear buffer because we are going past a line boundary and we do not know the line position
                else:
                    self.clear()

        elif amount > 0:
            whitespace_items = items[1].split()
            if len(whitespace_items) < amount:
                self.clear() # Clear buffer because we are going past our bounds
            else:
                next_item = whitespace_items[amount - 1]
                index = items[1].find(next_item)
                if index != -1 and line_index == len((items[0] + items[1][:index]).split("\n")) - 1:
                    index += len(next_item)
                    self.set_buffer(items[0] + items[1][:index], items[1][index:], _COARSE_MARKER)
                else:
                    self.clear()       

    # Synchronize the caret position
    def set_buffer(self, before_caret: str, after_caret: str = "", marker: str = _CARET_MARKER):
        if before_caret + after_caret:
            self.text_buffer = before_caret + marker + after_caret
        else:
            self.text_buffer = ""
        self.enable_caret_tracking()

    def append_before_caret(self, before_caret_text: str):
        items = self.text_buffer.split(_CARET_MARKER)
        items[0] += before_caret_text
        after_caret = ""
        if len(items) > 1:
            after_caret = items[1]
        self.set_buffer(items[0], after_caret)

    def remove_before_caret(self, remove_character_count: int):
        items = self.text_buffer.split(_CARET_MARKER)
        after_caret = ""
        if len(items) > 1:
            after_caret = items[1]
        before_caret = "" if len(items[0]) <= remove_character_count else items[0][:-remove_character_count]
        self.set_buffer(before_caret, after_caret)

    def remove_after_caret(self, remove_character_count: int):
        items = self.text_buffer.split(_CARET_MARKER)
        before_caret = items[0]
        after_caret = ""
        if len(items) > 1:
            after_caret = items[1]
        after_caret = "" if len(items[1]) <= remove_character_count else items[1][remove_character_count:]
        self.set_buffer(before_caret, after_caret)

    def get_caret_index(self, check_coarse = False) -> (int, int):
        line_index = -1
        character_index = -1
        lines = self.text_buffer.splitlines()
        if _CARET_MARKER in self.text_buffer:
            for index, line in enumerate(lines):
                if _CARET_MARKER in line:
                    line_index = index
                    character_index = len(line.split(_CARET_MARKER)[1])
                    break
        
        if _COARSE_MARKER in self.text_buffer:
            for index, line in enumerate(lines):
                if _COARSE_MARKER in line:
                    line_index = index
                    character_index = len(line.split(_COARSE_MARKER)[1]) if check_coarse else -1
                    break

        return line_index, character_index
    
    def get_leftmost_caret_index(self, check_coarse = False) -> (int, int):
        caret_index = self.get_caret_index(check_coarse)
        chosen_index = caret_index
        if self.is_selecting():
            selection_index = self.selection_caret_marker
            if selection_index[0] < caret_index[0]:
                chosen_index = selection_index
            elif selection_index[0] == caret_index[0] and selection_index[1] > caret_index[1]:
                chosen_index = selection_index

        return chosen_index

    def get_rightmost_caret_index(self, check_coarse = False) -> (int, int):
        leftmost_index = self.get_leftmost_caret_index(check_coarse)
        return self.get_caret_index(check_coarse) if not self.is_selecting() or self.get_caret_index(check_coarse) != leftmost_index else self.selection_caret_marker

    def split_string_with_punctuation(self, text: str) -> List[str]:
        return re.sub(r"[" + re.escape("!\"#$%&'()*+, -./:;<=>?@[\\]^`{|}~") + "]+", " ", text).split()
    
    def get_selection_text(self) -> str:
        selection_lines = []
        if self.is_selecting():
            left = self.get_leftmost_caret_index(True)
            right = self.get_rightmost_caret_index(True)

            lines = self.text_buffer.splitlines()
            for line_index, line in enumerate(lines):
                replaced_line = line.replace(_CARET_MARKER, '').replace(_COARSE_MARKER, '')
                if line_index == left[0] and line_index == right[0]:
                    selection_lines.append(replaced_line[len(replaced_line) - left[1]:len(replaced_line) - right[1]])
                elif line_index == left[0] and line_index < right[0]:
                    selection_lines.append( replaced_line[len(replaced_line) - left[1]] )
                elif line_index > left[0] and line_index < right[0]:
                    selection_lines.append( replaced_line )
                elif line_index > left[0] and line_index == right[0]:
                    selection_lines.append( replaced_line[:len(replaced_line) - right[1]] )
        return "\n".join(selection_lines)

    def navigate_to_position(self, line_index: int, character_from_end: int, deselection: bool = True, selecting: bool = None) -> List[str]:
        current = self.get_caret_index()

        keys = []
        if deselection:
            if self.shift_down:
                keys.append("shift:up")
            
            if self.is_selecting():
                selection = self.selection_caret_marker

                # If we are dealing with a coarse caret, navigate from the selection start point instead to have a known starting point
                favour_selection = False
                if current[1] == -1 and selection[1] != -1:
                    favour_selection = True
                # Favor the closest end to the desired character
                else:
                    if current[0] == selection[0] and line_index == current[0]:
                        # When going left, we need to move from the largest character count from the end
                        if character_from_end > current[1] and character_from_end > selection[1]:
                            favour_selection = selection[1] > current[1]
                        # Otherwise we need to move from the smallest
                        elif character_from_end < current[1] and character_from_end < selection[1]:
                            favour_selection = selection[1] < current[1]
                        # If the selection is in between the current selection, pick the nearest end to the place we need to go
                        else:
                            favour_selection = abs(selection[1] - character_from_end) < abs(current[1] - character_from_end)

                    elif current[0] == line_index:
                        favour_selection = False
                    elif selection[0] == line_index:
                        favour_selection = True
                    else:
                        favour_selection = abs(selection[0] - line_index) < abs(current[0] - line_index)

                if favour_selection:
                    current = selection

                coarse_caret = self.get_caret_index(True)
                if coarse_caret[0] < selection[0]:
                    keys.append("right" if favour_selection else "left")
                elif coarse_caret[0] > selection[0]:
                    keys.append("left" if favour_selection else "right")
                else:
                    if favour_selection:
                        keys.append("left" if selection[1] > coarse_caret[1] else "right")
                    else:
                        keys.append("left" if selection[1] < coarse_caret[1] else "right")

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
            keys.append("end" if not self.is_macos else "cmd-right")
            current = (current[0], 0)

        # Move to the right character position
        if not character_from_end == current[1] and current[1] != -1:
            char_diff = current[1] - character_from_end
            renewed_selection = selecting and not deselection and not self.shift_down
            keys.append( ("shift-" if renewed_selection else "" ) + ("left:" if char_diff < 0 else "right:") + str(abs(char_diff)))

        if current[0] == -1 or current[1] == -1:
            keys = []

        return keys