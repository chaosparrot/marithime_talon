
from .accessibility_api import AccessibilityCaret, AccessibilityText, AccessibilityApi
from typing import List

class WindowsAccessibilityApi(AccessibilityApi):

    # Retrieve the text available from the currently focused element
    def index_element_text(self, element = None) -> AccessibilityText:
        if element is None:
            element = self.get_focused_element()
            if element is None:
                return None

        # Takes the precedence order of Text2, Text, LegacyIAccessble, Value
        # NOTE - TextEdit is not a read value but a way to change the text
        accessibility_text = None
        value = None
        if "Text2" in element.patterns:
            try:
                value = element.text_pattern2.document_range.text
            # Windows sometimes just throws operation successful errors...
            except OSError as e:
                # NotImplemented error
                if str(e) == "0x80004001":
                    value = None
            # Talon pre 0.4 beta
            except NameError as e:
                value = None
            
            if value is not None:
                accessibility_text = AccessibilityText(value)
        
        if not accessibility_text and "Text" in element.patterns:
            try:
                value = element.text_pattern.document_range.text
            # Windows sometimes just throws operation successful errors...
            except OSError as e:
                # NotImplemented error
                if str(e) == "0x80004001":
                    value = None
            # Talon pre 0.4 beta
            except NameError as e:
                value = None

            if value is not None:
                accessibility_text = AccessibilityText(value)
        
        if not accessibility_text and "LegacyIAccessible" in element.patterns:
            # IAccessible Enum values
            # https://learn.microsoft.com/en-us/dotnet/api/system.windows.forms.accessiblerole?view=windowsdesktop-8.0
            try:
                if element.legacyiaccessible_pattern.role == 42:
                    value = element.legacyiaccessible_pattern.value
            # Windows sometimes just throws operation successful errors...
            except OSError as e:
                # NotImplemented error
                if str(e) == "0x80004001":
                    value = None
            # Talon pre 0.4 beta
            except NameError as e:
                value = None
            # Talon pre 0.4 beta - no selection supported
            except AttributeError as e:
                return []

            if value is not None:
                accessibility_text = AccessibilityText(value)

        # Finally fallback to the Value pattern
        if (not accessibility_text or accessibility_text.text == "") and "Value" in element.patterns:
            try:
                value = element.value_pattern.value
            # Windows sometimes just throws operation successful errors...
            except OSError:
                # NotImplemented error
                if str(e) == "0x80004001":
                    value = None
            # Talon pre 0.4 beta
            except NameError as e:
                value = None

            if value is not None:
                accessibility_text = AccessibilityText(value)

        if accessibility_text and accessibility_text.text != "":
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
        # Text(1) doesn't seem to have caret_range and other methods 
        has_text_pattern = "Text2" in element.patterns# or "Text" in element.patterns
        if has_text_pattern:
            text_pattern = element.text_pattern2# if "Text2" in element.patterns else element.text_pattern

            # Make copy of the document range to avoid modifying the original
            range_before_selection = text_pattern.document_range.clone()
            try:
                selection_ranges = text_pattern.selection
            except OSError as e:
                # NotImplemented error - Cannot check selection so early return
                if str(e) == "0x80004001":
                    return []

            if len(selection_ranges) > 1:
                print("ACCESSIBILITY INDEXATION ERROR - Found multiple or no selections")
                return []
            selection_range = selection_ranges[0].clone()
                    
            # Move the end of the copy to the start of the selection
            # range_before_selection.end = selection_range.start
            try:
                range_before_selection.move_endpoint_by_range("End", "Start", target=selection_range)
            # Talon pre 0.4 beta - no selection supported
            except AttributeError as e:
                return []

            range_before_selection_text = None
            try:
                range_before_selection_text = range_before_selection.text
            # Windows sometimes just throws operation successful errors...
            except OSError as e:
                # NotImplemented error
                if str(e) == "0x80004001":
                    return []
                pass

            selection_range_text = None
            try:
                selection_range_text = selection_range.text
            # Windows sometimes just throws operation successful errors...
            except OSError as e:
                # NotImplemented error
                if str(e) == "0x80004001":
                    return []                
                pass

            document_range_text = None
            try:
                document_range_text = text_pattern.document_range.text
            # Windows sometimes just throws operation successful errors...
            except OSError as e:
                # NotImplemented error
                if str(e) == "0x80004001":
                    return []                
                pass

            # Find the index by using the before selection text and the indexed text
            start = len(range_before_selection_text)
            start_position = self.indexer.determine_caret_position(range_before_selection_text, document_range_text, start)
            end = len(range_before_selection_text + selection_range_text)
            end_position = self.indexer.determine_caret_position(range_before_selection_text + selection_range_text, document_range_text, end)

            is_reversed = False
            print("DETERMININIG START AND END POSITION", start_position, end_position )
            if (start_position[0] > -1 and start_position[1] > -1) or (end_position[0] > -1 and end_position[1] > -1):

                # The selection is reversed if the caret is at the start of the selection
                try:
                    is_reversed = text_pattern.caret_range.compare_endpoints("Start", "Start", target=selection_ranges[0]) == 0
                # Windows sometimes just throws operation successful errors...
                except OSError as e:
                    # NotImplemented error
                    if str(e) == "0x80004001":
                        return []
                    pass

                start_caret = AccessibilityCaret(start, start_position[0], start_position[1])
                end_caret = AccessibilityCaret(end, end_position[0], end_position[1])

                return [end_caret, start_caret] if not is_reversed else [start_caret, end_caret]
            else:
                return []
        # IAccessible proves to be harder to implement
        # Further investigation can be done with the code seen in NVAccess
        # https://github.com/nvaccess/nvda/blob/e80d7822160f7d2ff151140bc97ca84e5798c1fb/source/NVDAObjects/IAccessible/__init__.py#L465
        #elif "LegacyIAccessible" in element.patterns:
        #    print("ATTEMPTING!")
        #    pattern = element.legacyiaccessible_pattern
        #    selection = pattern.selection
        #    if len(selection) > 0:
        #        print( dir( selection ), selection )
        #    print( dir(element), element.aria_role )

        return []

windows_api = WindowsAccessibilityApi()
