import platform
from talon import Module
from typing import List
from .accessibility_api import AccessibilityText, AccessibilityCaret, AccessibilityApi
from .linux import linux_api
from .macos import macos_api
from .windows import windows_api
mod = Module()

def get_accessibility_api() -> AccessibilityApi:
    # TODO - Does this check the system within VMs?
    system = platform.system()
    if system == "Windows":
        return windows_api
    elif system == "Darwin":
        return macos_api
    else:
        return linux_api

@mod.action_class
class Actions:

    def marithime_get_element_text() -> AccessibilityText:
        """Retrieve the accessible text from the currently focused element"""
        return get_accessibility_api().index_element_text()

    def marithime_get_element_caret() -> List[AccessibilityCaret]:
        """Retrieve the caret from the currently focused element"""
        return get_accessibility_api().determine_caret_positions()