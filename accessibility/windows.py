
from .accessibility_api import AccessibilityCaret, AccessibilityText, AccessibilityApi
from typing import List

class WindowsAccessibilityApi(AccessibilityApi):

    # Retrieve the text available from the currently focused element
    def index_element_text(self, element = None) -> AccessibilityText:
        if element is None:
            element = self.get_focused_element()
            if element is None:
                return None
        
        accessibility_text = None
        value = None
        if "LegacyIAccessible" in element.patterns:
            try:
                value = element.legacyiaccessible_pattern.value
            # Windows sometimes just throws operation successful errors...
            except OSError:
                value = value
            accessibility_text = AccessibilityText(value)

        elif "Text2" in element.patterns:
            try:
                value = element.text_pattern2.document_range.text
            # Windows sometimes just throws operation successful errors...
            except OSError:
                value = value
            accessibility_text = AccessibilityText(value)
            
        elif "Value" in element.patterns:
            try:
                value = element.value_pattern.value
            # Windows sometimes just throws operation successful errors...
            except OSError:
                value = value
            accessibility_text = AccessibilityText(value)

        if accessibility_text:
            caret_position = self.determine_caret_positions(element)
            if caret_position is not None and len(caret_position) == 2:
                accessibility_text.active_caret = caret_position[0]
                accessibility_text.selection_caret = caret_position[1]

        return accessibility_text


    # Retrieve the caret positions within the currently focused element
    def determine_caret_positions(self, element = None) -> List[AccessibilityCaret]:
        if element is None:
            element = self.get_focused_element()
            if element is None:
                return None
        
        # Code adapted from AndreasArvidsson's talon files
        # Currently only Text2 is supported
        if "Text2" in element.patterns:
            text_pattern = element.text_pattern2

            # Make copy of the document range to avoid modifying the original
            range_before_selection = text_pattern.document_range.clone()
            selection_ranges = text_pattern.selection
            if len(selection_ranges) != 1:
                print("ACCESSIBILITY INDEXATION ERROR - Found multiple selections")
                return []
            selection_range = selection_ranges[0].clone()
                    
            # Move the end of the copy to the start of the selection
            # range_before_selection.end = selection_range.start
            range_before_selection.move_endpoint_by_range("End", "Start", target=selection_range)
            try:
                range_before_selection_text = range_before_selection.text
            # Windows sometimes just throws operation successful errors...
            except OSError:
                pass

            try:
                selection_range_text = selection_range.text
            # Windows sometimes just throws operation successful errors...
            except OSError:
                pass

            try:
                document_range_text = text_pattern.document_range.text
            # Windows sometimes just throws operation successful errors...
            except OSError:
                pass

            # Find the index by using the before selection text and the indexed text
            start = len(range_before_selection_text)
            start_position = self.indexer.determine_caret_position(range_before_selection_text, document_range_text, start)
            end = len(range_before_selection_text + selection_range_text)
            end_position = self.indexer.determine_caret_position(range_before_selection_text + selection_range_text, document_range_text, end)

            if (start_position[0] > -1 and start_position[1] > -1) or (end_position[0] > -1 and end_position[1] > -1):

                # The selection is reversed if the caret is at the start of the selection
                try:
                    is_reversed = text_pattern.caret_range.compare_endpoints("Start", "Start", target=selection_ranges[0]) == 0
                # Windows sometimes just throws operation successful errors...
                except OSError:
                    pass

                start_caret = AccessibilityCaret(start, start_position[0], start_position[1])
                end_caret = AccessibilityCaret(end, end_position[0], end_position[1])

                return [end_caret, start_caret] if is_reversed else [start_caret, end_caret]
            else:
                return []

windows_api = WindowsAccessibilityApi()
