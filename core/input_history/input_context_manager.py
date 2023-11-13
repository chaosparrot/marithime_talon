from talon import ui, actions, clip
from .input_context import InputContext
from .input_indexer import InputIndexer
from .cursor_position_tracker import _CURSOR_MARKER
import time
from typing import List
from .formatters.text_formatter import TextFormatter
from .formatters.formatters import FORMATTERS_LIST
from .input_indexer import text_to_input_history_events
from ..utils.levenshtein import levenshtein
import os

# Class keeping track of all the different contexts availa ble
class InputContextManager:

    indexer: InputIndexer = None
    current_context: InputContext = None
    contexts: List[InputContext] = None
    last_clear_check = time.perf_counter()
    use_last_set_formatter = False
    active_formatters: List[TextFormatter]
    formatter_names: List[str]

    last_title: str = ""
    last_pid: int = -1

    def __init__(self):
        self.indexer = InputIndexer(FORMATTERS_LIST.values())
        self.contexts = []
        self.active_formatters = []
        self.formatter_names = []
        self.switch_context(ui.active_window())

    def switch_context(self, window) -> bool:
        name, title, pid = self.get_window_context(window)

        if name and title and pid != -1:
            context_to_switch_to = None
            for context in self.contexts:
                if context.match_pattern(name, title, pid):
                    context_to_switch_to = context
                    break
                elif context.coarse_match_pattern(name, title, pid):
                    accessible_content = self.index_accessible_value()
                    context.input_history_manager.cursor_position_tracker.text_history

                    normalized_accessible_content = "".join(accessible_content.lower().split())
                    normalized_context = "".join(context.input_history_manager.cursor_position_tracker.text_history.lower().split())
                    comparison = levenshtein(normalized_accessible_content, normalized_context)

                    if (len(normalized_context) - comparison) > len(normalized_context) * 0.9:
                        context.update_pattern(name, title, pid)
                        context_to_switch_to = context
                        break

            self.current_context = context_to_switch_to
            return self.current_context is not None
        return False
    
    def set_formatter(self, formatter_name: str):
        if formatter_name in FORMATTERS_LIST:
            self.active_formatters = [FORMATTERS_LIST[formatter_name]]
            self.indexer.set_default_formatter(FORMATTERS_LIST[formatter_name])
            self.formatter_names = [formatter_name]
            self.should_use_last_formatter(True)

    def get_formatter(self, context_formatter: str = "") -> TextFormatter:
        default_formatter = self.active_formatters[0] if self.use_last_set_formatter and len(self.active_formatters) > 0 else None
        chosen_formatter = default_formatter
        if context_formatter:
            chosen_formatter = FORMATTERS_LIST[context_formatter] if context_formatter in FORMATTERS_LIST else default_formatter
        
        return chosen_formatter

    def apply_key(self, key: str):
        current_context = self.get_current_context()
        current_context.apply_key(key)

    def track_insert(self, insert: str, phrase: str = None):
        ihm = self.get_current_context().input_history_manager
        input_events = []
        formatters = ihm.get_current_formatters()
        if self.use_last_set_formatter or len(formatters) == 0:
            formatters = self.formatter_names

        # Automatic insert splitting if no explicit phrase is given
        if phrase == "" and " " in insert:
            inserts = insert.split(" ")
            for index, text in enumerate(inserts):
                if index < len(inserts) - 1:
                    text += " "
                
                input_events.extend(text_to_input_history_events(text, None, "|".join(formatters)))
        else:
            input_events = text_to_input_history_events(insert, phrase, "|".join(formatters))
        ihm.insert_input_events(input_events)

    def get_window_context(self, window) -> (str, str, int):
        pid = -1
        title = ""
        app_name = ""
        #print( window )
        # We only decide on a valid PID and Title if
        # 1 - The app is enabled
        # 2 - The app is visible
        # 3 - The app has a rectangle ( for window )
        # 4 - The window isn't 0 pixels
        # 5 - The window is inside of the current screen
        if window.app and window.enabled and not window.app.background and not window.hidden and window.rect:
            # Detect whether or not the window is in the current screen
            if window.rect.width * window.rect.height > 0 and \
                ( window.rect.x >= window.screen.x or \
                window.rect.x <= window.screen.x + window.screen.width ) and \
                ( window.rect.y >= window.screen.y or \
                window.rect.y <= window.screen.y + window.screen.height ):

                pid = window.app.pid
                app_name = window.app.name
                title = window.title
        
        self.clear_stale_contexts()

        self.last_pid = pid
        self.last_app_name = app_name
        self.last_title = title
        return (app_name, title, pid)
    
    def create_context(self):
        self.current_context = InputContext(self.last_app_name, self.last_title, self.last_pid)
        self.contexts.append(self.current_context)
    
    def clear_stale_contexts(self):
        # Only check stale contexts every minute
        if time.perf_counter() - self.last_clear_check > 60:
            contexts_to_clear = []
            for index, context in enumerate(self.contexts):
                if context.is_stale(300):
                    contexts_to_clear.append(index)
            
            while len(contexts_to_clear) > 0:
                context_index = contexts_to_clear[-1]
                print( "REMOVING STALE! " + self.contexts[context_index].key_matching, context_index )
                self.contexts[context_index].clear_context()
                if self.contexts[context_index] != self.current_context:
                    self.contexts[context_index].destroy()
                    del self.contexts[context_index]
                del contexts_to_clear[-1]

    def get_current_context(self) -> InputContext:
        if self.current_context:
            if self.current_context.pid == -1:
                self.switch_context(ui.active_window())

            self.current_context.update_modified_at()
            self.clear_stale_contexts()
        else:
            self.create_context()

        return self.current_context

    def close_context(self, window):
        title = window.title
        name = "" if window.app is None else window.app.name
        pid = -1 if window.app is None else window.app.pid

        if title and pid > -1:
            contexts_to_clear = []
            for index, context in enumerate(self.contexts):
                if context.match_pattern(title, name, pid):
                    contexts_to_clear.append(index)

            should_clear_context = len(contexts_to_clear) > 0
            if should_clear_context:
                while len(contexts_to_clear) > 0:
                    remove_index = contexts_to_clear[-1]
                    self.contexts[remove_index].destroy()
                    del self.contexts[remove_index]
                    del contexts_to_clear[-1]

                    print( "----- CLOSING " + title, pid )

                self.clear_stale_contexts()

    def should_use_last_formatter(self, use_last_formatter: bool):
        self.use_last_set_formatter = use_last_formatter

    def index_accessible_value(self):
        value = ""
        print( "----- CHECKING ACCESSIBLE TEXT" )
        try:
            element = ui.focused_element()
            if "Value" in element.patterns:
                value = element.value_pattern.value
            elif "Text2" in element.patterns:
                value = element.text_pattern2.value
            elif "Text" in element.patterns:
                value = element.text_pattern.value
            #print( "CARET!", element.patterns )
            #print( "RANGE", dir(element.text_pattern2.caret_range) )
            #print( "TEXT_PATERN!", dir(element.text_pattern2) )# element.text_pattern.value )
            #print( "TEXT_PATERN 2!", dir(element) )            
            value = element.value_pattern.value
        except: # Windows sometimes throws a success error, otherwise ui.UIErr
            pass
        return value
    
    def index_file(self, file_path: str):
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    file_contents = file.read()
            else:
                file_contents = ""
        except:
            file_contents = ""

        self.index_content(file_contents)

    def index_textarea(self, total_value: str = "", forced = True):
        total_value = self.index_accessible_value() if total_value == "" else total_value
        print( "A11Y", total_value )
        results = self.find_cursor_position(total_value, 1 if forced == True else 0)
        print( results )
        self.index_content(results[0], results[1], results[2])

    def zero_width_space_insertion_index(self) -> (int, int):
        zwsp = "​"
        actions.insert(zwsp)
        actions.sleep("50ms")
        total_value = self.index_accessible_value()
        actions.key("backspace")
        return self.indexer.determine_cursor_position(zwsp, total_value)
    
    def find_cursor_position(self, total_value: str, visibility_level = 0) -> (str, (int, int), (int, int)):
        undefined_positions = (total_value, (-1, -1), (-1, -1))
        before_text = ""
        after_text = ""

        # Find selection first if it exists
        current_clipboard = ""
        selected_text = ""
        with clip.revert():
            current_clipboard = clip.text()
            actions.sleep("200ms")
            
            with clip.capture() as current_selection:
                actions.edit.copy()
            actions.sleep("200ms")

            try:
                selected_text = current_selection.text()
                is_selected = current_selection.text() == current_clipboard
            except clip.NoChange:
                is_selected = True
            
            # If there is a selection, try out if our selection can be found in the total value
            if is_selected:
                after_position = self.indexer.determine_cursor_position(selected_text, total_value)
                if after_position[0] >= 0 and after_position[1] >= 0:
                    before_position = self.indexer.determine_cursor_position(selected_text, total_value, 0)
                    return (total_value, after_position, before_position)
                else:
                    # Free selection if it is allowed to be visible
                    if visibility_level > 0:
                        actions.key("right left")
                    else:
                        return undefined_positions
        
        # Add and quickly remove a zero width space to find our current position
        if total_value != "":
            zwsp_position = self.zero_width_space_insertion_index()
            if zwsp_position[0] >= -1 and zwsp_position[1] >= -1:
                return (total_value, zwsp_position, zwsp_position)

        if visibility_level > 0:
            # Go to the start of the document and copy that text
            actions.key("ctrl-shift-home")
            actions.sleep("200ms")
            with clip.revert():
                with clip.capture() as s:
                    actions.edit.copy()
                try:
                    before_text = s.text()
                except clip.NoChange:
                    before_text = ""
                if before_text != "":
                    actions.sleep("200ms")
                    actions.key("right")

            # If we have a total value and our value starts with the current selection
            # We can be certain that we have the right cursor position
            if total_value != "" and before_text != "" and total_value.startswith(before_text):
                top_scan_position = self.indexer.determine_cursor_position(before_text, total_value)
                if top_scan_position[0] >= -1 and top_scan_position[1] >= -1:
                    return (total_value, top_scan_position, top_scan_position)

            # Otherwise we need to select until the end of the document
            else:
                actions.key("ctrl-shift-end")
                actions.sleep("200ms")
                with clip.revert():
                    with clip.capture() as s:
                        actions.edit.copy()
                    try:
                        after_text = s.text()
                    except clip.NoChange:
                        after_text = ""

                if after_text != "":
                    actions.sleep("200ms")
                    actions.key("left")
                
                total_value = before_text + after_text
                bottom_scan_position = self.indexer.determine_cursor_position(before_text, total_value)
                return (total_value, bottom_scan_position, bottom_scan_position)                
        return undefined_positions

    def index_content(self, total_value: str = "", first_cursor_position: (int, int) = (-1, -1), second_cursor_position: (int, int) = (-1, -1)):
        context = self.get_current_context()

        # First, determine text history
        if first_cursor_position[0] >= -1 and first_cursor_position[1] >= -1:
            lines = total_value.splitlines()
            before_lines = []
            after_lines = []
            add_line_before_after = False
            for line_index, line in enumerate(lines):
                if line_index < first_cursor_position[0]:
                    before_lines.append( line )
                elif line_index > first_cursor_position[0]:
                    after_lines.append( line )
                else:
                    if first_cursor_position[1] == 0:
                        add_line_before_after = True
                    
                    index_in_line = len(line) - first_cursor_position[1]
                    before_char = line[:index_in_line]
                    after_char = line[index_in_line:]
                    before_lines.append(before_char)
                    if after_char != "":
                        after_lines.append(after_char)

            before_text = "\n".join(before_lines)
            after_text = "\n".join(after_lines)
            if add_line_before_after and len(after_lines) > 0:
                after_text = "\n" + after_text

            context.input_history_manager.cursor_position_tracker.set_history(before_text, after_text)

            # Set the selection correctly as well
            if second_cursor_position[0] > -1 and second_cursor_position[1] > -1 and (first_cursor_position != second_cursor_position):
                context.input_history_manager.cursor_position_tracker.selection_cursor_marker = second_cursor_position

            # If no cursor is known - Simply set the text history - We will deal with inconsistent behavior later
        else:
            context.input_history_manager.cursor_position_tracker.set_history(total_value)
        
        events = self.indexer.index_text(context.input_history_manager.cursor_position_tracker.text_history)
        context.input_history_manager.set_input_history(events)