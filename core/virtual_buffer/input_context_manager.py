from talon import ui, actions, clip
from .input_context import InputContext
import time
from typing import List, Callable, Tuple
from ..formatters.text_formatter import TextFormatter
from ..formatters.formatters import FORMATTERS_LIST
from .indexer import VirtualBufferIndexer, text_to_virtual_buffer_tokens
from .caret_tracker import _CARET_MARKER, _COARSE_MARKER
from ..utils.levenshtein import levenshtein
import os
import platform

# Class keeping track of all the different contexts availa ble
class InputContextManager:

    visual_state = None

    indexer: VirtualBufferIndexer = None
    current_context: InputContext = None
    contexts: List[InputContext] = None
    last_clear_check = time.perf_counter()
    use_last_set_formatter = False
    active_formatters: List[TextFormatter]
    formatter_names: List[str]
    state_callback: Callable[[str, int, int, bool], None] = None

    last_title: str = ""
    last_pid: int = -1
    system = ""

    def __init__(self, state_callback: Callable[[str, int, int, bool], None] = None):
        self.visual_state = {
            'scanning': True, # Whether we are scanning or not
            'level': '', # Disabled - Typed - Accessibility
            'caret_confidence': 0, # 0 Is no known caret - 1 is line confidence - 2 is document confidence
            'content_confidence': 0, # 0 is empty - 1 is some - 2 is full document
        }

        self.state_callback = state_callback
        self.update_visual_state(scanning=False)

        self.indexer = VirtualBufferIndexer(FORMATTERS_LIST.values())
        self.system = platform.system()
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
                    text_buffer = context.buffer.caret_tracker.text_buffer.replace(_CARET_MARKER, '').replace(_COARSE_MARKER, '')

                    normalized_accessible_content = "".join(accessible_content.lower().split())
                    normalized_context = "".join(text_buffer.lower().split())
                    comparison = levenshtein(normalized_accessible_content, normalized_context)

                    if (len(normalized_context) - comparison) > len(normalized_context) * 0.9:
                        context.update_pattern(name, title, pid)
                        context_to_switch_to = context
                        break

            self.current_context = context_to_switch_to

            # Update the visual state
            if context_to_switch_to is not None:
                caret_index = context_to_switch_to.buffer.caret_tracker.get_caret_index()
                caret_confidence = 0 if caret_index[0] == -1 else 1 if caret_index[1] == -1 else 2
                content_confidence = 0 if len(context_to_switch_to.buffer.tokens) == 0 else 1

                # Check if we can upgrade the context to be fully confident
                if caret_confidence > 0 and context_to_switch_to.accessible_api_available:
                    accessible_text = self.index_accessible_value()
                    text_buffer = context_to_switch_to.buffer.caret_tracker.text_buffer.replace(_CARET_MARKER, '').replace(_COARSE_MARKER, '')

                    if text_buffer == accessible_text:
                        content_confidence = 2

                self.update_visual_state("accessibility" if context_to_switch_to.accessible_api_available else "text", caret_confidence=caret_confidence, content_confidence=content_confidence)
            else:
                self.update_visual_state("text", 0, 0, False)

            return self.current_context is not None
        return False

    def ensure_viable_context(self):
        update_caret = self.visual_state['caret_confidence'] != 2
        update_content = self.visual_state['caret_confidence'] == 1 and self.visual_state['content_confidence'] < 1
        self.poll_accessible_changes(update_caret=update_caret, update_content=update_content)

    def poll_accessible_changes(self, update_caret = False, update_content = False):
        caret_updated = False
        context = self.get_current_context()
        value = self.index_accessible_value()

        if update_content and self.visual_state['content_confidence'] != 2:
            if context:
                text_buffer = context.buffer.caret_tracker.text_buffer.replace(_CARET_MARKER, '').replace(_COARSE_MARKER, '')
                
                if value != text_buffer:
                    self.index_textarea(value, False)
                    caret_updated = True

        if update_caret and caret_updated == False and self.visual_state['caret_confidence'] != 2:
            results = self.find_caret_position(value, -1)

            # Only if the caret position is not the same as the known position do we need to reindex
            if results[1] != context.buffer.caret_tracker.get_caret_index():
                self.index_content(results[0], results[1], results[2])
    
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
        
        # TODO IMPROVE FORMATTER SELECTION!!!
        return self.indexer.default_formatter

    def apply_key(self, key: str):
        current_context = self.get_current_context()
        current_context.apply_key(key)

        # Only poll the changes for specific key combinations that have known changes to the content
        if len(current_context.buffer.tokens) > 0:
            if self.system == "Darwin" and ("cmd" in key or "super" in key):
                if "cmd-z" in key or "cmd-v" in key or "cmd-x" in key \
                    or "cmd-backspace" in key or "cmd-delete" in key \
                    or "super-z" in key or "super-v" in key or "super-x" in key \
                    or "super-backspace" in key or "super-delete" in key:
                    self.poll_accessible_changes(True, True)

            elif "ctrl" in key:
                if "ctrl-z" in key or "ctrl-v" in key or "ctrl-x" in key \
                    or "ctrl-backspace" in key or "ctrl-delete" in key:
                    self.poll_accessible_changes(True, True)

    def track_insert(self, insert: str, phrase: str = None):
        vbm = self.get_current_context().buffer
        tokens = []
        formatters = vbm.get_current_formatters()
        if self.use_last_set_formatter or len(formatters) == 0:
            formatters = self.formatter_names

        # Automatic insert splitting if no explicit phrase is given
        if phrase == "" and " " in insert:
            inserts = insert.split(" ")
            for index, text in enumerate(inserts):
                if index < len(inserts) - 1:
                    text += " "
                
                tokens.extend(text_to_virtual_buffer_tokens(text, None, "|".join(formatters)))
        else:
            tokens = text_to_virtual_buffer_tokens(insert, phrase, "|".join(formatters))
        vbm.insert_tokens(tokens)

        if self.current_context:
            caret_index = vbm.caret_tracker.get_caret_index()
            caret_confidence = 0 if caret_index[0] == -1 else 1 if caret_index[1] == -1 else 2
            self.update_visual_state(caret_confidence=caret_confidence)

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
        if window and window.app and window.enabled and not window.app.background and not window.hidden and window.rect:
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
        except:
            element = None
        
        # Windows based A11Y
        if self.system == "Windows":
            #print( "ELEMENT PATTERNS!", element.patterns)
            #if "LegacyIAccessible" in element.patterns:
            #    print( "LEGACY!", dir( element.legacyiaccessible_pattern ) )
            #    print( "ROLE", element.legacyiaccessible_pattern.value )
                #print( element.legacy_pattern )    
            #try:
            #    print( "SELECTION", dir(element.text_pattern.selection), element.text_pattern.selection.index(), element.text_pattern.selection.count() )
            #except:
            #    print( "ERROR! " )

            if "Text2" in element.patterns:
                value = element.text_pattern2.document_range.text
                #print( "YEET", element.text_pattern2.caret_range.text, dir(element.text_pattern2.caret_range) )
                # , element.text_pattern2.caret_range.compare_endpoints("", "")
                if self.current_context:
                    self.current_context.set_accessible_api_available("text", True)
            elif "Value" in element.patterns:
                value = element.value_pattern.value
                if self.current_context:
                    self.current_context.set_accessible_api_available("text", True)
            #raise NotImplementedError("ARGH")
        # Mac based A11Y - Currently untested
        # Examples taken from phillco/ax_kit and tweaked afterwards
        elif self.system == "Darwin":
            # Has accessibility support
            if element and element.attrs:
                value = element.get("AXValue")
        # Linux based A11Y - Currently unimplemented
        else:
            pass

        # Update the visual state to accessible if a value was found        
        if value:
            self.update_visual_state(level = "accessibility")

        if value is None:
            value = ""
    
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
        self.update_visual_state(scanning=True)
        total_value = self.index_accessible_value() if total_value == "" else total_value
        results = self.find_caret_position(total_value, 1 if forced == True else 0)
        self.index_content(results[0], results[1], results[2])
        
    def get_accessible_cursor_indecis(self, total_value: str) -> ((int, int), (int, int)):
        left_cursor_index = (-1, -1) 
        right_cursor_index = (-1, -1)

        try:
            element = ui.focused_element()
        except:
            element = None

        if element and self.system == "Darwin":
            # Has accessibility support
            if element.attrs:
                ranges = element.get("AXSelectedTextRanges")

                # Multiple carets / cursors - Undefined locations
                if ranges is not None and len(ranges) > 1:
                    return (left_cursor_index, right_cursor_index)
                else:
                    selected_text_range = element.get("AXSelectedTextRange")
                    if selected_text_range is not None:
                        left_index = selected_text_range.left
                        right_index = selected_text_range.right
                        
                        # No selection - only need to check one and duplicate it
                        left_cursor_index = self.indexer.determine_caret_position("", total_value, left_index)
                        if left_index == right_index:
                           right_cursor_index = left_cursor_index
                        # Selection, need to find both cursors
                        else:
                           right_cursor_index = self.indexer.determine_caret_position("", total_value, right_index)
        elif element and self.system == "Windows" and "Text2" in element.patterns:
            windows_cursor_indices = self.get_windows_cursor_indices(element)
            if len(windows_cursor_indices) > 0:
                left_cursor_index = windows_cursor_indices[0]
                right_cursor_index = windows_cursor_indices[1]

        return (left_cursor_index, right_cursor_index)
    
    # Code adapted from AndreasArvidsson's talon files
    def get_windows_cursor_indices(self, element) -> List[Tuple[int, int]]:
        text_pattern = element.text_pattern2

        # Make copy of the document range to avoid modifying the original
        range_before_selection = text_pattern.document_range.clone()
        selection_ranges = text_pattern.selection
        if len(selection_ranges) != 1:
            print("INDEXATION ERROR - Found multiple ranges")
            return []
        selection_range = selection_ranges[0].clone()
                
        # Move the end of the copy to the start of the selection
        # range_before_selection.end = selection_range.start
        range_before_selection.move_endpoint_by_range("End", "Start", target=selection_range)

        # Find the index by using the before selection text and the indexed text
        start_position = self.indexer.determine_caret_position(range_before_selection.text, text_pattern.document_range.text)
        end_position = self.indexer.determine_caret_position(range_before_selection.text + selection_range.text, text_pattern.document_range.text)

        if (start_position[0] > -1 and start_position[1] > -1) or (end_position[0] > -1 and end_position[1] > -1):
            # If our start position is empty - We are at the start of the document
            if (start_position[0] == -1 and end_position[0] != -1):
                lines = text_pattern.document_range.text.split("\n")
                start_position = (0, 0 if len(lines) == 0 else len(lines[0]))

            # The selection is reversed if the caret is at the start of the selection
            #is_reversed = text_pattern.caret_range.compare_endpoints("Start", "Start", target=selection_ranges[0]) == 0
            # TODO REVERSE LOGIC IN INDEXATION
            return [start_position, end_position]#[end_position, start_position] if is_reversed else [start_position, end_position]
        else:
            return []

    def zero_width_space_insertion_index(self) -> (int, int):
        zwsp = "​"
        actions.insert(zwsp)
        actions.sleep("50ms")
        total_value = self.index_accessible_value()
        actions.key("backspace")
        return self.indexer.determine_caret_position(zwsp, total_value)
    
    def find_caret_position(self, total_value: str, visibility_level = 0) -> (str, (int, int), (int, int)):
        print("UPDATE CARET POSITION!!!")
        self.update_visual_state(scanning=True)        
        undefined_positions = (total_value, (-1, -1), (-1, -1))
        before_text = ""
        after_text = ""
        
        # Check for accessible cursor indexes ( selection or not )
        accessible_cursor_index = self.get_accessible_cursor_indecis(total_value)
        print("ACC", accessible_cursor_index)
        if accessible_cursor_index[0] != (-1, -1) and accessible_cursor_index[1] != (-1, -1):
            return [total_value, accessible_cursor_index[0], accessible_cursor_index[1]]

        # Find selection first if it exists
        current_clipboard = ""
        selected_text = ""
        with clip.revert():
            current_clipboard = clip.text()
            actions.sleep("200ms")
            
            with clip.capture() as current_selection:
                actions.edit.copy()
            actions.sleep("200ms")
            print("UPDATE CARET SELECTION TEST!!!")

            try:
                selected_text = current_selection.text()
                is_selected = current_selection.text() == current_clipboard
            except clip.NoChange:
                is_selected = True
            
            # If there is a selection, try out if our selection can be found in the total value
            if is_selected:
                after_position = self.indexer.determine_caret_position(selected_text, total_value)
                if after_position[0] >= 0 and after_position[1] >= 0:
                    before_position = self.indexer.determine_caret_position(selected_text, total_value, 0)
                    return (total_value, after_position, before_position)
                else:
                    # Free selection if it is allowed to be visible
                    if visibility_level > 0:
                        actions.key("right left")
                    else:
                        return undefined_positions
        
        # Add and quickly remove a zero width space to find our current position
        if total_value != "":
            print("ZERO WIDTH PIXEL!!!")
            zwsp_position = self.zero_width_space_insertion_index()
            if zwsp_position[0] >= -1 and zwsp_position[1] >= -1:
                return (total_value, zwsp_position, zwsp_position)

        if visibility_level > 0:
            # Go to the start of the document and copy that text
            actions.key("ctrl-shift-home" if self.system != "Darwin" else "cmd-shift-up")
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
            # We can be certain that we have the right caret position
            if total_value != "" and before_text != "" and total_value.startswith(before_text):
                top_scan_position = self.indexer.determine_caret_position(before_text, total_value)
                if top_scan_position[0] >= -1 and top_scan_position[1] >= -1:
                    return (total_value, top_scan_position, top_scan_position)

            # Otherwise we need to select until the end of the document
            else:
                actions.key("ctrl-shift-end" if self.system != "Darwin" else "cmd-shift-down")
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
                bottom_scan_position = self.indexer.determine_caret_position(before_text, total_value)
                return (total_value, bottom_scan_position, bottom_scan_position)                
        return undefined_positions

    def index_content(self, total_value: str = "", first_caret_position: (int, int) = (-1, -1), second_caret_position: (int, int) = (-1, -1)):
        context = self.get_current_context()
        caret_confidence = 0
        content_confidence = 2 if total_value != "" else 0

        # First, determine text buffer
        if first_caret_position[0] >= -1 and first_caret_position[1] >= -1:
            lines = total_value.splitlines()
            before_lines = []
            after_lines = []
            add_line_before_after = False
            for line_index, line in enumerate(lines):
                if line_index < first_caret_position[0]:
                    before_lines.append( line )
                elif line_index > first_caret_position[0]:
                    after_lines.append( line )
                else:
                    if first_caret_position[1] == 0:
                        add_line_before_after = True
                    
                    index_in_line = len(line) - first_caret_position[1]
                    before_char = line[:index_in_line]
                    after_char = line[index_in_line:]
                    before_lines.append(before_char)
                    if after_char != "":
                        after_lines.append(after_char)

            before_text = "\n".join(before_lines)
            after_text = "\n".join(after_lines)
            if add_line_before_after and len(after_lines) > 0:
                after_text = "\n" + after_text

            context.buffer.caret_tracker.set_buffer(before_text, after_text)
            caret_confidence = 2

            # Set the selection correctly as well
            if second_caret_position[0] > -1 and second_caret_position[1] > -1 and (first_caret_position != second_caret_position):
                context.buffer.caret_tracker.selection_caret_marker = second_caret_position

            # If no caret is known - Simply set the text buffer - We will deal with inconsistent behavior later
        else:
            context.buffer.caret_tracker.set_buffer(total_value)

        tokens = self.indexer.index_text(context.buffer.caret_tracker.text_buffer)
        context.buffer.set_tokens(tokens)
        self.update_visual_state(caret_confidence=caret_confidence, content_confidence=content_confidence, scanning=False)

    def update_visual_state(self, level: str = None, caret_confidence: int = -1, content_confidence: int = -1, scanning: bool = None):
        is_updated = False
        if scanning is not None:
            if scanning != self.visual_state['scanning']:
                is_updated = True
                self.visual_state['scanning'] = scanning

        if level is not None:
            if level != self.visual_state['level']:
                is_updated = True
                self.visual_state['level'] = level

        if caret_confidence > -1:
            if caret_confidence != self.visual_state['caret_confidence']:
                is_updated = True
                self.visual_state['caret_confidence'] = caret_confidence

        if content_confidence > -1:
            if content_confidence != self.visual_state['content_confidence']:
                is_updated = True
                self.visual_state['content_confidence'] = content_confidence

        # TODO implement non-hud visualisation
        try:
            if is_updated and self.state_callback:        
                self.state_callback(self.visual_state['scanning'], self.visual_state['level'], self.visual_state['caret_confidence'], self.visual_state['content_confidence'])
        except NotImplementedError:
            pass