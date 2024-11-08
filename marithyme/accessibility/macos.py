
from accessibility_api import AccessibilityCaret, AccessibilityText, AccessibilityApi
from typing import List
import time

class MacOsAccessibilityApi(AccessibilityApi):

    def get_focused_element(self):
        element = super().get_focused_element()

        # On MacOS when switching windows, sometimes the window being switched to or the scrollbar
        # Is focused, even though the AXFocused state is False
        # We delay checking the focused element again so we don't mess up our context state
        if element and element.attrs and element.get("AXFocused") == False:
            print("Found unfocused element - Delaying focused element polling by 100ms")
            time.sleep(0.1)
            element = super().get_focused_element()
        return element

    # Retrieve the text available from the currently focused element
    def index_element_text(self, element = None) -> AccessibilityText:
        if element is None:
            element = self.get_focused_element()
            if element is None:
                return None

        accessibility_text = None            
        if element and element.attrs and element.get("AXRole") in ["AXTextField", "AXTextArea", "AXComboBox"]:
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
                if element.get("AXRole") == "AXStaticText":
                    value = ""

                # TODO FIX END POSITION IF DOCUMENT IS EMPTY OR VALUE HAPPENS MULTIPLE TIMES                
                
                # No selection - only need to check one and duplicate it
                left_cursor_index = self.indexer.determine_caret_position("", value, left_index)
                if left_index == right_index:
                    right_cursor_index = left_cursor_index
                # Selection, need to find both cursors
                else:
                    right_cursor_index = self.indexer.determine_caret_position("", value, right_index)

                start_caret = AccessibilityCaret(left_index, left_cursor_index[0], left_cursor_index[1])
                end_caret = AccessibilityCaret(right_index, right_cursor_index[0], right_cursor_index[1])

                # MacOS doesn't really have the concept of a caret position when text is selected
                # So just keep the orientation so that the end caret is active
                return [end_caret, start_caret]
            else:

                # Sometimes programs do not have an AXSelectedTextRange set up
                # When it has an empty value
                # In that case, set the cursor to be at the start of the document
                value = element.get("AXValue")
                if not value:
                    start_caret = AccessibilityCaret(0, 0, 0)
                    end_caret = AccessibilityCaret(0, 0, 0)
                    return []

                return []

macos_api = MacOsAccessibilityApi()

# Accessibility notes on programs
# In MacOS Excel, the FormulaBar puts all the text inside of the AXDescription instead of in the AXValue
# When you are editing within the cell, it is fine, but certain keystrokes obviously won't work well

# In iTerm2, the value cannot be accessed in any way, event the AXInsertionPointLineNumber seems off somehow, VoiceOver does seem to be able to retrieve the text though...
# Since terminals are all iffy when it comes to accessibility / keyboard shortcuts / mouse movements anyway
# I'm fine to just only support backspacing within a single line either way

# Microsoft Outlook seems to work just fine, but when adding email addresses, it adds a special OBJECT REPLACEMENT CHARACTER for every email that has been added.
# That object replacement character then refers to the StaticText child within it
# Probably fine to, for now, make sure that Object replacement characters become their own token

# Object replacement character 65532

# For a search field within PROGRAM_X - There is an AXNumberOfCharacters of 0 for AXTextField as a role
# This AXTextField only gets an AXSelectedTextRange if the value isn't empty

# For Chrome searching, this doesn't seem to be the same. Though the AXTextField role does seem to signify that only single line entries are allowed
# Which needs to be taken into account when doing AX listening

# In Slack, the search bar, when empty, has the role AXStaticText with a set value even though it is focused
# This means that we should check for this role as well to not index that value if it is available
# Searching is done within an AXComboBox that only seems to get the right value when the caret is not at the end
# If we are to make a consistent focus state, it seems like we need to do it on a per application basis,
# Because the AXFocused value seems to be set on list items within the combo box within Slack and presumably within other applications as well

# It seems that, on MacOS, when selecting text, it doesn't really matter where the caret is set. This makes sense since when pressing delete, backspace, left or right arrow key, the result is the same regardless of the current cursor position
# We don't need to reverse the arrow keys in this manner in this case.

# Chrome fields
# Number fields seem to be AXIncrementor, which might be useful for flow number state
# Email fields are AXTextField with the AXRoleDescription of email
# Search fields have AXTextField with the AXRoleDescription of search text field and a AXSubRole of AxSearchField
# Phone fields have an AXTextField with the AXRoleDescription of telephone
# URL fields have an AXTextField with the AXRoleDescription of url

# VSCode has a very interesting message to enable screen reader mode, namely in the AXDescription:
# The editor is not accessible at this time. To enable screen reader optimized mode, use Shift+Option+F1
# We might be able to detect and auto-enable it by looking at the AXRoleDescription of 'editor'

# To detect the terminal within VSCode, we can check for the AXTextField element having an AXDescription containing 'Terminal'
# Because the AXTextArea's are used for the editor and other multiline fields