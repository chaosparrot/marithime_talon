
from talon import actions, Context
from typing import List, Union
import os

def index_document(_ = None, _2 = None):
    actions.user.marithime_index_textarea()

ctx_override = Context()
ctx_override.matches = """
tag: user.talon_hud_available
"""

IMAGES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")
@ctx_override.action_class("user")
class HudActions:

    def marithime_move_caret(phrase: str, caret_position: int = -1):
        """Move the caret to the given phrase"""
        try:
            actions.next(phrase, caret_position)
        except RuntimeError as e:
            actions.user.hud_add_log("warning", phrase + " could not be found in context")
            raise e

    def marithime_select(phrase: Union[str, List[str]]):
        """Move the caret to the given phrase and select it"""
        try:
            actions.next(phrase)
        except RuntimeError as e:
            actions.user.hud_add_log("warning", phrase + " could not be found in context")
            raise e
        
    def marithime_correction(selection_and_correction: List[str]):
        """Select a fuzzy match of the words and apply the given words"""
        try:
            actions.next(selection_and_correction)
        except RuntimeError as e:
            actions.user.hud_add_log("warning", "'" + " ".join(selection_and_correction) + "' could not be corrected")
            raise e

    def marithime_update_sensory_state(scanning: bool, level: str, caret_confidence: int, content_confidence: int):
        """Visually or audibly update the state for the user"""
        
        # Build up the status bar image icon name
        status_bar_image = "virtual_buffer"
        if level == "accessibility" and not scanning:
            status_bar_image += "_a11y"
        
        if caret_confidence <= 0 and content_confidence <= 0:
            status_bar_image += "_empty"
        else:
            status_bar_image += "_all_content" if content_confidence > 1 else "_some_content"
            if caret_confidence <= 0:
                status_bar_image += "_no_caret"
            elif caret_confidence == 1:
                status_bar_image += "_coarse_caret"
            else:
                status_bar_image += "_known_caret"

        if scanning:
            status_bar_image += "_scan"

        absolute_status_bar_image = os.path.join(IMAGES_DIR, status_bar_image + ".png")
        status_bar_icon = actions.user.hud_create_status_icon("virtual_buffer", absolute_status_bar_image, "", "Virtual buffer unavailable", index_document)
        actions.user.hud_publish_status_icon("virtual_buffer", status_bar_icon)