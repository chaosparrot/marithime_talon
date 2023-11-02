from talon import Module, Context, actions, settings, ui, speech_system
from .input_context_manager import InputContextManager
from .input_fixer import InputFixer
from typing import List, Union
import json
import re

mod = Module()

mod.setting("context_remove_undo", type=str, default="ctrl-z", desc="The key combination to undo a paste action")
mod.setting("context_remove_word", type=str, default="ctrl-backspace", desc="The key combination to clear a word to the left of the cursor")
mod.setting("context_remove_letter", type=str, default="backspace", desc="The key combination to clear a single letter to the left of the cursor")
mod.setting("context_remove_forward_word", type=str, default="ctrl-delete", desc="The key combination to clear a word to the right of the cursor")
mod.setting("context_remove_forward_letter", type=str, default="delete", desc="The key combination to clear a single letter to the right of the cursor")

mod.tag("flow_numbers", desc="Ensure that the user can freely insert numbers")
mod.tag("flow_letters", desc="Ensure that the user can freely insert letters")
mod.tag("flow_symbols", desc="Ensure that the user can freely insert symbols")
mod.tag("flow_words", desc="Ensure that the user can freely insert words")

mod.tag("context_disable_shift_selection", desc="Disables shift selection for the current context")
mod.tag("context_disable_word_wrap", desc="Disables word wrap detection for the current context")

mod.list("indexed_words", desc="A list of words that correspond to inserted text and their cursor positions for quick navigation in text")
ctx = Context()
ctx.lists["user.indexed_words"] = []

@mod.capture(rule="({user.indexed_words} | <user.word>)")
def fuzzy_indexed_word(m) -> str:
    "Returns a single word that is possibly indexed inside of the input history"
    try:
        return m.indexed_words
    except AttributeError:
        return m.word

# Class to manage all the talon bindings and key presses for input history
class InputMutator:
    manager: InputContextManager    
    fixer: InputFixer
    tracking = True
    tracking_lock: str = ""
    use_last_set_formatter = False

    def __init__(self):
        self.manager = InputContextManager()
        self.fixer = InputFixer()

    def clear_context(self):
        for context in self.manager.contexts:
            context.clear_context()
        self.manager.contexts = []
        self.manager.current_context = None

    def set_formatter(self, name: str):
        self.manager.set_formatter(name)

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
            self.manager.apply_key(key_string)
            self.index()

    def track_insert(self, insert: str, phrase: str = None):
        if self.tracking:
            self.manager.track_insert(insert, phrase)
            self.index()

    def is_selecting(self) -> bool:
        return self.manager.get_current_context().input_history_manager.is_selecting()

    def has_phrase(self, phrase: str) -> bool:
        return self.manager.get_current_context().input_history_manager.has_matching_phrase(phrase)
    
    def move_cursor_back(self, keep_selection: bool = False) -> List[str]:
        ihm = self.manager.get_current_context().input_history_manager

        if len(ihm.input_history) > 0:
            last_event = ihm.input_history[-1]
            self.manager.should_use_last_formatter(True)
            if keep_selection:
                return ihm.select_until_end("", True)
            else:
                return ihm.navigate_to_event(last_event, -1, keep_selection)
        else:
            return ["end"]
        
    def select_phrase(self, phrase: str, until_end = False) -> List[str]:
        ihm = self.manager.get_current_context().input_history_manager

        if self.has_phrase(phrase):
            self.manager.should_use_last_formatter(False)

        if until_end:
            return ihm.select_until_end(phrase)
        else:
            return ihm.select_phrase(phrase)
        
    def select_phrases(self, phrases: List[str], until_end = False) -> List[str]:
        ihm = self.manager.get_current_context().input_history_manager
        self.manager.should_use_last_formatter(False)

        if until_end:
            return ihm.select_until_end(phrases)
        else:
            return ihm.select_phrases(phrases)

    def move_to_phrase(self, phrase: str, character_index: int = -1, keep_selection: bool = False, next_occurrence: bool = True) -> List[str]:
        if self.has_phrase(phrase):
            self.manager.should_use_last_formatter(False)
        ihm = self.manager.get_current_context().input_history_manager
        return ihm.go_phrase(phrase, "end" if character_index == -1 else "start", keep_selection, next_occurrence )

    def transform_insert(self, insert: str, enable_self_repair: bool = False) -> (str, List[str]):
        ihm = self.manager.get_current_context().input_history_manager

        repair_keys = []

        # Allow the user to do self repair in speech
        correction_insertion = self.is_selecting()
        previous_selection = "" if not correction_insertion else ihm.cursor_position_tracker.get_selection_text()
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

            self_repair_match = ihm.find_self_repair(insert.split())
            if self_repair_match is not None:
                actions.user.hud_add_log("success", "SELF REPAIR FOUND! " + insert )

                # If we are dealing with a continuation, change the insert to remove the first few words
                if self_repair_match.score / len(self_repair_match.scores) == 3:
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
                    first_index = self_repair_match.indices[0]
                    allow_initial_replacement = False
                    if first_index - 1 >= 0:
                        allow_initial_replacement = any(punc in ihm.input_history[first_index - 1].text for punc in (".", "?", "!"))
                    else:
                        allow_initial_replacement = True
                    replacement_index = 0 if allow_initial_replacement else -1

                    # Make sure that we only replace words from the first matching word instead of allowing a full replacement
                    if not allow_initial_replacement:
                        for index, score in enumerate(self_repair_match.scores):
                            if score >= 1:
                                replacement_index = index
                                insert = " ".join(insert.split()[index:])
                                break
                    
                    if replacement_index >= 0:
                        start_index = self_repair_match.indices[replacement_index]
                        end_index = self_repair_match.indices[-1]

                        input_history = ihm.input_history
                        if start_index < len(input_history) and end_index < len(input_history):
                            repair_keys.extend( ihm.select_event_range(input_history[start_index], input_history[end_index]) )
                            previous_selection = ihm.cursor_position_tracker.get_selection_text()
                            current_insertion = " ".join(insert.split()[:end_index - start_index])

                            repair_keys.append("backspace")
                            self.manager.apply_key("backspace")
                            correction_insertion = True

        # Determine formatter
        previous_text = ""
        next_text = ""
        input_index = ihm.determine_leftmost_input_index()
        if input_index[0] > -1:
            previous_text = ihm.get_previous_text()
            next_text = ihm.get_next_text()

            context_formatters = ihm.get_current_formatters()
            context_formatter = context_formatters[0] if len(context_formatters) > 0 else None
            formatter = self.manager.get_formatter(context_formatter)
        else:
            formatter = self.manager.get_formatter()

        # Do automatic fixing for non-correction text
        words = insert.split()
        before_auto_correction = " ".join(words)
        if not correction_insertion:
            words = self.fixer.automatic_fix_list(words, previous_text, next_text)

        # Format text 
        if formatter is not None:
            actions.user.hud_add_log("warning", ihm.cursor_position_tracker.text_history )
            formatter_repair_keys = formatter.determine_correction_keys(insert.split(), previous_text, next_text)
            for formatter_repair_key in formatter_repair_keys:
                self.manager.apply_key(formatter_repair_key)

            repair_keys.extend(formatter_repair_keys)
            words = formatter.words_to_format(insert.split(), previous_text, next_text)
        
        # If there was a fix, keep track of it here
        #if previous_selection:
        #    if not current_insertion:
        #        current_insertion = "".join(words)
        #
        #        # Do not track automatic fixes - Still need to find a proper way to do this if we want to keep one of them
        #        if current_insertion == before_auto_correction:
        #            self.fixer.track_fix(previous_selection, current_insertion, previous_text, next_text)
        #
        #        # Track self repair corrections
        #    else:
        #        self.fixer.track_fix(previous_selection, current_insertion, previous_text, next_text)

        return ("".join(words), repair_keys)

    def clear_keys(self, backwards = True) -> List[str]:
        ihm = self.manager.get_current_context().input_history_manager
        context = ihm.determine_context()

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
        ihm = self.manager.get_current_context().input_history_manager

        words_list = []
        for event in ihm.input_history:
            words_list.append(event.phrase)
        ctx.lists["user.indexed_words"] = words_list

        tags = []
        input_index = ihm.determine_input_index()
        if input_index[0] > -1 and input_index[1] > -1:
            event = ihm.input_history[input_index[0]]
            # TODO APPLY FLOW TAGS DEPENDING ON WORDS
        ctx.tags = tags

    def focus_changed(self, event):
        context_switched = self.manager.switch_context(event)
        if context_switched:
            self.index()

    def window_closed(self, event):
        self.manager.close_context(event)


mutator = InputMutator()
ui.register("win_focus", mutator.focus_changed)
ui.register("win_close", mutator.window_closed)
def update_language(language: str):
    if language == "":
        language = settings.get("speech.language", "en")
    language = language.split("_")[0]
    engine_description = settings.get("speech.engine")
    try:
        if speech_system.engine.engine:
            engine_description = re.sub(r"[^\w\d]", '', str(speech_system.engine.engine)).lower().strip()
    except:
        pass
    mutator.fixer.load_fixes(language, engine_description)

settings.register("speech.language", lambda language: update_language(language))
settings.register("speech.engine", lambda _: update_language(""))
update_language("")

@mod.action_class
class Actions:

    def input_core_enable_tracking():
        """Enable tracking of input values so that we can make contextual decisions and keep the cursor position"""
        global mutator
        mutator.enable_tracking()

    def input_core_disable_tracking():
        """Disable tracking of input values"""
        global mutator
        mutator.disable_tracking()

    def input_core_set_formatter(formatter: str):
        """Sets the current formatter to be used in text editing"""
        global mutator
        mutator.set_formatter(formatter)

    def input_core_transform_insert(insert: str) -> str:
        """Transform an insert automatically depending on previous context"""
        global mutator
        return mutator.transform_insert(insert)[0]

    def input_core_self_repair_insert(prose: str):
        """Input words based on context surrounding the words to input, allowing for self repair within speech as well"""
        global mutator

        text_to_insert, keys = mutator.transform_insert(prose, True)
        if len(keys) > 0:
            mutator.disable_tracking()
            for key in keys:
                actions.key(key)
            mutator.enable_tracking()

        actions.insert(text_to_insert)

    def input_core_insert(prose: str):
        """Input words based on context surrounding the words to input"""
        global mutator

        text_to_insert, keys = mutator.transform_insert(prose)
        if len(keys) > 0:
            mutator.disable_tracking()
            for key in keys:
                actions.key(key)
            mutator.enable_tracking()

        actions.insert(text_to_insert)

    def input_core_track_key(key_string: str) -> str:
        """Track one or more key presses according to the key string"""
        global mutator
        mutator.track_key(key_string)

    def input_core_track_insert(insert: str, phrase: str = "") -> str:
        """Track a full insert"""
        global mutator
        mutator.track_insert(insert, phrase)

    def input_core_clear(backward: bool = True):
        """Apply a clear based on the current input history"""
        global mutator
        keys = mutator.clear_keys(backward)
        for key in keys:
            actions.key(key)

    def input_core_move_cursor(phrase: str, cursor_position: int = -1):
        """Move the cursor to the given phrase"""
        global mutator
        if mutator.has_phrase(phrase):
            keys = mutator.move_to_phrase(phrase, cursor_position)
            if keys:
                mutator.disable_tracking()
                for key in keys:
                    actions.key(key)
                mutator.enable_tracking()
        else:
            actions.user.hud_add_log("command", phrase + " could not be found in context")
            raise RuntimeError("Input phrase '" + phrase + "' could not be found in the history")

    def input_core_select(phrase: Union[str, List[str]]):
        """Move the cursor to the given phrase and select it"""
        global mutator

        if isinstance(phrase, List):
            keys = mutator.select_phrases(phrase)
            mutator.disable_tracking()
            if keys:
                for key in keys:
                    actions.key(key)
            mutator.enable_tracking()
        else:
            if mutator.has_phrase(phrase):
                keys = mutator.select_phrase(phrase)
                mutator.disable_tracking()
                if keys:
                    for key in keys:
                        actions.key(key)
                mutator.enable_tracking()
            else:
                actions.user.hud_add_log("warning", phrase + " could not be found in context")
                raise RuntimeError("Input phrase '" + phrase + "' could not be found in the history")
            
    def input_core_correction(selection_and_correction: List[str]):
        """Select a fuzzy match of the words and apply the given words"""
        global mutator
        keys = mutator.select_phrases(selection_and_correction)
        if len(keys) > 0:
            mutator.disable_tracking()
            if keys:
                for key in keys:
                    actions.key(key)
            mutator.enable_tracking()
            text = " ".join(selection_and_correction)
            actions.user.input_core_insert(text)
        else:
            actions.user.hud_add_log("warning", "'" + " ".join(selection_and_correction) + "' could not be corrected")
            raise RuntimeError("Input phrase '" + " ".join(selection_and_correction) + "' could not be corrected")

    def input_core_clear_phrase(phrase: str):
        """Move the cursor behind the given phrase and remove it"""
        global mutator
        before_keys = mutator.move_to_phrase(phrase, -1, False, False)
        mutator.disable_tracking()
        if before_keys:
            for key in before_keys:
                actions.key(key)
        mutator.enable_tracking()

        keys = mutator.clear_keys()
        actions.user.hud_add_log("warning", "CLEAR! " + " ".join(keys))
        for key in keys:
            actions.key(key)

    def input_core_continue():
        """Move the cursor to the end of the current input history"""
        global mutator
        keys = mutator.move_cursor_back()

        mutator.disable_tracking()
        for key in keys:
            actions.key(key)
        mutator.enable_tracking()

    def input_core_forget():
        """Forget the current context of the input history completely"""
        global mutator
        mutator.clear_context()

    def input_core_best_match(phrases: List[str], correct_previous: bool = False, starting_phrase: str = '') -> str:
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
    
    def input_core_dump():
        """Dump the current state of the input history for debugging purposes"""
        global mutator
        mutator.disable_tracking("DUMP")
        actions.insert("Available contexts:" )
        for context in mutator.manager.contexts:
            actions.insert( "    " + context.key_matching + " - PID - " + str(context.pid))

        actions.key("enter")
        actions.insert("Using " + mutator.manager.get_current_context().key_matching + " - PID " + str(mutator.manager.get_current_context().pid ))
        actions.key("enter")        
        actions.insert(mutator.manager.get_current_context().input_history_manager.cursor_position_tracker.text_history)
        actions.key("enter:2")
        events = []
        for event in mutator.manager.get_current_context().input_history_manager.input_history:
            events.append({
                "index_from_line_end": event.index_from_line_end,
                "line_index": event.line_index,
                "phrase": event.phrase,
                "text": event.text
            })
        actions.insert(json.dumps(events))
        actions.key("enter")
        actions.key("enter")

        actions.insert(json.dumps(list(mutator.fixer.done_fixes.keys())))
        actions.key("enter")

        mutator.enable_tracking("DUMP")