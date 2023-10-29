from talon import Module, Context, actions, clip
from typing import List, Union
from .list_manager import ListManager
from .managed_websites import ManagedWebsites
from .managed_directories import ManagedDirectories
from .managed_homophones import ManagedHomophones
from .managed_abbreviations import ManagedAbbreviations
from .managed_additional_words import ManagedVocabulary
from .managed_words_to_replace import ManagedWordsToReplace
from ..user_settings import SETTINGS_DIR

mod = Module()
hud_ctx = Context()
hud_ctx.matches = """
tag: user.talon_hud_available
"""

browser_ctx = Context()
browser_ctx.matches = """
tag: browser
"""

manager = ListManager(
    [
        ManagedWebsites("user.website", SETTINGS_DIR / "websites.csv"),
        ManagedDirectories("user.system_paths", SETTINGS_DIR / "system_paths.csv"),
    ],
    [
        ManagedHomophones(),
        ManagedWordsToReplace(SETTINGS_DIR / "words_to_replace.csv"),
        ManagedAbbreviations("user.abbreviation", SETTINGS_DIR / "abbreviations.csv"),
        ManagedVocabulary("user.vocabulary", SETTINGS_DIR / "additional_words.csv"),
    ]
)

@mod.action_class
class Actions:

    def remember_text(words: List[str], append: Union[bool, int] = False, list_name: str = None) -> str:
        """Detect text and save it as something known to use later"""
        global manager
        value_to_remember = actions.user.remember_detect_text()
        if value_to_remember:
            value_to_remember = value_to_remember if manager.update(value_to_remember, " ".join(words), append > 0 or append == True, list_name) else ""

        return value_to_remember
    
    def forget_text(words: List[str], list_name: str = None) -> str:
        """Detect text and remove it from the user managed lists"""
        global manager
        value_to_forget = actions.user.remember_detect_text()
        if value_to_forget:
            value_to_forget = value_to_forget if manager.remove(value_to_forget, " ".join(words), list_name) else ""
        
        return value_to_forget
    
    def remember_detect_text() -> str:
        """Detect text from a selection for use in user managed lists"""
        selection = ""
        old_clipboard = clip.text()
        with clip.revert():
            actions.edit.copy()
            actions.sleep("150ms")
            selection = clip.text()

            if old_clipboard == selection:
                selection = ""

        if selection:
            return selection.splitlines()[0]
        else:
            return ""

@hud_ctx.action_class("user")
class HudActions:

    def remember_text(words: List[str], append: Union[bool, int] = False, list_name: str = None) -> str:
        """Detect text and save it as something known to use later"""
        remembered = actions.next(words, append, list_name)
        if remembered:
            actions.user.hud_add_log("success", "'" + remembered + "' remembered as '" + " ".join(words) + "'")
        else:
            actions.user.hud_add_log("warning", "Could not detect anything to remember as '" + " ".join(words) + "'")
        return remembered
    
    def forget_text(words: List[str]) -> str:
        """Detect text and remove it from the user managed lists"""
        value_to_forget = actions.next(words)
        if value_to_forget:
            actions.user.hud_add_log("success", "'" + " ".join(words) + "' forgotten")
        else:
            actions.user.hud_add_log("warning", "Could not find anything to forget")
        return value_to_forget

@browser_ctx.action_class("user")
class BrowserActions:

    def remember_detect_text() -> str:
        """Detect text from a selection or the browser location for use in user managed lists"""
        remembered_text = actions.next()
        if not remembered_text:
            actions.browser.focus_address()
            browser_location = ""
            with clip.revert():
                actions.sleep("150ms")
                actions.edit.copy()
                actions.sleep("150ms")                
                browser_location = clip.text()
                if browser_location:
                    remembered_text = browser_location.splitlines()[0]
                actions.sleep("150ms")
            actions.browser.focus_page()
            
        return remembered_text