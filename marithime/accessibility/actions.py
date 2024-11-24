from .accessibility_api import AccessibilityText, AccessibilityCaret, AccessibilityApi
import platform
from .linux import linux_api
from .macos import macos_api
from .windows import windows_api
from talon import Module
from typing import List
mod = Module()

def get_accessibility_api() -> AccessibilityApi:
    # TODO - Does this check the system within VMs?
    system = platform.system()
    if system == "Windows":
        return windows_api.index_element_text()
    elif system == "Darwin":
        return macos_api.index_element_text()
    else:
        return linux_api.index_element_text()

@mod.action_class
class Actions:

    def marithime_get_element_text() -> AccessibilityText:
        """Retrieve the accessible text from the currently focused element"""
        return get_accessibility_api().index_element_text()

    def marithime_get_element_caret() -> List[AccessibilityCaret]:
        """Retrieve the caret from the currently focused element"""
        return get_accessibility_api().determine_caret_positions()