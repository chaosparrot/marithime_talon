
from accessibility_api import AccessibilityCaret, AccessibilityText, AccessibilityApi
from typing import List

class MacOsAccessibilityApi(AccessibilityApi):

    # Retrieve the text available from the currently focused element
    def index_element_text(self, element = None) -> AccessibilityText:
        if element is None:
            element = self.get_focused_element()
            if element is None:
                return None

        accessibility_text = None            
        if element and element.attrs:
            value = element.get("AXValue")
            if value is not None:
                accessibility_text = AccessibilityText(value)

        if accessibility_text:
            caret_position = self.determine_caret_positions(element)
            if len(caret_position) == 2:
                accessibility_text.active_caret = caret_position[0]
                accessibility_text.selection_caret = caret_position[1]

        return accessibility_text

    # Retrieve the caret positions within the currently focused element
    def determine_caret_positions(self, element = None) -> List[AccessibilityCaret]:
        if element is None or not element.attrs:
            element = self.get_focused_element()
            if element is None or not element.attrs:
                return None
            
        ranges = element.get("AXSelectedTextRanges")

        # Multiple carets / cursors - Undefined locations
        if ranges is not None and len(ranges) > 1:
            print("ACCESSIBILITY INDEXATION ERROR - Found multiple selections")
            return []
        elif ranges is not None:
            selected_text_range = element.get("AXSelectedTextRange")

            if selected_text_range is not None:
                left_index = selected_text_range.left
                right_index = selected_text_range.right
                value = element.get("AXValue")

                # TODO FIX END POSITION IF DOCUMENT IS EMPTY OR VALUE HAPPENS MULTIPLE TIMES                
                
                # No selection - only need to check one and duplicate it
                left_cursor_index = self.indexer.determine_caret_position("", value, left_index)
                if left_index == right_index:
                    right_cursor_index = left_cursor_index
                # Selection, need to find both cursors
                else:
                    right_cursor_index = self.indexer.determine_caret_position("", value, right_index)

                # TODO - Can we check for reversed carets?
                start_caret = AccessibilityCaret(left_index, left_cursor_index[0], left_cursor_index[1])
                end_caret = AccessibilityCaret(right_index, right_cursor_index[0], right_cursor_index[1])
                is_reversed = False

                return [end_caret, start_caret] if is_reversed else [start_caret, end_caret]            
            else:
                return []
