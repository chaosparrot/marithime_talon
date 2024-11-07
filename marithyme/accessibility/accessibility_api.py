
from dataclasses import dataclass
from talon import ui
from typing import List
from ..virtual_buffer.indexer import VirtualBufferIndexer

@dataclass
class AccessibilityCaret:
    index_within_text: int = -1
    line_index: int = -1
    characters_from_end: int = -1

@dataclass
class AccessibilityText:
    text: str = ""
    active_caret: AccessibilityCaret = None
    selection_caret: AccessibilityCaret = None

class AccessibilityApi:
    indexer: VirtualBufferIndexer

    def __init__(self):
        self.indexer = VirtualBufferIndexer([])

    def get_focused_element(self):
        try:
            return ui.get_focused_element()
        except:
            return None

    # Retrieve the text available from the currently focused element
    def index_element_text(self, element = None) -> AccessibilityText:
        return None

    # Retrieve the caret positions within the currently focused element
    def determine_caret_positions(self, element = None) -> List[AccessibilityCaret]:
        return None