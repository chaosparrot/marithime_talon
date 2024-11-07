
from accessibility_api import AccessibilityCaret, AccessibilityText, AccessibilityApi
from typing import List

class LinuxAccessibilityApi(AccessibilityApi):

    # Retrieve the text available from the currently focused element
    def index_element_text(self, element = None) -> AccessibilityText:
        return None

    # Retrieve the caret positions within the currently focused element
    def determine_caret_positions(self, element = None) -> List[AccessibilityCaret]:
        return None