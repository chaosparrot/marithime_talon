from talon import Module, Context, actions, settings, ui, speech_system, app
from .input_context_manager import InputContextManager
from .input_fixer import InputFixer
from .typing import CORRECTION_THRESHOLD, SELECTION_THRESHOLD
from .settings import VirtualBufferSettings, virtual_buffer_settings
from ..phonetics.detection import EXACT_MATCH, normalize_text
from typing import List, Union
import json
import re

mod = Module()

#mod.tag("flow_numbers", desc="Ensure that the user can freely insert numbers")
#mod.tag("flow_letters", desc="Ensure that the user can freely insert letters")
#mod.tag("flow_symbols", desc="Ensure that the user can freely insert symbols")
#mod.tag("flow_words", desc="Ensure that the user can freely insert words")

mod.list("marithime_indexed_words", desc="A list of words that correspond to inserted text and their caret positions for quick navigation in text")
ctx = Context()
ctx.lists["user.marithime_indexed_words"] = []

@mod.capture(rule="({user.marithime_indexed_words} | <user.marithime_word>)")
def marithime_fuzzy_indexed_word(m) -> str:
    "Returns a single word that is possibly indexed inside of the virtual buffer"
    if hasattr(m, "indexed_words"):
        return str(m.indexed_words)
    else:
        return str(m)

# Class to manage all the talon bindings and key presses for the virtual buffer
class VirtualBufferManager:
    manager: InputContextManager
    fixer: InputFixer
    tracking = True
    tracking_lock: str = ""
    repeater_type: str = "positive" # "positive", "skip", "positive_after_skip"
    use_last_set_formatter = False

    def __init__(self, settings: VirtualBufferSettings = None):
        global virtual_buffer_settings
        self.fixer = InputFixer()
        self.context = InputContextManager(actions.user.marithime_update_sensory_state, self.fixer)
        self.settings = settings if settings is not None else virtual_buffer_settings
        # self.fixer.verbose = True
        # TODO - Improve logging for fixes when the fixer is improved

    def clear_context(self):
        for context in self.context.contexts:
            context.clear_context()
        self.context.contexts = []
        self.context.current_context = None

    def set_formatter(self, name: str):
        self.context.set_formatter(name)

    def set_repeating_type(self, type: str):
        if self.repeater_type == "skip" and type != "skip":
            type = "positive_after_skip"
        self.repeater_type = type

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
            self.context.apply_key(key_string, True)
            self.index()

    def track_insert(self, insert: str, phrase: str = None):
        if self.tracking:
            self.context.track_insert(insert, phrase)
            self.index()

    def is_selecting(self) -> bool:
        return self.context.get_current_context().buffer.is_selecting()
    
    def is_virtual_selecting(self) -> bool:
        return len(self.context.get_current_context().buffer.virtual_selection) > 0

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
            return [vbm.settings.get_end_of_line_key()]

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

        # Make sure we remove the virtual selection if we apply a new insert
        if len(vbm.virtual_selection) > 0:
            previous_selection = "" if not correction_insertion else vbm.caret_tracker.get_text_between_tokens(
                vbm.virtual_selection[0],
                vbm.virtual_selection[-1]
            )

            # Apply virtual selection removal so the formatter has up to date information
            keys_to_remove_virtual_selection = vbm.remove_virtual_selection()
            repair_keys.extend(keys_to_remove_virtual_selection)
            for key in keys_to_remove_virtual_selection:
                self.context.apply_key(key)

        # Detect if we are doing a repeated phonetic correction
        # In order to cycle through it
        if vbm.last_action_type == "phonetic_correction":
            normalized_input = normalize_text(insert).lower()
            normalized_last_insert = normalize_text(" ".join(self.context.last_insert_phrases)).lower()
            if normalized_last_insert.endswith(normalized_input):
                enable_self_repair = enable_self_repair and not correction_insertion

                # Replace the words with phonetic equivelants
                insert, cycle_count = self.fixer.cycle_through_fixes(" ".join(self.context.last_insert_phrases), vbm.correction_cycle_count)
                vbm.correction_cycle_count = cycle_count

                # Make sure we do not save the transformed text as an individual insert
                # As it would update the state as if it wasn't a repeated item
                vbm.skip_last_action_insert = True

            # If the words don't match, just clear the correction
            else:
                vbm.correction_cycle_count = 0
                vbm.skip_last_action_insert = False

        normalized_input = insert.lower()
        normalized_last_select = "" if vbm.correction_start_phrases is None else vbm.correction_start_phrases.lower()

        # On repeated corrections, cycle through the corrections
        # Only do an initial repeat if we have an exact match!
        if vbm.last_action_type == "correction" or \
            ( vbm.last_action_type == "first-correction" and normalized_last_select.endswith(normalized_input) ):
            normalized_input = normalize_text(normalized_input)
            normalized_last_search = normalize_text(" ".join(vbm.last_search)).lower()
            
            if normalized_last_search.endswith(normalized_input):
                # Replace the words with phonetic equivelants
                insert, cycle_count = self.fixer.cycle_through_fixes(" ".join(vbm.last_search), vbm.correction_cycle_count, vbm.correction_start_phrases)
                vbm.correction_cycle_count = cycle_count

                # Make sure we do not save the transformed text as an individual insert
                # As it would update the state as if it wasn't a repeated item
                vbm.skip_last_action_insert = True
            else:
                vbm.correction_cycle_count = 0
                vbm.skip_last_action_insert = False

        # Make sure we do not save the transformed text as an individual insert
        # As it would update the state as if it wasn't a repeated item
        if vbm.last_action_type == "first-correction":
            vbm.skip_last_action_insert = True

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

            self_repair_match = vbm.find_self_repair(insert.split(), verbose=True)

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
                    if first_index - 1 > 0:
                        allow_initial_replacement = not any(punc in vbm.tokens[first_index - 1].text for punc in (".", "?", "!"))
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

                            # Regular shift selection
                            if len(vbm.virtual_selection) == 0:
                                remove_character_left_key = self.settings.get_remove_character_left_key()
                                repair_keys.append(remove_character_left_key)
                                self.context.apply_key(remove_character_left_key)

                            # Let self repair work for virtual selection as well
                            else:
                                keys_to_remove_virtual_selection = vbm.remove_virtual_selection()
                                repair_keys.extend(keys_to_remove_virtual_selection)
                                for key in keys_to_remove_virtual_selection:
                                    self.context.apply_key(key)
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
            return [self.settings.get_remove_character_left_key()]
        elif self.is_virtual_selecting():
            return vbm.remove_virtual_selection()

        # For single character insertions we want to remove characters one by one
        elif vbm and vbm.single_character_presses > 0 and backwards:
            return [self.settings.get_remove_character_left_key()]
        
        if context.current is not None:
            if context.character_index == 0 and backwards and context.previous is not None:
                return [self.settings.get_remove_character_left_key() + ":" + str(len(context.previous.text))]

            elif context.character_index == len(context.current.text):
                if not backwards and context.next is not None:
                    return [self.settings.get_remove_character_right_key() + ":" + str(len(context.next.text))]
                elif backwards:
                    return [self.settings.get_remove_character_left_key() + ":" + str(len(context.current.text))]

            # Clear character-wise in the middle of a word
            if context.character_index > 0 and context.character_index < len(context.current.text) - 1:
                if backwards:
                    return [self.settings.get_remove_character_left_key()]
                else:
                    return [self.settings.get_remove_character_right_key()]

        return [self.settings.get_remove_word_left_key() if backwards else self.settings.get_remove_word_right_key()]

    def index(self):
        vbm = self.context.get_current_context().buffer

        words_list = []
        for token in vbm.tokens:
            words_list.append(token.phrase)
        ctx.lists["user.marithime_indexed_words"] = words_list

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
    global mutator
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

    # Enable this line to allow for quicker debugging
    # actions.menu.open_log()
    update_language("")
    return mutator

def get_mutator() -> VirtualBufferManager:
    global mutator
    return mutator if mutator is not None else init_mutator()

app.register("ready", init_mutator)

@mod.action_class
class Actions:

    def marithime_enable_input_tracking():
        """Enable tracking of input values so that we can make contextual decisions and keep the caret position"""
        mutator = get_mutator()
        mutator.enable_tracking()

    def marithime_disable_input_tracking():
        """Disable tracking of input values"""
        mutator = get_mutator()
        mutator.disable_tracking()

    def marithime_set_formatter(formatter: str):
        """Sets the current formatter to be used in text editing"""
        mutator = get_mutator()
        mutator.set_formatter(formatter)

    def marithime_transform_insert(insert: str) -> str:
        """Transform an insert automatically depending on previous context"""
        mutator = get_mutator()
        return mutator.transform_insert(insert)[0]

    def marithime_self_repair_insert(prose: str):
        """Input words based on context surrounding the words to input, allowing for self repair within speech as well"""
        mutator = get_mutator()

        text_to_insert, keys = mutator.transform_insert(prose, True)
        if len(keys) > 0:
            mutator.disable_tracking()
            for key in keys:
                actions.key(key)
            mutator.enable_tracking()

        actions.insert(text_to_insert)

    def marithime_insert(prose: str):
        """Input words based on context surrounding the words to input"""
        mutator = get_mutator()

        text_to_insert, keys = mutator.transform_insert(prose)
        if len(keys) > 0:
            mutator.disable_tracking()
            for key in keys:
                actions.key(key)
            mutator.enable_tracking()

        actions.insert(text_to_insert)

    def marithime_track_key(key_string: str) -> str:
        """Track one or more key presses according to the key string"""
        mutator = get_mutator()
        mutator.track_key(key_string)

    def marithime_track_insert(insert: str, phrase: str = "") -> str:
        """Track a full insert"""
        mutator = get_mutator()
        mutator.track_insert(insert, phrase)

    def marithime_backspace(backward: bool = True):
        """Apply a clear based on the current virtual buffer"""
        mutator = get_mutator()
        keys = mutator.clear_keys(backward)
        for key in keys:
            actions.key(key)
        #mutator.index_textarea()

    def marithime_move_caret(phrase: str, caret_position: int = -1):
        """Move the caret to the given phrase"""
        mutator = get_mutator()
        if mutator.has_phrase(phrase):
            keys = mutator.move_to_phrase(phrase, caret_position)
            if keys:
                mutator.disable_tracking()
                for key in keys:
                    actions.key(key)
                mutator.enable_tracking()
        else:
            raise RuntimeError("Input phrase '" + phrase + "' could not be found in the buffer")

    def marithime_select(phrase: Union[str, List[str]]):
        """Move the caret to the given phrase and select it"""
        mutator = get_mutator()

        phrases = phrase if isinstance(phrase, List) else [phrase]
        keys = mutator.select_phrases(phrases)
        mutator.disable_tracking()
        if keys:
            for key in keys:
                actions.key(key)
        mutator.enable_tracking()
            
    def marithime_correction(selection_and_correction: List[str]):
        """Select a fuzzy match of the words and apply the given words"""
        mutator = get_mutator()

        # We can repeat this command - But skip to the next selection if we are dealing with a "skip" repetition
        # Positive - cycle through single corrections
        # Skip - Select the next correctable phrase
        # Positive_after_skip - Replace the selection with the insertion
        if mutator.repeater_type == "positive_after_skip":
            keys = []
        else:
            keys = mutator.select_phrases(selection_and_correction, for_correction=True)

        if len(keys) > 0 or mutator.is_virtual_selecting() or mutator.repeater_type == "positive_after_skip":
            mutator.disable_tracking()
            if keys:
                for key in keys:
                    actions.key(key)
            mutator.enable_tracking()

            # Do not insert text upon skipping a correction
            if mutator.repeater_type != "skip":
                text = " ".join(selection_and_correction)
                actions.user.marithime_insert(text)
        else:
            raise RuntimeError("Input phrase '" + " ".join(selection_and_correction) + "' could not be corrected")

    def marithime_clear_phrase(phrase: str):
        """Move the caret behind the given phrase and remove it"""
        mutator = get_mutator()
        before_keys = mutator.move_to_phrase(phrase, -1, False, False)
        mutator.disable_tracking()
        if before_keys:
            for key in before_keys:
                actions.key(key)
        mutator.enable_tracking()

        keys = mutator.clear_keys()
        for key in keys:
            actions.key(key)

    def marithime_continue():
        """Move the caret to the end of the current virtual buffer"""
        mutator = get_mutator()
        keys = mutator.move_caret_back()

        mutator.disable_tracking()
        for key in keys:
            actions.key(key)
        mutator.enable_tracking()

    def marithime_forget_context():
        """Forget the current context of the virtual buffer completely"""
        mutator = get_mutator()
        mutator.clear_context()

    def marithime_best_match(phrases: List[str], correct_previous: bool = False, starting_phrase: str = '') -> str:
        """Improve accuracy by picking the best matches out of the words used"""
        mutator = get_mutator()
        match_dictionary = {}
        if starting_phrase:
            phrases.append( starting_phrase )

        for phrase in phrases:
            if phrase not in match_dictionary:
                match_dictionary[phrase] = 0
            match_dictionary[phrase] += 1
        
        return max(match_dictionary, key=match_dictionary.get)
    
    def marithime_index_textarea():
        """Select the index area and update the internal state completely"""
        mutator = get_mutator()
        mutator.index_textarea()
    
    def marithime_update_sensory_state(scanning: bool, level: str, caret_confidence: int, content_confidence: int):
        """Visually or audibly update the state for the user"""
        pass

    def marithime_repeat(type: str):
        """Repeat a command within Marithime context or fall back to regular repeater"""
        mutator = get_mutator()
        mutator.set_repeating_type(type)
        actions.core.repeat_command()

    def marithime_toggle_track_context():
        """Toggle between tracking and not tracking the marithime virtual buffer context"""
        mutator = get_mutator()
        if mutator.context.context_tracking == True:
            actions.user.marithime_disable_track_context()
        else:
            actions.user.marithime_enable_track_context()

    def marithime_enable_track_context():
        """Start tracking the marithime virtual buffer context as it changes"""
        mutator = get_mutator()
        mutator.context.set_context_tracking(True)
        actions.user.marithime_show_context()

    def marithime_disable_track_context():
        """Stop tracking the marithime virtual buffer context as it changes"""
        mutator = get_mutator()
        mutator.context.set_context_tracking(False)

    def marithime_show_context() -> str:
        """Show the current context in a Window if supported"""
        mutator = get_mutator()
        current_context = mutator.context.get_current_context()
        lines = "Using " + current_context.title + " - PID " + str(current_context.pid ) + "\n"
        lines += "------------------------------------------------\n"
        text_lines = current_context.buffer.caret_tracker.text_buffer.splitlines()
        found_index = -1
        for index, text_line in enumerate(text_lines):
            if "$CARET" in text_line:
                found_index = index

        # Only show the relevant lines around the cursor
        if found_index == -1:
            lines += (current_context.buffer.caret_tracker.text_buffer).replace("$CARET", "|^|")
        else:
            if found_index > 0:
                lines += text_lines[found_index - 1] + "\n"
            lines += text_lines[found_index].replace("$CARET", "|^|")
            if found_index < len(text_lines) - 1:
                lines += "\n" + text_lines[found_index + 1]

        return lines