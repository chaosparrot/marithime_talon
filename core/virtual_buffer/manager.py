from talon import Module, Context, actions, settings, ui, speech_system, app
from .input_context_manager import InputContextManager
from .input_fixer import InputFixer
from .typing import CORRECTION_THRESHOLD, SELECTION_THRESHOLD
from ..phonetics.detection import EXACT_MATCH
from typing import List, Union
import json
import re

mod = Module()

mod.setting("context_remove_undo", type=str, default="ctrl-z", desc="The key combination to undo a paste action")
mod.setting("context_remove_word", type=str, default="ctrl-backspace", desc="The key combination to clear a word to the left of the caret")
mod.setting("context_remove_letter", type=str, default="backspace", desc="The key combination to clear a single letter to the left of the caret")
mod.setting("context_remove_forward_word", type=str, default="ctrl-delete", desc="The key combination to clear a word to the right of the caret")
mod.setting("context_remove_forward_letter", type=str, default="delete", desc="The key combination to clear a single letter to the right of the caret")

mod.tag("flow_numbers", desc="Ensure that the user can freely insert numbers")
mod.tag("flow_letters", desc="Ensure that the user can freely insert letters")
mod.tag("flow_symbols", desc="Ensure that the user can freely insert symbols")
mod.tag("flow_words", desc="Ensure that the user can freely insert words")

mod.tag("context_disable_shift_selection", desc="Disables shift selection for the current context")
mod.tag("context_disable_word_wrap", desc="Disables word wrap detection for the current context")

mod.list("indexed_words", desc="A list of words that correspond to inserted text and their caret positions for quick navigation in text")
ctx = Context()
ctx.lists["user.indexed_words"] = []

@mod.capture(rule="({user.indexed_words} | <user.word>)")
def fuzzy_indexed_word(m) -> str:
    "Returns a single word that is possibly indexed inside of the virtual buffer"
    try:
        return m.indexed_words
    except AttributeError:
        return m.word

# Class to manage all the talon bindings and key presses for the virtual buffer
class VirtualBufferManager:
    manager: InputContextManager
    fixer: InputFixer
    tracking = True
    tracking_lock: str = ""
    use_last_set_formatter = False

    def __init__(self):
        self.context = InputContextManager(actions.user.virtual_buffer_update_sensory_state)
        self.fixer = InputFixer()
        self.fixer.verbose = True

    def clear_context(self):
        for context in self.context.contexts:
            context.clear_context()
        self.context.contexts = []
        self.context.current_context = None

    def set_formatter(self, name: str):
        self.context.set_formatter(name)

    def enable_tracking(self, lock: str = ""):
        if self.tracking_lock == "" or self.tracking_lock == lock:
            self.tracking = True
            self.tracking_lock = ""

    def disable_tracking(self, lock: str = ""):
        if self.tracking_lock == "" and lock != "":
            self.tracking_lock = lock
        self.tracking = False

    def track_key(self, key_string: str):
        if self.tracking:
            self.context.apply_key(key_string)
            self.index()

    def track_insert(self, insert: str, phrase: str = None):
        if self.tracking:
            self.context.track_insert(insert, phrase)
            self.index()

    def is_selecting(self) -> bool:
        return self.context.get_current_context().buffer.is_selecting()

    def has_phrase(self, phrase: str) -> bool:
        return self.context.get_current_context().buffer.has_matching_phrase(phrase)
    
    def move_caret_back(self, keep_selection: bool = False) -> List[str]:
        self.disable_tracking()
        self.context.ensure_viable_context()
        self.enable_tracking()
        
        vbm = self.context.get_current_context().buffer

        if len(vbm.tokens) > 0:
            last_token = vbm.tokens[-1]
            self.context.should_use_last_formatter(True)
            if keep_selection:
                return vbm.select_until_end("", True)
            else:
                return vbm.navigate_to_token(last_token, -1, keep_selection)
        else:
            return ["end"]

    def select_phrases(self, phrases: List[str], until_end = False, for_correction=False) -> List[str]:
        self.disable_tracking()
        self.context.ensure_viable_context()
        self.enable_tracking()

        vb = self.context.get_current_context().buffer
        self.context.should_use_last_formatter(False)

        if until_end:
            return vb.select_until_end(phrases)
        else:
            match_threshold = CORRECTION_THRESHOLD if not for_correction else SELECTION_THRESHOLD
            return vb.select_phrases(phrases, match_threshold=match_threshold, for_correction=for_correction)

    def move_to_phrase(self, phrase: str, character_index: int = -1, keep_selection: bool = False, next_occurrence: bool = True) -> List[str]:
        self.disable_tracking()
        self.context.ensure_viable_context()
        self.enable_tracking()

        if self.has_phrase(phrase):
            self.context.should_use_last_formatter(False)
        vbm = self.context.get_current_context().buffer
        return vbm.go_phrase(phrase, "end" if character_index == -1 else "start", keep_selection, next_occurrence )

    def transform_insert(self, insert: str, enable_self_repair: bool = False) -> (str, List[str]):
        # Make sure we have the right caret position for insertion
        self.disable_tracking()
        self.context.ensure_viable_context()
        self.enable_tracking()
        vbm = self.context.get_current_context().buffer

        repair_keys = []

        # Allow the user to do self repair in speech
        correction_insertion = self.is_selecting()
        previous_selection = "" if not correction_insertion else vbm.caret_tracker.get_selection_text()
        current_insertion = ""
        if enable_self_repair:
            
            # Remove stutters / repeats in the same phrase
            words = insert.split()
            words_to_insert = []
            preceding_word = ""
            for word in words:
                if word != preceding_word:
                    words_to_insert.append(word)
                preceding_word = word
            insert = " ".join(words_to_insert)

            self_repair_match = vbm.find_self_repair(insert.split())
            if self_repair_match is not None:

                # If we are dealing with a continuation, change the insert to remove the first few words
                if self_repair_match.score_potential == EXACT_MATCH:
                    words = insert.split()
                    if len(words) > len(self_repair_match.scores):
                        insert = " ".join(words[len(self_repair_match.scores):])
                    # Complete repetition - Do not insert anything
                    else:
                        return ("", [])
                # Do a complete replacement from the first high matching score
                # We do not support replacing initial words, only inserting, as replacing initial words requires more context about meaning
                # ( We have no -> We have a , but not, We have no -> They have no )
                else:
                    first_index = self_repair_match.buffer_indices[0][0]
                    allow_initial_replacement = False
                    if first_index - 1 >= 0:
                        allow_initial_replacement = any(punc in vbm.tokens[first_index - 1].text for punc in (".", "?", "!"))
                    else:
                        allow_initial_replacement = True
                    replacement_index = 0 if allow_initial_replacement else 1

                    # Make sure that we only replace words from the first matching word instead of allowing a full replacement
                    if not allow_initial_replacement:
                        for index, score in enumerate(self_repair_match.scores):
                            if score == EXACT_MATCH:
                                replacement_index = index
                                insert = " ".join(insert.split()[index:])
                                break
                    
                    if replacement_index >= 0:
                        start_index = self_repair_match.buffer_indices[replacement_index][0]
                        end_index = self_repair_match.buffer_indices[-1][-1]

                        tokens = vbm.tokens
                        if start_index < len(tokens) and end_index < len(tokens):
                            repair_keys.extend( vbm.select_token_range(tokens[start_index], tokens[end_index]) )
                            previous_selection = vbm.caret_tracker.get_selection_text()
                            current_insertion = " ".join(insert.split()[:end_index - start_index])

                            repair_keys.append("backspace")
                            self.context.apply_key("backspace")
                            correction_insertion = True

        # Determine formatter
        previous_text = ""
        next_text = ""
        token_index = vbm.determine_leftmost_token_index()
        if token_index[0] > -1:
            previous_text = vbm.get_previous_text()
            next_text = vbm.get_next_text()

            context_formatters = vbm.get_current_formatters()
            context_formatter = context_formatters[0] if len(context_formatters) > 0 else None
            formatter = self.context.get_formatter(context_formatter)
        else:
            formatter = self.context.get_formatter()

        # Do automatic fixing for non-correction text
        words = insert.split()

        before_auto_correction = " ".join(words)
        if not correction_insertion:
            words = self.fixer.automatic_fix_list(words, previous_text, next_text)

        # Format text 
        if formatter is not None:
            words = formatter.words_to_format(insert.split(), previous_text, next_text)
            formatter_repair_keys = formatter.determine_correction_keys(words, previous_text, next_text)

            for formatter_repair_key in formatter_repair_keys:
                self.context.apply_key(formatter_repair_key)

            repair_keys.extend(formatter_repair_keys)
        
        # If there was a fix, keep track of it here
        if previous_selection:
            if not current_insertion:
                current_insertion = " ".join(words)
        
                # Do not track automatic fixes - Still need to find a proper way to do this if we want to keep a fix in between the automatic fixes
                if current_insertion == before_auto_correction:
                    self.fixer.track_fix_list(previous_selection.split(), words, previous_text, next_text)
        
                # Track self repair corrections
            else:
                self.fixer.track_fix_list(previous_selection.split(), words, previous_text, next_text)

        return ("".join(words), repair_keys)

    def clear_keys(self, backwards = True) -> List[str]:
        vbm = self.context.get_current_context().buffer
        context = vbm.determine_context()

        if self.is_selecting():
            return [settings.get("user.context_remove_letter")]
        
        if context.current is not None:
            if context.character_index == 0 and backwards and context.previous is not None:
                return [settings.get("user.context_remove_letter") + ":" + str(len(context.previous.text))]

            elif context.character_index == len(context.current.text):
                if not backwards and context.next is not None:
                    return [settings.get("user.context_remove_forward_letter") + ":" + str(len(context.next.text))]
                elif backwards:
                    return [settings.get("user.context_remove_letter") + ":" + str(len(context.current.text))]

            if context.character_index > 0 and context.character_index < len(context.current.text) - 1:
                if backwards:
                    return [settings.get("user.context_remove_letter") + ":" + str(context.character_index)]
                else:
                    return [settings.get("user.context_remove_forward_letter") + ":" + str(len(context.current.text) - context.character_index)]

        return [settings.get("user.context_remove_word") if backwards else settings.get("user.context_remove_forward_word")]

    def index(self):
        vbm = self.context.get_current_context().buffer

        words_list = []
        for token in vbm.tokens:
            words_list.append(token.phrase)
        ctx.lists["user.indexed_words"] = words_list

        tags = []
        token_index = vbm.determine_token_index()
        if token_index[0] > -1 and token_index[1] > -1:
            token = vbm.tokens[token_index[0]]
            # TODO APPLY FLOW TAGS DEPENDING ON WORDS
            # TODO APPLY FORMATTERS DEPENDING ON POSITION ? 
        ctx.tags = tags

    def index_textarea(self):
        self.disable_tracking()
        self.context.index_textarea()
        self.index()
        self.enable_tracking()

    def focus_changed(self, event):
        context_switched = self.context.switch_context(event)
        if context_switched:
            self.index()

    def window_closed(self, event):
        self.context.close_context(event)

def update_language(language: str):
    if not language:
        language = settings.get("speech.language", "en")
        if language is None:
            language = "en"
    language = language.split("_")[0]
    engine_description = settings.get("speech.engine")
    try:
        if speech_system.engine.engine:
            engine_description = re.sub(r"[^\w\d]", '', str(speech_system.engine.engine)).lower().strip()
    except:
        pass
    mutator.fixer.load_fixes(language, engine_description)

mutator = None
def init_mutator():
    global mutator
    mutator = VirtualBufferManager()
    ui.register("win_focus", mutator.focus_changed)
    ui.register("win_close", mutator.window_closed)
    settings.register("speech.language", lambda language: update_language(language))
    settings.register("speech.engine", lambda _: update_language(""))
    update_language("")

app.register("ready", init_mutator)

@mod.action_class
class Actions:

    def virtual_buffer_enable_tracking():
        """Enable tracking of input values so that we can make contextual decisions and keep the caret position"""
        global mutator
        mutator.enable_tracking()

    def virtual_buffer_disable_tracking():
        """Disable tracking of input values"""
        global mutator
        mutator.disable_tracking()

    def virtual_buffer_set_formatter(formatter: str):
        """Sets the current formatter to be used in text editing"""
        global mutator
        mutator.set_formatter(formatter)

    def virtual_buffer_transform_insert(insert: str) -> str:
        """Transform an insert automatically depending on previous context"""
        global mutator
        return mutator.transform_insert(insert)[0]

    def virtual_buffer_self_repair_insert(prose: str):
        """Input words based on context surrounding the words to input, allowing for self repair within speech as well"""
        global mutator

        text_to_insert, keys = mutator.transform_insert(prose, True)
        if len(keys) > 0:
            mutator.disable_tracking()
            for key in keys:
                actions.key(key)
            mutator.enable_tracking()

        actions.insert(text_to_insert)

    def virtual_buffer_insert(prose: str):
        """Input words based on context surrounding the words to input"""
        global mutator

        text_to_insert, keys = mutator.transform_insert(prose)
        if len(keys) > 0:
            mutator.disable_tracking()
            for key in keys:
                actions.key(key)
            mutator.enable_tracking()

        actions.insert(text_to_insert)

    def virtual_buffer_track_key(key_string: str) -> str:
        """Track one or more key presses according to the key string"""
        global mutator
        mutator.track_key(key_string)

    def virtual_buffer_track_insert(insert: str, phrase: str = "") -> str:
        """Track a full insert"""
        global mutator
        mutator.track_insert(insert, phrase)

    def virtual_buffer_clear(backward: bool = True):
        """Apply a clear based on the current virtual buffer"""
        global mutator
        keys = mutator.clear_keys(backward)
        for key in keys:
            actions.key(key)
        mutator.index_textarea()

    def virtual_buffer_move_caret(phrase: str, caret_position: int = -1):
        """Move the caret to the given phrase"""
        global mutator
        if mutator.has_phrase(phrase):
            keys = mutator.move_to_phrase(phrase, caret_position)
            if keys:
                mutator.disable_tracking()
                for key in keys:
                    actions.key(key)
                mutator.enable_tracking()
        else:
            raise RuntimeError("Input phrase '" + phrase + "' could not be found in the buffer")

    def virtual_buffer_select(phrase: Union[str, List[str]]):
        """Move the caret to the given phrase and select it"""
        global mutator

        phrases = phrase if isinstance(phrase, List) else [phrase]
        keys = mutator.select_phrases(phrases)
        mutator.disable_tracking()
        if keys:
            for key in keys:
                actions.key(key)
        mutator.enable_tracking()
            
    def virtual_buffer_correction(selection_and_correction: List[str]):
        """Select a fuzzy match of the words and apply the given words"""
        global mutator
        keys = mutator.select_phrases(selection_and_correction, for_correction=True)
        if len(keys) > 0:
            mutator.disable_tracking()
            if keys:
                for key in keys:
                    actions.key(key)
            mutator.enable_tracking()
            text = " ".join(selection_and_correction)
            actions.user.virtual_buffer_insert(text)
        else:
            raise RuntimeError("Input phrase '" + " ".join(selection_and_correction) + "' could not be corrected")

    def virtual_buffer_clear_phrase(phrase: str):
        """Move the caret behind the given phrase and remove it"""
        global mutator
        before_keys = mutator.move_to_phrase(phrase, -1, False, False)
        mutator.disable_tracking()
        if before_keys:
            for key in before_keys:
                actions.key(key)
        mutator.enable_tracking()

        keys = mutator.clear_keys()
        for key in keys:
            actions.key(key)

    def virtual_buffer_continue():
        """Move the caret to the end of the current virtual buffer"""
        global mutator
        keys = mutator.move_caret_back()

        mutator.disable_tracking()
        for key in keys:
            actions.key(key)
        mutator.enable_tracking()

    def virtual_buffer_forget():
        """Forget the current context of the virtual buffer completely"""
        global mutator
        mutator.clear_context()

    def virtual_buffer_best_match(phrases: List[str], correct_previous: bool = False, starting_phrase: str = '') -> str:
        """Improve accuracy by picking the best matches out of the words used"""
        global mutator
        match_dictionary = {}
        if starting_phrase:
            phrases.append( starting_phrase )

        for phrase in phrases:
            if phrase not in match_dictionary:
                match_dictionary[phrase] = 0
            match_dictionary[phrase] += 1
        
        return max(match_dictionary, key=match_dictionary.get)
    
    def virtual_buffer_index_textarea():
        """Select the index area and update the internal state completely"""
        global mutator
        mutator.index_textarea()
    
    def virtual_buffer_update_sensory_state(scanning: bool, level: str, caret_confidence: int, content_confidence: int):
        """Visually or audibly update the state for the user"""
        pass

    def virtual_buffer_dump():
        """Dump the current state of the virtual buffer for debugging purposes"""
        global mutator
        mutator.disable_tracking("DUMP")
        actions.insert("Available contexts:" )
        for context in mutator.context.contexts:
            actions.insert( "    " + context.app_name + " - " + context.title + " - PID - " + str(context.pid))

        actions.key("enter")
        actions.insert("Using " + mutator.context.get_current_context().title + " - PID " + str(mutator.context.get_current_context().pid ))
        actions.key("enter")
        actions.insert(mutator.context.get_current_context().buffer.caret_tracker.text_buffer)
        actions.key("enter:2")
        tokens = []
        for token in mutator.context.get_current_context().buffer.tokens:
            tokens.append({
                "index_from_line_end": token.index_from_line_end,
                "line_index": token.line_index,
                "phrase": token.phrase,
                "text": token.text
            })
        actions.insert(json.dumps(tokens))
        actions.key("enter")
        actions.key("enter")

        actions.insert(json.dumps(list(mutator.fixer.done_fixes.keys())))
        actions.key("enter")

        mutator.enable_tracking("DUMP")

ctx_override = Context()
ctx_override.matches = """
tag: user.talon_hud_available
"""

def index_document(self, icon):
    actions.user.virtual_buffer_index_textarea()

@ctx_override.action_class("user")
class HudActions:

    def virtual_buffer_move_caret(phrase: str, caret_position: int = -1):
        """Move the caret to the given phrase"""
        try:
            actions.next(phrase, caret_position)
        except RuntimeError as e:
            actions.user.hud_add_log("warning", phrase + " could not be found in context")
            raise e

    def virtual_buffer_select(phrase: Union[str, List[str]]):
        """Move the caret to the given phrase and select it"""
        try:
            actions.next(phrase)
        except RuntimeError as e:
            actions.user.hud_add_log("warning", phrase + " could not be found in context")
            raise e
        
    def virtual_buffer_correction(selection_and_correction: List[str]):
        """Select a fuzzy match of the words and apply the given words"""
        try:
            actions.next(selection_and_correction)
        except RuntimeError as e:
            actions.user.hud_add_log("warning", "'" + " ".join(selection_and_correction) + "' could not be corrected")
            raise e

    def virtual_buffer_update_sensory_state(scanning: bool, level: str, caret_confidence: int, content_confidence: int):
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

        status_bar_icon = actions.user.hud_create_status_icon("virtual_buffer", status_bar_image, "", "Virtual buffer unavailable", index_document)
        actions.user.hud_publish_status_icon("virtual_buffer", status_bar_icon)